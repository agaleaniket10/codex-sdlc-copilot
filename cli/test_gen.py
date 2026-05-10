"""
Test Generation mode — uses Codex to generate missing unit tests for a Python file.

Workflow:
  1. Agent reads the source file
  2. Identifies functions/classes lacking test coverage
  3. Generates a pytest test file
  4. Optionally runs the tests to verify they pass
"""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from agents.codex_agent import CodexAgent
from agents.tools import READ_FILE_TOOL, RUN_TESTS_TOOL, TOOL_HANDLERS

console = Console()

SYSTEM_PROMPT = """You are a senior Python engineer specialising in test-driven development.

Your task is to generate comprehensive pytest unit tests for a given Python source file.

Steps:
1. Use the read_file tool to read the source file.
2. Identify all public functions, methods, and classes.
3. For each, generate tests covering:
   - Happy path (expected inputs → expected outputs)
   - Edge cases (empty input, None, boundary values)
   - Error cases (invalid input, exceptions)
4. Use the run_tests tool to verify the generated tests pass.
5. If tests fail, fix them and re-run.

Output ONLY the complete pytest file content — valid Python, no markdown fences, no explanation.
The file should start with the necessary imports and be ready to save directly as test_<module>.py.

Use pytest fixtures where appropriate. Mock external dependencies (HTTP calls, DB, filesystem) 
using unittest.mock or pytest-mock.
"""


def run(source_path: str, output_dir: str = "output", verify: bool = True) -> None:
    """
    Generate unit tests for a Python source file.

    Parameters
    ----------
    source_path : str
        Path to the Python file to generate tests for.
    output_dir : str
        Directory to write the generated test file to.
    verify : bool
        If True, run the generated tests with pytest to verify they pass.
    """
    src = Path(source_path)
    if not src.exists():
        console.print(f"[red]Error:[/red] source file not found: {source_path}")
        return

    console.print(
        Panel(
            f"[bold cyan]Test Generation[/bold cyan]\nSource: {source_path}",
            expand=False,
        )
    )

    tools = [READ_FILE_TOOL, RUN_TESTS_TOOL] if verify else [READ_FILE_TOOL]
    handlers = {
        k: TOOL_HANDLERS[k]
        for k in (["read_file", "run_tests"] if verify else ["read_file"])
    }

    agent = CodexAgent(
        tools=tools,
        tool_handlers=handlers,
        system_prompt=SYSTEM_PROMPT,
    )

    user_message = (
        f"Generate comprehensive pytest unit tests for the file at: {source_path}\n\n"
        f"{'After generating, use run_tests to verify they pass and fix any failures.' if verify else ''}"
    )

    with console.status("[bold green]Codex is generating tests…"):
        test_code = agent.run(user_message)

    # Strip accidental markdown fences
    test_code = _strip_fences(test_code)

    # Display preview
    console.print("\n[bold]Generated test file preview:[/bold]")
    console.print(
        Syntax(test_code[:2000], "python", theme="monokai", line_numbers=True)
    )
    if len(test_code) > 2000:
        console.print(f"[dim]… ({len(test_code) - 2000} more characters)[/dim]")

    # Save
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    out_path = Path(output_dir) / f"test_{src.stem}.py"
    out_path.write_text(test_code, encoding="utf-8")
    console.print(f"\n[dim]Test file saved to {out_path}[/dim]")


def _strip_fences(code: str) -> str:
    """Remove markdown code fences if the model accidentally included them."""
    lines = code.strip().splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines)
