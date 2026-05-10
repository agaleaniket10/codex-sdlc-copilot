# Lab 03 — Code Migration with Codex

**Duration:** 35 minutes  
**Level:** Advanced  
**Prerequisites:** Labs 01 and 02 complete, familiarity with FastAPI

---

## Learning Objectives

- Use Codex to migrate a legacy Flask app to FastAPI
- Understand how the agent reasons about framework patterns, not just syntax
- Evaluate migration quality: correctness, idioms, breaking changes
- Build a repeatable migration workflow for your team

---

## Background

Framework migrations are expensive. A typical Flask → FastAPI migration for a mid-size codebase takes weeks of engineering time. The risk isn't just the rewrite — it's the subtle behavioural differences that only surface in production.

Codex can produce a first-pass migration in minutes. More importantly, it annotates every significant change with `# MIGRATION:` comments, giving your team a clear audit trail of what changed and why.

---

## Step 1 — Review the legacy app

Re-read `examples/legacy_flask_app.py`. Key patterns to note:
- Synchronous route handlers
- Raw SQLite with string interpolation (SQL injection risk)
- MD5 password hashing
- No type hints
- No dependency injection

---

## Step 2 — Run the migration

```bash
python -m cli.main migration-assist \
  --file examples/legacy_flask_app.py \
  --target fastapi
```

The agent will:
1. Read the source file
2. Analyse the framework patterns in use
3. Produce a migrated FastAPI version
4. Generate a migration summary with breaking changes

---

## Step 3 — Review the migrated code

Open `output/legacy_flask_app_fastapi.py` and `output/migration-summary-legacy_flask_app-to-fastapi.md`.

**Review checklist:**
- [ ] Are all routes present and correctly mapped?
- [ ] Are route parameters typed correctly (Path, Query, Body)?
- [ ] Is async/await used appropriately?
- [ ] Are Pydantic models used for request/response validation?
- [ ] Is the SQL injection fixed?
- [ ] Is the MD5 hashing replaced with bcrypt/passlib?
- [ ] Are `# MIGRATION:` comments present and accurate?

---

## Step 4 — Test the migration

Install FastAPI and run the migrated app:
```bash
pip install fastapi uvicorn[standard] passlib[bcrypt]
uvicorn output.legacy_flask_app_fastapi:app --reload
```

Open `http://localhost:8000/docs` — FastAPI's auto-generated OpenAPI docs should show all your routes.

**Exercise:** Write a quick smoke test using `httpx`:
```python
import httpx
client = httpx.Client(base_url="http://localhost:8000")
response = client.get("/users")
assert response.status_code == 200
```

---

## Step 5 — Try other targets

```bash
# Migrate to async Flask (same framework, modernised patterns)
python -m cli.main migration-assist \
  --file examples/legacy_flask_app.py \
  --target async

# Migrate to Django REST Framework
python -m cli.main migration-assist \
  --file examples/legacy_flask_app.py \
  --target django5
```

Compare the migration summaries. Which target has the most breaking changes? Why?

---

## Step 6 — Bring your own code (optional)

If you have a legacy Python file in your own codebase:
1. Copy it to `examples/`
2. Run migration-assist against it
3. Review the output with the team

**Discussion:** What would you need to add to the system prompt to handle your specific codebase patterns?

---

## Wrap-up

**Key takeaways:**
- Codex migrations are a starting point, not a finished product — human review of `# MIGRATION:` comments is essential
- The migration summary's "Breaking Changes" section is the most valuable output for planning
- This pattern works best for well-structured, modular code; tightly coupled monoliths need decomposition first
- Pair this with the test-gen mode: generate tests *before* migrating, then verify they still pass after

---

## Full Workshop Debrief (15 min)

After completing all three labs, discuss as a team:

1. **Where did Codex add the most value?** (speed, consistency, coverage, something else?)
2. **Where did it fall short?** (false positives, missed issues, wrong idioms?)
3. **What would you adopt today?** Which mode would you wire into your CI/CD pipeline first?
4. **What's your biggest concern?** (cost, latency, accuracy, security, developer trust?)
5. **What's your 30-day adoption plan?**
