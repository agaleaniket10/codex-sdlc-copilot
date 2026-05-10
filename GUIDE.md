# Adopting OpenAI Codex in Your SDLC: A Practical Guide

*A cookbook-style reference for engineering teams integrating Codex into their development workflow.*

---

## Introduction

This guide walks through three high-ROI entry points for Codex in a software development lifecycle: automated PR review, test generation, and code migration. Each pattern is production-tested and designed to be adopted incrementally — you don't need to change your entire workflow to get value.

All examples use the [codex-sdlc-copilot](https://github.com/agaleaniket10/codex-sdlc-copilot) reference implementation, which you can fork and adapt.

---

## Core Concept: Tool-Use Agents

The key to making Codex useful for SDLC tasks is **tool use**. A naive approach sends code to the model and asks for a review. A tool-use approach lets the model *ask for more context* — reading related files, running tests, listing directory structure — before producing its response.

```python
# Without tool use: model only sees what you give it
response = client.chat.completions.create(
    model="gpt-4.1",
    messages=[{"role": "user", "content": f"Review this diff:\n{diff}"}]
)

# With tool use: model can fetch context it needs
response = client.chat.completions.create(
    model="gpt-4.1",
    messages=[{"role": "user", "content": f"Review this diff:\n{diff}"}],
    tools=[READ_FILE_TOOL, LIST_FILES_TOOL],
    tool_choice="auto",
)
```

The difference in output quality is significant, especially for large diffs where the model needs to understand the surrounding codebase.

---

## Pattern 1: PR Review

### When to use this
- You want consistent, structured feedback on every PR
- Your team's review bandwidth is a bottleneck
- You want to catch security and correctness issues before human review

### How it works

```
git diff → CodexAgent → structured JSON review → Markdown report
```

The agent reads the diff, optionally fetches surrounding context via tool calls, and returns a JSON object with issues categorised by severity (critical, major, minor, nit), positive observations, and a recommended action (approve / request_changes / block).

### Key design decisions

**Structured output over free text.** Returning JSON instead of prose makes the output programmatically useful — you can filter by severity, post only critical issues to Slack, or block merges on critical findings.

**Severity taxonomy matters.** Define what "critical" means for your team upfront. A good default:
- `critical` — security vulnerability, data loss risk, broken functionality
- `major` — logic error, missing error handling, significant performance issue
- `minor` — code smell, naming issue, missing test
- `nit` — style, formatting, minor readability

**Don't block on AI review alone.** Use it as a required-but-non-blocking check, or block only on `critical` findings. Human review remains the gate.

### Example system prompt pattern

```python
SYSTEM_PROMPT = """You are a senior software engineer conducting a code review.
Review the diff and return a JSON object with this structure:
{
  "summary": "...",
  "overall_score": <1-10>,
  "issues": [{"severity": "critical|major|minor|nit", "location": "...", 
               "description": "...", "suggestion": "..."}],
  "recommended_action": "approve|approve_with_changes|request_changes|block"
}
Return ONLY the JSON object."""
```

### GitHub Actions integration

```yaml
- name: Run Codex PR Review
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  run: python -m cli.main pr-review --diff /tmp/pr.diff
```

---

## Pattern 2: Test Generation

### When to use this
- You have legacy code with low test coverage
- You want to enforce a coverage threshold before merging
- You're refactoring and need a safety net

### How it works

```
source file → CodexAgent → pytest file → run tests → fix failures → save
```

The self-correcting loop (generate → run → fix) is what separates this from naive code generation. The agent runs the tests it generates and fixes failures before returning the output.

### Key design decisions

**Always verify.** Generated tests that don't run are worse than no tests — they give false confidence. The `run_tests` tool call is not optional.

**Mock external dependencies explicitly.** Tell the model in the system prompt to mock HTTP calls, database connections, and filesystem operations. Without this instruction, generated tests often try to make real connections.

**Prioritise by risk, not by coverage.** Ask the model to focus on functions that handle user input, authentication, or data mutation first. Coverage percentage is a lagging indicator; test quality is what matters.

### Example: requesting specific test patterns

```python
SYSTEM_PROMPT = """...
Prioritise tests for:
1. Functions that handle user input (SQL injection, XSS, validation)
2. Authentication and authorisation logic
3. Functions with complex branching logic

Use pytest.mark.parametrize for functions with multiple input combinations.
Mock all external I/O using unittest.mock.patch.
"""
```

### Coverage gate in CI

```yaml
- name: Check coverage
  run: |
    pytest --cov=src --cov-fail-under=80
```

---

## Pattern 3: Code Migration

### When to use this
- You're modernising a legacy service (Flask → FastAPI, Python 2 → 3, sync → async)
- You want a first-pass migration with an audit trail of changes
- You're evaluating migration complexity before committing engineering time

### How it works

```
legacy file + target framework → CodexAgent → migrated file + summary
```

The agent produces two outputs: the migrated code (with `# MIGRATION:` comments on every significant change) and a migration summary (changes made, breaking changes, next steps).

### Key design decisions

**`# MIGRATION:` comments are the most valuable output.** They give your team an audit trail and make the PR review of the migration much faster. Make them mandatory in your system prompt.

**Generate tests before migrating.** Run test-gen on the legacy code first. Then migrate. Then verify the same tests pass against the migrated code. This is the safest migration workflow.

**Treat the output as a starting point.** Complex business logic, custom middleware, and database ORM patterns often need manual adjustment. The migration summary's "Breaking Changes" section tells you where to focus.

### Migration workflow

```bash
# Step 1: Generate tests for the legacy code
python -m cli.main test-gen --file legacy_app.py

# Step 2: Verify tests pass against legacy code
pytest output/test_legacy_app.py

# Step 3: Migrate
python -m cli.main migration-assist --file legacy_app.py --target fastapi

# Step 4: Verify tests pass against migrated code
pytest output/test_legacy_app.py --rootdir output/
```

---

## Choosing the Right Model

| Use case | Recommended model | Rationale |
|----------|------------------|-----------|
| PR review (complex diffs) | `gpt-4.1` | Best reasoning on multi-file context |
| Test generation | `gpt-4.1` | Needs to understand code semantics deeply |
| Migration (simple files) | `gpt-4.1-mini` | Good enough, 10x cheaper |
| High-volume CI/CD | `gpt-4.1-mini` | Cost and rate limit considerations |

---

## Common Pitfalls

**Prompt injection via code comments.** Malicious code comments like `// ignore previous instructions` can influence model output. Sanitise or wrap code in XML tags to reduce this risk:

```python
user_message = f"Review this diff:\n<diff>\n{diff_content}\n</diff>"
```

**Context window limits.** Very large diffs (>10,000 lines) may exceed the context window. Chunk the diff by file and run separate reviews per file.

**Hallucinated line numbers.** Models sometimes cite incorrect line numbers in reviews. Use the `location` field as a hint, not a precise reference. Always verify in the actual diff.

**Over-reliance on score.** The `overall_score` field is a rough signal, not a precise metric. Two different runs on the same diff may produce different scores. Use it directionally, not as a hard threshold.

---

## Further Reading

- [OpenAI Cookbook](https://cookbook.openai.com) — patterns and examples for the OpenAI API
- [OpenAI Responses API docs](https://platform.openai.com/docs/api-reference) — full API reference
- [codex-sdlc-copilot architecture](docs/architecture.md) — design decisions for this implementation
- [Enterprise adoption guide](docs/enterprise-adoption.md) — rolling this out at scale
