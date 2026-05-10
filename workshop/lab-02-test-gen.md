# Lab 02 — Automated Test Generation with Codex

**Duration:** 35 minutes  
**Level:** Intermediate  
**Prerequisites:** Lab 01 complete, pytest installed

---

## Learning Objectives

- Use Codex to generate pytest unit tests for untested legacy code
- Understand the agentic verify-and-fix loop (generate → run → fix)
- Evaluate test quality: coverage, edge cases, mocking
- Discuss where AI-generated tests add value vs. where they fall short

---

## Background

Low test coverage is one of the most common blockers to safe refactoring. Writing tests for legacy code is tedious — you have to understand the code, identify all the paths, and write boilerplate. Codex can do the first draft in seconds.

The critical difference from naive code generation: this agent **runs the tests** after generating them. If they fail, it reads the error and fixes them. This self-correcting loop is what makes the output production-ready rather than just plausible-looking.

---

## Step 1 — Inspect the legacy file

Open `examples/legacy_flask_app.py`. Note:
- No tests exist for this file
- Several functions have no input validation
- There's a SQL injection vulnerability in `create_user`
- `calculate_discount` has no edge case handling

**Question:** Which functions would you prioritise testing first, and why?

---

## Step 2 — Generate tests

```bash
python -m cli.main test-gen --file examples/legacy_flask_app.py
```

The agent will:
1. Read the source file
2. Identify all testable functions
3. Generate a pytest file
4. Run the tests
5. Fix any failures (up to `MAX_TOOL_ROUNDS` iterations)

---

## Step 3 — Review the generated tests

Open `output/test_legacy_flask_app.py`.

**Checklist:**
- [ ] Are all public functions covered?
- [ ] Are there happy path tests?
- [ ] Are there edge case tests (empty input, None, boundary values)?
- [ ] Are Flask routes tested using the test client?
- [ ] Are external dependencies (SQLite) mocked?
- [ ] Do the tests actually pass?

Run them yourself:
```bash
pytest output/test_legacy_flask_app.py -v
```

---

## Step 4 — Improve coverage

**Exercise A:** The SQL injection in `create_user` should be tested. Add a test that demonstrates the vulnerability, then fix the source code and verify the test now passes safely.

**Exercise B:** Modify the system prompt in `cli/test_gen.py` to explicitly request:
- Property-based tests using `hypothesis`
- Parametrized tests for `calculate_discount` with multiple input combinations

**Exercise C:** Run coverage:
```bash
pip install pytest-cov
pytest output/test_legacy_flask_app.py --cov=examples --cov-report=term-missing
```
What's the coverage percentage? What's still missing?

---

## Step 5 — The verify loop in action

Run with `--no-verify` to skip the self-correction loop:
```bash
python -m cli.main test-gen --file examples/legacy_flask_app.py --no-verify
```

Compare the output quality. Does the verify loop make a meaningful difference?

---

## Wrap-up

**Key takeaways:**
- The generate → run → fix loop is essential for production-quality output
- AI-generated tests are best for boilerplate coverage; humans should write tests for business-critical logic
- Test generation is a forcing function: it reveals untestable code (tight coupling, no DI, global state)
- This pattern scales: run it as a pre-merge check to enforce minimum coverage thresholds

**Next:** [Lab 03 — Migration Assist](lab-03-migration-assist.md)
