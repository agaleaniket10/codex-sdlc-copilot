# Enterprise Adoption Guide

A practical guide for rolling out `codex-sdlc-copilot` patterns across an engineering organisation.

---

## Adoption Phases

### Phase 1 — Pilot (Weeks 1–2)
**Goal:** Prove value with a single team, low risk.

- Pick one team with an active codebase and willing engineers
- Start with PR review only — it's read-only, zero risk to production
- Run it manually (CLI) before automating
- Collect feedback: false positive rate, missed issues, time saved

**Success metric:** Team voluntarily uses it on >50% of PRs by end of week 2.

### Phase 2 — Automate (Weeks 3–4)
**Goal:** Remove friction, make it the default.

- Wire the GitHub Action into the team's repo
- Add `OPENAI_API_KEY` as a repository secret (or org-level secret)
- Set up a Slack/Teams notification for reviews with score < 6
- Run test-gen on the 5 most-changed files in the last quarter

**Success metric:** Zero manual steps required for PR review.

### Phase 3 — Scale (Month 2+)
**Goal:** Expand to more teams and more modes.

- Roll out to 3–5 additional teams
- Enable test-gen as a pre-merge coverage gate
- Identify 1–2 migration candidates (legacy services due for modernisation)
- Build an internal "Codex patterns" wiki based on what's working

**Success metric:** >80% of PRs across all enrolled teams get a Codex review.

---

## Data Handling & Privacy

### What gets sent to OpenAI

| Mode | Data sent |
|------|-----------|
| PR review | Git diff (code changes only, not full files unless tool-called) |
| Test gen | Source file contents |
| Migration | Source file contents |

### Mitigations for sensitive codebases

**Option 1: Azure OpenAI with private networking**
- Deploy via Azure OpenAI Service in your tenant
- Use VNet integration to keep traffic off the public internet
- Data is not used for model training (enterprise agreement)

**Option 2: Secret scrubbing**
- Add a pre-processing step to redact secrets, API keys, and PII before sending
- Use tools like `detect-secrets` or `truffleHog` to identify sensitive patterns

**Option 3: Self-hosted models**
- For the highest sensitivity requirements, swap `CodexAgent` to use a self-hosted model via Ollama or vLLM
- Quality will be lower for complex reasoning tasks — benchmark first (see [local-llm-benchmark-suite](https://github.com/agaleaniket10/local-llm-benchmark-suite))

---

## Access Control

### API Key Management
- Use a dedicated API key per team or per environment (not a shared org key)
- Set spend limits per key in the OpenAI dashboard
- Rotate keys quarterly

### GitHub Actions
- Store `OPENAI_API_KEY` as an **environment secret** (not a repo secret) to scope it to specific workflows
- Use `permissions: pull-requests: write` only — do not grant write access to code

### Rate Limiting
- The OpenAI API has per-minute token limits
- For large orgs, request a rate limit increase or implement a queue
- `gpt-4.1-mini` has higher default rate limits than `gpt-4.1`

---

## Change Management

### Common objections and responses

**"I don't trust AI to review my code."**
> Frame it as a first-pass triage tool, not a replacement for human review. It catches the obvious stuff so your senior engineers can focus on architecture and business logic.

**"What if it misses something critical?"**
> It will. So do human reviewers. The goal is to raise the floor, not replace judgment. Keep your existing review process; add Codex as an additional signal.

**"Our code is proprietary — I don't want it sent to OpenAI."**
> Valid concern. Use Azure OpenAI with a data processing agreement, or self-host. We can walk through the architecture for your specific compliance requirements.

**"This will make junior engineers lazy."**
> The opposite tends to happen. Seeing Codex catch issues they missed is a learning signal. Many engineers report it accelerates their growth by showing them patterns they hadn't considered.

### Measuring ROI

Track these metrics before and after adoption:

| Metric | How to measure |
|--------|---------------|
| PR cycle time | GitHub Insights: time from PR open to merge |
| Review comments per PR | GitHub API |
| Post-merge bug rate | Incident tracking (PagerDuty, Jira) |
| Test coverage trend | pytest-cov in CI |
| Engineer satisfaction | Quarterly survey |

---

## Support & Escalation

For issues with the tool:
- Open a GitHub issue on [codex-sdlc-copilot](https://github.com/agaleaniket10/codex-sdlc-copilot)

For OpenAI API issues:
- [OpenAI Status Page](https://status.openai.com)
- [OpenAI Developer Forum](https://community.openai.com)

For enterprise OpenAI support:
- Contact your OpenAI account team for SLA-backed support
