# Lab 01 — AI-Powered PR Review with Codex

**Duration:** 30 minutes  
**Level:** Intermediate  
**Prerequisites:** Python 3.11+, OpenAI API key, repo cloned

---

## Learning Objectives

By the end of this lab you will:
- Understand how Codex uses tool-use to reason about real code (not just prompts)
- Run an automated PR review against a sample diff
- Interpret the structured output and discuss it as a team
- Know how to wire this into a GitHub Actions workflow

---

## Background

Traditional code review is slow, inconsistent, and expensive. A senior engineer reviewing a 500-line diff might spend 45 minutes on it. Codex can produce a structured first-pass review in under 30 seconds — not to replace human review, but to surface obvious issues before the human reviewer even opens the PR.

The key insight: Codex doesn't just read the diff. It uses **tool calls** to fetch surrounding context from the codebase, so it understands *why* a change was made, not just *what* changed.

---

## Step 1 — Set up your environment

```bash
# Clone the repo
git clone https://github.com/agaleaniket10/codex-sdlc-copilot.git
cd codex-sdlc-copilot

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set your API key
export OPENAI_API_KEY=sk-...
```

---

## Step 2 — Inspect the sample diff

Open `examples/sample_pr_diff.txt` and read through it. This is a real-world style diff of a Flask authentication module.

**Discussion questions (5 min):**
- What security issues can you spot manually?
- What would you flag in a human code review?
- How long did it take you to read it?

---

## Step 3 — Run the Codex review

```bash
python -m cli.main pr-review --diff examples/sample_pr_diff.txt
```

Watch the terminal output. You'll see:
1. The agent starting its tool-use loop
2. Any tool calls Codex makes (e.g. reading related files)
3. The structured review rendered as a table
4. A Markdown report saved to `output/`

---

## Step 4 — Analyse the output

Open `output/pr-review-sample_pr_diff.md`.

**Discussion questions (10 min):**
- Did Codex catch the issues you spotted manually?
- Did it find anything you missed?
- Were there false positives? Why might that happen?
- How would you tune the system prompt to reduce noise?

---

## Step 5 — Customise the system prompt

Open `cli/pr_review.py` and find `SYSTEM_PROMPT`. Try modifying it:

**Exercise A:** Add a rule: *"Flag any use of MD5 for password hashing as CRITICAL"*  
**Exercise B:** Add a dimension: *"API design — check for REST convention violations"*  
**Exercise C:** Change the output format to include a `confidence` field (0.0–1.0) per issue

Re-run after each change and compare outputs.

---

## Step 6 — Wire it to GitHub Actions (optional)

If you have a GitHub repo with Actions enabled:

1. Add your `OPENAI_API_KEY` as a repository secret
2. Copy `.github/workflows/pr-review.yml` to your repo
3. Open a PR and watch the automated review appear as a comment

---

## Wrap-up

**Key takeaways:**
- Tool-use is what makes Codex reviews *contextual*, not just syntactic
- The system prompt is your primary lever for tuning quality and focus
- This pattern works for any diff — not just Python, not just Flask
- The GitHub Action makes this zero-friction for your team

**Next:** [Lab 02 — Test Generation](lab-02-test-gen.md)
