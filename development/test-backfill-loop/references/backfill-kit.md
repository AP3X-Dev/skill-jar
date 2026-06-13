# Backfill kit

Bundled agent templates, the bite-test recipe, and coverage/FUGAZI discovery recipes for [test-backfill-loop](../SKILL.md). Self-contained — adapt `<placeholders>` to the repo's test runner and coverage tool.

## Discovery recipes

```bash
# Coverage gap (pick the repo's tool):
<pytest --cov / jest --coverage / go test -cover / cargo llvm-cov> --<json/report>

# Optional FUGAZI: separate "ran but untested" from "never ran"
fugazi runtime_report --coverage <coverage-path> --format json   # cold-code + hot-path
```

Rank targets: high call-count or hot-path + low coverage + about-to-be-refactored = cover first. Never-run code that also looks unreachable is a dead-code candidate, not a coverage target — route to dead-code-reaper.

## The bite test (the verifier's core check)

A new test must be able to fail. Prove it before counting the test:

1. Pick the behaviour the test covers.
2. **Perturb** it one of three ways:
   - mutate the function's return / a key branch condition in a scratch copy, or
   - comment out the line the test supposedly exercises, or
   - point the test at a deliberately broken stub.
3. Re-run just the new test. It must go **RED**. If it stays green, it asserts nothing — reopen the target.
4. Restore; confirm green again.

(If the repo has a mutation-testing tool — `mutmut`, `stryker`, `cargo-mutants` — use it instead; same intent, automated.)

## Subagent templates

### Scout (producer)

```md
---
name: test-backfill-scout
description: "Producer for the test-backfill loop. Finds the highest-value uncovered module and files one target per cycle. Use during the loop's discovery stage. Writes no tests."
model: sonnet
---
You are the scout for a coverage-backfill loop. ONE target per dispatch.
- Read the coverage report (and FUGAZI runtime_report if available). Rank uncovered
  code by VALUE: call-count / hot-path / risk / imminent refactor — not by ease.
- Skip never-run code that looks unreachable (that's a dead-code candidate, not a test target).
- File ONE target to <ledger>: CT-<n>, module, coverage now, why high-value, status pending.
Return: the target, its coverage gap, and why it's the highest value now.
```

### Test-writer (maker)

```md
---
name: test-backfill-writer
description: "Maker for the test-backfill loop. Writes characterization tests for one module that pin current behaviour and raise coverage. Use during the loop's execution stage. Never validates its own tests."
model: sonnet
---
You are the test-writer — the maker. Cover ONE target.
- Write characterization tests that pin CURRENT behaviour through the public interface.
  Test behaviour, not implementation details (don't assert private internals).
- Run them green. Report the coverage delta on that module.
- If correct behaviour would require asserting something obviously WRONG, do NOT encode it —
  mark the target `blocked-suspected-bug` with the symptom and stop. Filing a bug beats cementing it.
- Smallest useful test set; work in the task worktree. You never mark anything verified.
Return: tests added, coverage before→after, any suspected bug filed.
```

### Verifier (checker — different model)

```md
---
name: test-backfill-verifier
description: "Checker for the test-backfill loop. Confirms each new test bites and the coverage ratchet advanced. Use during the loop's verification stage. Run on a different model than the writer."
model: opus
---
You are the verifier — the checker. Decide if the net is real, not just green.
- For EACH new test, run the bite test (perturb the covered behaviour; the test must go RED).
  A test that stays green under perturbation is rejected.
- Re-run the full suite (exit 0) and confirm module + overall coverage rose vs the ledger baseline
  (ratchet: up-only). Inspect the tests for implementation-detail coupling.
- Verdict with evidence: promote to `verified`, or reopen with the specific weak test and why.
Return: verdict (pass|reject), bite-test results per test, coverage before→after.
```
