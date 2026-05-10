"""
Unit tests for agent tool handlers.
These tests run fully offline — no OpenAI API key required.
"""

import subprocess
from unittest.mock import patch

from agents.tools import list_files, read_file, run_tests


# ---------------------------------------------------------------------------
# read_file
# ---------------------------------------------------------------------------


def test_read_file_returns_content(tmp_path):
    f = tmp_path / "hello.py"
    f.write_text("print('hello')")
    result = read_file(str(f))
    assert result == "print('hello')"


def test_read_file_missing_returns_error():
    result = read_file("/nonexistent/path/file.py")
    assert result.startswith("Error:")
    assert "not found" in result


def test_read_file_too_large_returns_error(tmp_path):
    f = tmp_path / "big.py"
    f.write_bytes(b"x" * 200_001)
    result = read_file(str(f))
    assert result.startswith("Error:")
    assert "too large" in result


def test_read_file_handles_encoding(tmp_path):
    f = tmp_path / "unicode.py"
    f.write_text("# café résumé", encoding="utf-8")
    result = read_file(str(f))
    assert "café" in result


# ---------------------------------------------------------------------------
# list_files
# ---------------------------------------------------------------------------


def test_list_files_returns_filenames(tmp_path):
    (tmp_path / "a.py").write_text("")
    (tmp_path / "b.py").write_text("")
    result = list_files(str(tmp_path))
    assert "a.py" in result
    assert "b.py" in result


def test_list_files_empty_directory(tmp_path):
    result = list_files(str(tmp_path))
    assert result == "(empty directory)"


def test_list_files_missing_directory():
    result = list_files("/nonexistent/dir")
    assert result.startswith("Error:")
    assert "not found" in result


def test_list_files_excludes_subdirectories(tmp_path):
    (tmp_path / "file.py").write_text("")
    (tmp_path / "subdir").mkdir()
    result = list_files(str(tmp_path))
    assert "file.py" in result
    assert "subdir" not in result


# ---------------------------------------------------------------------------
# run_tests
# ---------------------------------------------------------------------------


def test_run_tests_returns_output(tmp_path):
    test_file = tmp_path / "test_sample.py"
    test_file.write_text("def test_pass():\n    assert 1 + 1 == 2\n")
    result = run_tests(str(test_file))
    assert "passed" in result or "1 passed" in result


def test_run_tests_failing_test_shows_failure(tmp_path):
    test_file = tmp_path / "test_fail.py"
    test_file.write_text("def test_fail():\n    assert 1 == 2\n")
    result = run_tests(str(test_file))
    assert "failed" in result or "AssertionError" in result


def test_run_tests_timeout_handled():
    with patch("agents.tools.subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="pytest", timeout=60)
        result = run_tests(".")
    assert "timed out" in result


def test_run_tests_pytest_not_found_handled():
    with patch("agents.tools.subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError
        result = run_tests(".")
    assert "not found" in result


def test_run_tests_caps_output_length(tmp_path):
    # Generate a test that produces a lot of output
    test_file = tmp_path / "test_verbose.py"
    test_file.write_text(
        "def test_output():\n"
        "    for i in range(1000):\n"
        "        print('x' * 100)\n"
        "    assert True\n"
    )
    result = run_tests(str(test_file))
    assert len(result) <= 4000
