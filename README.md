# codex-sdlc-copilot

> An agentic reference implementation using **OpenAI Codex** to automate high-ROI tasks across the software development lifecycle — PR review, test generation, and code migration.

Built as a cookbook-style reference for engineering teams adopting Codex. Designed to be demoed, forked, and extended.

---

## Why This Exists

Most teams know AI can help with coding. Few have a clear, production-ready pattern for *where* to plug it into their SDLC. This project answers that question with three concrete, battle-tested entry points:

| Mode | Pain Point Solved | ROI Signal |
|------|------------------|------------|
| `pr-review` | Inconsistent, slow code reviews | Faster merge cycles, fewer regressions |
| `test-gen` | Low test coverage on legacy code | Reduced QA burden, safer refactors |
| `migration-assist` | Costly framework migrations | Accelerated modernisation, lower risk |

Each mode is a standalone module you can adopt independently or chain together.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  codex-sdlc-copilot                  │
│                                                     │
│  CLI / GitHub Action                                │
│       │                                             │
│       ▼                                             │
│  CodexAgent (agents/codex_agent.py)                 │
│  ┌─────────────────────────────────────────────┐   │
│  │  OpenAI Responses API  (gpt-4.1 / codex)    │   │
│  │  + Tool Use loop                            │   │
│  └─────────────────────────────────────────────┘   │
│       │                                             │
│       ▼                                             │
│  Tools: read_file │ run_tests │ fetch_pr_diff       │
│       │                                             │
│       ▼                                             │
│  Structured Output (JSON) → Markdown Report         │
└─────────────────────────────────────────────────────┘
```

The agent uses a **tool-use loop**: Codex decides which tools to call, inspects real code, then produces a structured response. No hardcoded prompts — the agent reasons about the actual diff or file it receives.

See [`docs/architecture.md`](docs/architecture.md) for the full design walkthrough.

---

## Quickstart

### 1. Clone and install

```bash
git clone https://github.com/agaleaniket10/codex-sdlc-copilot.git
cd codex-sdlc-copilot
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Set your API key

```bash
export OPENAI_API_KEY=sk-...
```

### 3. Run a mode

```bash
# Review a PR diff
python -m cli.main pr-review --diff examples/sample_pr_diff.txt

# Generate tests for a file
python -m cli.main test-gen --file examples/legacy_flask_app.py

# Migrate legacy code to a modern framework
python -m cli.main migration-assist --file examples/legacy_flask_app.py --target fastapi
```

---

## GitHub Action: Auto PR Review

Add this to your repo and every PR gets an automated Codex review posted as a comment.

```yaml
# .github/workflows/pr-review.yml
on:
  pull_request:
    types: [opened, synchronize]
```

See [`.github/workflows/pr-review.yml`](.github/workflows/pr-review.yml) for the full workflow.

---

## Workshop

The [`workshop/`](workshop/) folder contains hands-on lab guides designed for a 2-hour engineering team enablement session. Each lab is self-contained with sample code, exercises, and discussion prompts.

- [Lab 01 — PR Review](workshop/lab-01-pr-review.md)
- [Lab 02 — Test Generation](workshop/lab-02-test-gen.md)
- [Lab 03 — Migration Assist](workshop/lab-03-migration-assist.md)

---

## Docs

- [Architecture & Design](docs/architecture.md)
- [Enterprise Adoption Guide](docs/enterprise-adoption.md)
- [Adoption Guide (Cookbook style)](GUIDE.md)

---

## Stack

- **OpenAI Responses API** — `gpt-4.1` with tool use
- **Python 3.11+**
- **GitHub Actions** — CI/CD integration
- **Rich** — terminal output formatting
- **PyGithub** — PR diff fetching

---

## Why Codex Over Local Models

I built [`local-llm-benchmark-suite`](https://github.com/agaleaniket10/local-llm-benchmark-suite) to understand model tradeoffs at the inference layer. The benchmarks showed that for SDLC tasks requiring long context, precise instruction-following, and consistent structured output, cloud-hosted Codex outperforms local 7–9B models significantly — especially on multi-file reasoning and test generation accuracy. Local models remain valuable for privacy-sensitive or offline scenarios.

---

## License

MIT
