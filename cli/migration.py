"""
Migration Assist mode — uses Codex to migrate legacy Python code to a modern framework.

Supported targets: fastapi, flask3, django5, async

Workflow:
  1. Agent reads the source file
  2. Analyses the framework patterns in use
  3. Produces a migrated version with inline comments explaining each change
  4. Generates a migration summary report
"""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax

from agents.codex_agent import CodexAgent
from agents.tools import READ_FILE_TOOL, LIST_FILES_TOOL, TOOL_HANDLERS

console = Console()

SUPPORTED_TARGETS = ["fastapi", "flask3", "django5", "async"]

SYSTEM_PROMPT = """You are a senior Python architect specialising in framework migrations.

Your task is to migrate legacy Python web application code to a modern target framework.

Steps:
1. Use read_file to read the source file thoroughly.
2. Use list_files to understand the broader project structure if needed.
3. Identify all patterns that need migration:
   - Route definitions
   - Request/response handling
   - Middleware
   - Database access patterns
   - Authentication
   - Error handling
4. Produce the migrated code with:
   - Inline comments prefixed with # MIGRATION: explaining each significant change
   - Modern idioms for the target framework
   - Type hints where appropriate
   - Async/await where the target supports it

Return your response in this exact format:

===MIGRATED_CODE===
<complete migrated Python file>
===END_MIGRATED_CODE===

===MIGRATION_SUMMARY===
## Migration Summary

### Changes Made
- <bullet list of significant changes>

### Breaking Changes
- <anything that requires manual intervention>

### Next Steps
- <recommended follow-up actions>
===END_MIGRATION_SUMMARY===
"""


def run(source_path: str, target: str = "fastapi", output_dir: str = "output") -> None:
    """
    Migrate a legacy Python file to a modern framework.

    Parameters
    ----------
    source_path : str
        Path to the legacy Python file.
    target : str
        Target framework: fastapi | flask3 | django5 | async
    output_dir : str
        Directory to write migrated file and summary to.
    """
    if target not in SUPPORTED_TARGETS:
        console.print(
            f"[red]Error:[/red] unsupported target '{target}'. "
            f"Choose from: {', '.join(SUPPORTED_TARGETS)}"
        )
        return

    src = Path(source_path)
    if not src.exists():
        console.print(f"[red]Error:[/red] source file not found: {source_path}")
        return

    console.print(
        Panel(
            f"[bold cyan]Migration Assist[/bold cyan]\n"
            f"Source: {source_path}  →  Target: [bold]{target}[/bold]",
            expand=False,
        )
    )

    agent = CodexAgent(
        tools=[READ_FILE_TOOL, LIST_FILES_TOOL],
        tool_handlers={
            "read_file": TOOL_HANDLERS["read_file"],
            "list_files": TOOL_HANDLERS["list_files"],
        },
        system_prompt=SYSTEM_PROMPT,
    )

    user_message = (
        f"Migrate the file at '{source_path}' to {target}.\n"
        f"Read the file first, then produce the migrated code and migration summary."
    )

    with console.status(f"[bold green]Codex is migrating to {target}…"):
        response = agent.run(user_message)

    migrated_code, summary = _parse_response(response)

    if migrated_code:
        console.print("\n[bold]Migrated code preview:[/bold]")
        console.print(
            Syntax(migrated_code[:2000], "python", theme="monokai", line_numbers=True)
        )
        if len(migrated_code) > 2000:
            console.print(f"[dim]… ({len(migrated_code) - 2000} more characters)[/dim]")

    if summary:
        console.print("\n")
        console.print(Markdown(summary))

    # Save outputs
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    if migrated_code:
        code_path = Path(output_dir) / f"{src.stem}_{target}.py"
        code_path.write_text(migrated_code, encoding="utf-8")
        console.print(f"\n[dim]Migrated file saved to {code_path}[/dim]")

    if summary:
        summary_path = Path(output_dir) / f"migration-summary-{src.stem}-to-{target}.md"
        summary_path.write_text(summary, encoding="utf-8")
        console.print(f"[dim]Migration summary saved to {summary_path}[/dim]")


def _parse_response(response: str) -> tuple[str, str]:
    """Extract migrated code and summary from the structured response."""
    migrated_code = ""
    summary = ""

    if "===MIGRATED_CODE===" in response and "===END_MIGRATED_CODE===" in response:
        start = response.index("===MIGRATED_CODE===") + len("===MIGRATED_CODE===")
        end = response.index("===END_MIGRATED_CODE===")
        migrated_code = response[start:end].strip()

    if (
        "===MIGRATION_SUMMARY===" in response
        and "===END_MIGRATION_SUMMARY===" in response
    ):
        start = response.index("===MIGRATION_SUMMARY===") + len(
            "===MIGRATION_SUMMARY==="
        )
        end = response.index("===END_MIGRATION_SUMMARY===")
        summary = response[start:end].strip()

    # Fallback: if delimiters not found, treat whole response as code
    if not migrated_code and not summary:
        migrated_code = response

    return migrated_code, summary
