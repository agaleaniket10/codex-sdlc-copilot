"""
Tool definitions and handlers shared across all CLI modes.

Each tool has:
  - A JSON schema (passed to the OpenAI API)
  - A Python handler function (executed locally when the model calls the tool)
"""

import subprocess
from pathlib import Path


# ---------------------------------------------------------------------------
# Python handler functions
# ---------------------------------------------------------------------------


def read_file(path: str) -> str:
    """Read a local file and return its contents."""
    p = Path(path)
    if not p.exists():
        return f"Error: file not found — {path}"
    if p.stat().st_size > 200_000:
        return f"Error: file too large to read (>{200_000} bytes)"
    return p.read_text(encoding="utf-8", errors="replace")


def list_files(directory: str = ".") -> str:
    """List files in a directory (non-recursive, relative paths)."""
    p = Path(directory)
    if not p.exists():
        return f"Error: directory not found — {directory}"
    files = [str(f.relative_to(p)) for f in p.iterdir() if f.is_file()]
    return "\n".join(sorted(files)) or "(empty directory)"


def run_tests(test_path: str = ".", extra_args: str = "") -> str:
    """
    Run pytest on the given path and return stdout + stderr.
    Used by test-gen mode to verify generated tests actually pass.
    """
    cmd = ["python", "-m", "pytest", test_path, "--tb=short", "-q"]
    if extra_args:
        cmd += extra_args.split()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = result.stdout + result.stderr
        return output[:4000]  # cap to avoid flooding context
    except subprocess.TimeoutExpired:
        return "Error: pytest timed out after 60 seconds"
    except FileNotFoundError:
        return "Error: pytest not found — ensure it is installed in the active venv"


# ---------------------------------------------------------------------------
# OpenAI tool schemas
# ---------------------------------------------------------------------------

READ_FILE_TOOL = {
    "type": "function",
    "function": {
        "name": "read_file",
        "description": (
            "Read the full contents of a local file. "
            "Use this to inspect source code, diffs, or configuration files."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative or absolute path to the file.",
                }
            },
            "required": ["path"],
        },
    },
}

LIST_FILES_TOOL = {
    "type": "function",
    "function": {
        "name": "list_files",
        "description": "List files in a directory to understand project structure.",
        "parameters": {
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": "Directory path to list. Defaults to current directory.",
                }
            },
            "required": [],
        },
    },
}

RUN_TESTS_TOOL = {
    "type": "function",
    "function": {
        "name": "run_tests",
        "description": (
            "Run pytest on a given path and return the output. "
            "Use this to verify that generated tests are syntactically valid and pass."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "test_path": {
                    "type": "string",
                    "description": "Path to test file or directory. Defaults to current directory.",
                },
                "extra_args": {
                    "type": "string",
                    "description": "Additional pytest arguments, e.g. '-k test_login'.",
                },
            },
            "required": [],
        },
    },
}

# Convenience exports
ALL_TOOLS = [READ_FILE_TOOL, LIST_FILES_TOOL, RUN_TESTS_TOOL]

TOOL_HANDLERS = {
    "read_file": read_file,
    "list_files": list_files,
    "run_tests": run_tests,
}
