"""
PR Review mode — uses Codex to produce a structured code review from a diff.

The agent reads the diff, reasons about it, and returns a JSON report with:
  - summary
  - issues (severity: critical | major | minor | nit)
  - suggestions
  - overall_score (1–10)

The report is rendered as a Rich table in the terminal and saved as Markdown.
"""

from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from agents.codex_agent import CodexAgent
from agents.tools import READ_FILE_TOOL, TOOL_HANDLERS

console = Console()

SYSTEM_PROMPT = """You are a senior software engineer conducting a thorough code review.

You will be given a git diff. Your job is to:
1. Read the diff carefully using the read_file tool if you need more context about the surrounding codebase.
2. Identify issues across these dimensions:
   - Correctness (bugs, logic errors, edge cases)
   - Security (injection, auth, secrets, input validation)
   - Performance (unnecessary complexity, N+1 queries, blocking calls)
   - Maintainability (naming, structure, duplication, missing docs)
   - Test coverage (missing or inadequate tests)

3. Return a JSON object with this exact structure:
{
  "summary": "2-3 sentence overview of the changes and their quality",
  "overall_score": <integer 1-10>,
  "issues": [
    {
      "severity": "critical|major|minor|nit",
      "location": "filename:line or description",
      "description": "clear explanation of the issue",
      "suggestion": "concrete fix or improvement"
    }
  ],
  "positive_observations": ["list of things done well"],
  "recommended_action": "approve|approve_with_changes|request_changes|block"
}

Return ONLY the JSON object, no markdown fences, no extra text.
"""


def run(diff_path: str, output_dir: str = "output") -> None:
    """
    Run PR review on a diff file.

    Parameters
    ----------
    diff_path : str
        Path to a .diff or .txt file containing the git diff.
    output_dir : str
        Directory to write the Markdown report to.
    """
    diff_file = Path(diff_path)
    if not diff_file.exists():
        console.print(f"[red]Error:[/red] diff file not found: {diff_path}")
        return

    diff_content = diff_file.read_text(encoding="utf-8")

    console.print(
        Panel(f"[bold cyan]PR Review[/bold cyan]\nDiff: {diff_path}", expand=False)
    )

    agent = CodexAgent(
        tools=[READ_FILE_TOOL],
        tool_handlers={"read_file": TOOL_HANDLERS["read_file"]},
        system_prompt=SYSTEM_PROMPT,
    )

    user_message = f"""Please review the following git diff and return your structured JSON review.

<diff>
{diff_content}
</diff>
"""

    with console.status("[bold green]Codex is reviewing the diff…"):
        raw_response = agent.run(user_message)

    # Parse JSON response
    try:
        report = json.loads(raw_response)
    except json.JSONDecodeError:
        console.print(
            "[red]Warning:[/red] Could not parse JSON response. Showing raw output.\n"
        )
        console.print(raw_response)
        return

    _render_report(report)
    _save_report(report, diff_path, output_dir)


def _render_report(report: dict) -> None:
    """Render the review report as a Rich table."""
    score = report.get("overall_score", "?")
    score_color = "green" if score >= 7 else "yellow" if score >= 4 else "red"

    console.print()
    console.print(
        Panel(
            f"[bold]Summary:[/bold] {report.get('summary', '')}\n\n"
            f"[bold]Score:[/bold] [{score_color}]{score}/10[/{score_color}]   "
            f"[bold]Action:[/bold] {report.get('recommended_action', '').upper()}",
            title="[bold cyan]Codex PR Review[/bold cyan]",
        )
    )

    issues = report.get("issues", [])
    if issues:
        table = Table(title="Issues Found", show_lines=True)
        table.add_column("Severity", style="bold", width=10)
        table.add_column("Location", width=30)
        table.add_column("Description")
        table.add_column("Suggestion")

        severity_colors = {
            "critical": "red",
            "major": "orange3",
            "minor": "yellow",
            "nit": "dim",
        }

        for issue in issues:
            sev = issue.get("severity", "minor")
            color = severity_colors.get(sev, "white")
            table.add_row(
                f"[{color}]{sev.upper()}[/{color}]",
                issue.get("location", ""),
                issue.get("description", ""),
                issue.get("suggestion", ""),
            )
        console.print(table)

    positives = report.get("positive_observations", [])
    if positives:
        console.print("\n[bold green]Positive observations:[/bold green]")
        for p in positives:
            console.print(f"  ✓ {p}")


def _save_report(report: dict, diff_path: str, output_dir: str) -> None:
    """Save the review as a Markdown file."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    diff_name = Path(diff_path).stem
    out_path = Path(output_dir) / f"pr-review-{diff_name}.md"

    lines = [
        f"# PR Review: {diff_name}\n",
        f"**Score:** {report.get('overall_score')}/10  ",
        f"**Action:** {report.get('recommended_action', '').upper()}\n",
        f"## Summary\n{report.get('summary', '')}\n",
        "## Issues\n",
    ]

    for issue in report.get("issues", []):
        lines.append(
            f"### [{issue.get('severity', '').upper()}] {issue.get('location', '')}\n"
            f"**Issue:** {issue.get('description', '')}\n\n"
            f"**Suggestion:** {issue.get('suggestion', '')}\n"
        )

    positives = report.get("positive_observations", [])
    if positives:
        lines.append("## Positive Observations\n")
        for p in positives:
            lines.append(f"- {p}")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    console.print(f"\n[dim]Report saved to {out_path}[/dim]")
