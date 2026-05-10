"""
codex-sdlc-copilot CLI entry point.

Usage:
    python -m cli.main pr-review --diff examples/sample_pr_diff.txt
    python -m cli.main test-gen --file examples/legacy_flask_app.py
    python -m cli.main migration-assist --file examples/legacy_flask_app.py --target fastapi
"""

import os
import sys

import click
from rich.console import Console

console = Console()


def _check_api_key() -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        console.print(
            "[red]Error:[/red] OPENAI_API_KEY environment variable is not set.\n"
            "Run: [bold]export OPENAI_API_KEY=sk-...[/bold]"
        )
        sys.exit(1)


@click.group()
def cli():
    """codex-sdlc-copilot — AI-powered SDLC automation using OpenAI Codex."""
    pass


@cli.command("pr-review")
@click.option(
    "--diff",
    required=True,
    help="Path to a git diff file (.diff or .txt)",
)
@click.option(
    "--output-dir",
    default="output",
    show_default=True,
    help="Directory to write the Markdown report",
)
def pr_review(diff: str, output_dir: str) -> None:
    """Review a PR diff and produce a structured code review report."""
    _check_api_key()
    from cli.pr_review import run

    run(diff_path=diff, output_dir=output_dir)


@cli.command("test-gen")
@click.option(
    "--file",
    "source_file",
    required=True,
    help="Path to the Python source file to generate tests for",
)
@click.option(
    "--output-dir",
    default="output",
    show_default=True,
    help="Directory to write the generated test file",
)
@click.option(
    "--no-verify",
    is_flag=True,
    default=False,
    help="Skip running pytest to verify generated tests",
)
def test_gen(source_file: str, output_dir: str, no_verify: bool) -> None:
    """Generate pytest unit tests for a Python source file."""
    _check_api_key()
    from cli.test_gen import run

    run(source_path=source_file, output_dir=output_dir, verify=not no_verify)


@cli.command("migration-assist")
@click.option(
    "--file",
    "source_file",
    required=True,
    help="Path to the legacy Python file to migrate",
)
@click.option(
    "--target",
    default="fastapi",
    show_default=True,
    type=click.Choice(["fastapi", "flask3", "django5", "async"], case_sensitive=False),
    help="Target framework",
)
@click.option(
    "--output-dir",
    default="output",
    show_default=True,
    help="Directory to write migrated file and summary",
)
def migration_assist(source_file: str, target: str, output_dir: str) -> None:
    """Migrate legacy Python code to a modern framework."""
    _check_api_key()
    from cli.migration import run

    run(source_path=source_file, target=target, output_dir=output_dir)


if __name__ == "__main__":
    cli()
