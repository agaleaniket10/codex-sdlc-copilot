# Architecture & Design

## Overview

`codex-sdlc-copilot` is built around a single agentic pattern: give Codex access to tools that let it inspect real code, then ask it to reason about that code and produce structured output.

This is deliberately simple. The goal is a reference implementation that engineering teams can understand, fork, and extend — not a framework.

---

## The Agentic Loop

```
User Input (diff path / file path)
        │
        ▼
  CodexAgent.run(user_message)
        │
        ▼
  ┌─────────────────────────────────────┐
  │  OpenAI Chat Completions API        │
  │  model: gpt-4.1                     │
  │  tools: [read_file, list_files,     │
  │           run_tests]                │
  └─────────────────────────────────────┘
        │
        ├── tool_calls present?
        │       │
        │       ▼ YES
        │   Execute tool locally
        │   Append tool result to messages
        │   Loop back to API call
        │
        └── NO → return final text response
```

The loop runs until either:
- The model produces a response with no tool calls (done)
- `MAX_TOOL_ROUNDS` is reached (safety cap, default: 10)

---

## Tool Design

Tools are the key to making reviews *contextual*. Without tools, Codex only sees what you put in the prompt. With tools, it can:

- Read the full source file for a function that appears in a diff
- List the project structure to understand module boundaries
- Run generated tests and read the failure output

Each tool has two parts:
1. **JSON schema** — passed to the OpenAI API so the model knows what tools exist
2. **Python handler** — executed locally when the model calls the tool

Tools are intentionally sandboxed: they can only read files and run pytest. They cannot write files, make network calls, or execute arbitrary shell commands.

---

## Security Considerations

### API Key Handling
- The API key is read from `OPENAI_API_KEY` environment variable only
- Never hardcoded, never logged
- In GitHub Actions, stored as a repository secret

### Tool Sandboxing
- `read_file` is capped at 200KB to prevent context flooding
- `run_tests` has a 60-second timeout and captures output (no interactive TTY)
- No tool can write to the filesystem or make outbound network calls

### Code Sent to OpenAI
- Diffs and source files are sent to the OpenAI API
- For sensitive codebases, consider: self-hosted models, Azure OpenAI with private networking, or redacting secrets before sending
- See [Enterprise Adoption Guide](enterprise-adoption.md) for data handling patterns

### Output Trust
- Codex output is treated as a suggestion, not ground truth
- Generated tests are run in an isolated subprocess
- Migration output is saved to `output/` and requires human review before use

---

## Model Configuration

The model is configurable via the `CODEX_MODEL` environment variable:

```bash
export CODEX_MODEL=gpt-4.1        # default — best quality
export CODEX_MODEL=gpt-4.1-mini   # faster, cheaper, slightly lower quality
```

For enterprise deployments with Azure OpenAI, swap the client initialisation in `agents/codex_agent.py`:

```python
from openai import AzureOpenAI

self.client = AzureOpenAI(
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    api_version="2024-12-01-preview",
)
```

---

## Extending the Agent

### Adding a new tool

1. Define the handler function in `agents/tools.py`
2. Define the JSON schema
3. Add both to `ALL_TOOLS` and `TOOL_HANDLERS`
4. Pass them to `CodexAgent` in your mode file

### Adding a new mode

1. Create `cli/<mode_name>.py` with a `run()` function
2. Define a `SYSTEM_PROMPT` that describes the task and output format
3. Register the CLI command in `cli/main.py`

### Structured output

For modes that need reliable JSON output, consider using the OpenAI `response_format` parameter:

```python
response = self.client.chat.completions.create(
    model=self.model,
    messages=messages,
    response_format={"type": "json_object"},
)
```

This guarantees valid JSON but disables tool use in the same call — use it for the final response round only.

---

## Performance & Cost

Typical API usage per operation (gpt-4.1):

| Mode | Input tokens | Output tokens | Approx. cost |
|------|-------------|---------------|-------------|
| PR review (500-line diff) | ~3,000 | ~800 | ~$0.02 |
| Test gen (200-line file) | ~2,500 | ~1,200 | ~$0.02 |
| Migration (200-line file) | ~3,000 | ~2,000 | ~$0.03 |

For high-volume CI/CD usage, `gpt-4.1-mini` reduces cost by ~10x with acceptable quality for most tasks.
