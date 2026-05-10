"""
Integration tests for the CLI layer.
Tests run fully offline — OpenAI API calls are mocked.
"""

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from cli.main import cli


SAMPLE_DIFF = "diff --git a/foo.py b/foo.py\n--- a/foo.py\n+++ b/foo.py\n@@ -1 +1 @@\n-x = 1\n+x = 2\n"

MOCK_PR_REVIEW_JSON = """{
  "summary": "Minor change to variable assignment.",
  "overall_score": 8,
  "issues": [],
  "positive_observations": ["Clean, minimal change"],
  "recommended_action": "approve"
}"""

MOCK_TEST_GEN_OUTPUT = "import pytest\n\ndef test_example():\n    assert 1 + 1 == 2\n"

MOCK_MIGRATION_OUTPUT = (
    "===MIGRATED_CODE===\nfrom fastapi import FastAPI\napp = FastAPI()\n===END_MIGRATED_CODE===\n"
    "===MIGRATION_SUMMARY===\n## Migration Summary\n### Changes Made\n- Replaced Flask with FastAPI\n"
    "===END_MIGRATION_SUMMARY==="
)


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def diff_file(tmp_path):
    f = tmp_path / "test.diff"
    f.write_text(SAMPLE_DIFF)
    return str(f)


@pytest.fixture
def source_file(tmp_path):
    f = tmp_path / "app.py"
    f.write_text("def add(a, b):\n    return a + b\n")
    return str(f)


# ---------------------------------------------------------------------------
# API key guard
# ---------------------------------------------------------------------------


def test_pr_review_requires_api_key(runner, diff_file, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    result = runner.invoke(cli, ["pr-review", "--diff", diff_file])
    assert result.exit_code == 1 or "OPENAI_API_KEY" in result.output


# ---------------------------------------------------------------------------
# pr-review
# ---------------------------------------------------------------------------


def test_pr_review_runs_with_mock(runner, diff_file, tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    with patch("cli.pr_review.CodexAgent") as MockAgent:
        instance = MockAgent.return_value
        instance.run.return_value = MOCK_PR_REVIEW_JSON

        result = runner.invoke(
            cli,
            ["pr-review", "--diff", diff_file, "--output-dir", str(tmp_path)],
        )

    assert result.exit_code == 0
    reports = list(tmp_path.glob("pr-review-*.md"))
    assert len(reports) == 1
    content = reports[0].read_text()
    assert "Score" in content


def test_pr_review_missing_diff_file(runner, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    result = runner.invoke(cli, ["pr-review", "--diff", "/nonexistent/file.diff"])
    assert "not found" in result.output or result.exit_code != 0


# ---------------------------------------------------------------------------
# test-gen
# ---------------------------------------------------------------------------


def test_test_gen_runs_with_mock(runner, source_file, tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    with patch("cli.test_gen.CodexAgent") as MockAgent:
        instance = MockAgent.return_value
        instance.run.return_value = MOCK_TEST_GEN_OUTPUT

        result = runner.invoke(
            cli,
            [
                "test-gen",
                "--file",
                source_file,
                "--output-dir",
                str(tmp_path),
                "--no-verify",
            ],
        )

    assert result.exit_code == 0
    test_files = list(tmp_path.glob("test_*.py"))
    assert len(test_files) == 1
    assert "def test_example" in test_files[0].read_text()


def test_test_gen_strips_markdown_fences(runner, source_file, tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    fenced_output = "```python\ndef test_foo():\n    assert True\n```"

    with patch("cli.test_gen.CodexAgent") as MockAgent:
        instance = MockAgent.return_value
        instance.run.return_value = fenced_output

        runner.invoke(
            cli,
            [
                "test-gen",
                "--file",
                source_file,
                "--output-dir",
                str(tmp_path),
                "--no-verify",
            ],
        )

    test_files = list(tmp_path.glob("test_*.py"))
    content = test_files[0].read_text()
    assert "```" not in content


# ---------------------------------------------------------------------------
# migration-assist
# ---------------------------------------------------------------------------


def test_migration_runs_with_mock(runner, source_file, tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    with patch("cli.migration.CodexAgent") as MockAgent:
        instance = MockAgent.return_value
        instance.run.return_value = MOCK_MIGRATION_OUTPUT

        result = runner.invoke(
            cli,
            [
                "migration-assist",
                "--file",
                source_file,
                "--target",
                "fastapi",
                "--output-dir",
                str(tmp_path),
            ],
        )

    assert result.exit_code == 0
    code_files = list(tmp_path.glob("*_fastapi.py"))
    summary_files = list(tmp_path.glob("migration-summary-*.md"))
    assert len(code_files) == 1
    assert len(summary_files) == 1


def test_migration_invalid_target(runner, source_file, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    result = runner.invoke(
        cli,
        ["migration-assist", "--file", source_file, "--target", "rails"],
    )
    assert result.exit_code != 0
