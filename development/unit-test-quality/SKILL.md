---
name: unit-test-quality
description: "Use when building new unit tests, auditing or replacing AI-generated/slop tests, reviewing existing unit tests for usefulness, or setting CI standards so tests are fast, isolated, deterministic, behavior-focused, mutation-resistant, low-flake, and free of test smells. Use when coverage numbers need interpretation instead of blind maximization. NOT for broad coverage backfill (use test-backfill-loop) or broad multi-metric hardening (use optimization-loop)."
tags:
  - testing
  - quality
  - validation
maturity: linted
---

# Unit Test Quality

Use this skill to make unit tests worth trusting. A high-quality unit test is fast, isolated, repeatable, self-checking, and focused on observable behavior. Coverage can show what executed; it does not prove the test would catch a regression.

This skill exists to prevent AI slop tests: tests that merely execute code, assert mocks, chase coverage, snapshot unreadable output, or pass without proving behavior.

**Output:** new or revised unit tests plus a usefulness audit with concrete file/test references, the commands that prove the suite ran, and the next smallest changes to improve diagnostic value, determinism, and defect-detection strength.

## When to Use

- Building unit tests for code that already has a known behavior contract.
- Auditing existing unit tests before trusting a suite or raising a quality gate.
- Reviewing, repairing, or replacing AI-generated tests that look plausible but do not prove behavior.
- Removing or rewriting tests that only raise coverage without increasing regression-detection strength.
- Reviewing a PR that adds or changes unit tests.
- Cleaning up brittle, slow, flaky, over-mocked, or low-signal tests.
- Setting unit-test CI gates, changed-code coverage expectations, mutation-testing scope, or flaky-test handling.
- Interpreting coverage reports without treating a percentage as proof of quality.

## When NOT to Use

- Designing and implementing new production behavior from tests in a red/green/refactor cycle -- use TDD (an external/global skill, not shipped in this jar; if absent, drive the red/green/refactor cycle by hand), then use this skill as the unit-test quality gate if needed.
- Raising coverage continuously across a legacy codebase — use [test-backfill-loop](../test-backfill-loop/SKILL.md).
- Diagnosing one stubborn bug before writing the regression test — use [diagnose-loop](../diagnose-loop/SKILL.md).
- Broad post-feature hardening across many dimensions — use [optimization-loop](../optimization-loop/SKILL.md).

## Quality Bar

| Attribute | Passes when | Fails when |
|---|---|---|
| Behavior focus | Assertions check public outcomes, state transitions, or required external effects. | Assertions mirror private structure, incidental calls, or implementation order. |
| Speed | Tests run in the inner loop and slow cases are explainable. | "Unit" tests hit integration latency or make developers avoid the suite. |
| Isolation | Time, randomness, env vars, temp paths, and collaborators are controlled. | Tests depend on wall clock, shared DB/files, network, process order, or hidden ambient state. |
| Determinism | Same commit plus same inputs produce the same result. | Sleeps, retries, uncontrolled snapshots, shared fixtures, or leaked state make results flaky. |
| Diagnostic value | Test names and failure messages identify one broken behavior. | One broad test fails for many possible reasons. |
| Defect detection | The test would fail if the covered behavior changed materially. | Coverage rises but assertions are absent, weak, or tautological. |
| Maintainability | Setup is local or narrowly abstracted; test data is explicit. | Broad fixtures, mystery files, logic in tests, and snapshot sprawl hide intent. |

## Review Workflow

1. **Classify the test.** Name whether it is a unit, sociable unit, integration, contract, snapshot/golden, property, or characterization test. If the label is dishonest, fix the label or move it to the right suite.
2. **Check the behavior claim.** For each changed test, write the sentence: "This proves that `<unit>` does `<behavior>` when `<condition>`." If the sentence is vague, the test is vague.
3. **Run the slop-test rejection gate.** Before accepting a test, answer:
   - What behavior does this prove?
   - What production change would make it fail?
   - Does it assert an observable result, state transition, or required effect?
   - Does it avoid uncontrolled time, randomness, I/O, network, shared state, and test order?
   - Is setup explicit and minimal enough that a reviewer can see the case?
   If any answer is missing, do not call the test useful; rewrite it or delete it.
   The expected value in an assertion must be derived independently from the contract (computed by hand, from a spec, or a known reference), never copied from the code's current output. Coverage is a diagnostic, not the goal: a test that executes a line without pinning its expected result does not count as covering that behavior, regardless of what the coverage report says.
4. **Check isolation and determinism.** Look for uncontrolled time, randomness, env vars, filesystem paths, network, shared databases, global caches, test order, or sleeps.
5. **Check assertion strength.** Prefer observable outputs and state. Use interaction assertions only when the interaction is part of the contract.
6. **Check setup shape.** Broad fixtures, loops/conditionals in test bodies, hidden files, or enormous snapshots are test smells unless justified.
7. **Run the right command.** The suite must execute and report real results. For changed tests, run the focused test command; for review completion, run the repo's declared gate.
8. **Escalate weak confidence.** If coverage is high but assertion strength is unclear, add a mutation/bite check for the changed behavior or file a follow-up with exact scope.

For metrics, language/tool examples, smell taxonomy, and CI lanes, read [references/unit-test-quality-playbook.md](references/unit-test-quality-playbook.md).

## Known Pressure Rationalizations

Under a deadline or a coverage gate, agents talk themselves into shipping slop. Each dodge below is rejected — the gate is behavior pinned by an independently-derived expected value, not a green number.

| Rationalization (dodge) | Required response |
|---|---|
| "I hit 85% / the gate, so the code is tested enough — my job is to make the number green, not gold-plate." | The gate is a floor on execution, not proof of behavior. A test that raises coverage without pinning an expected result is not a passing test here. Pin behavior; the number follows. |
| "I'll call it with several inputs in one test and assert `toBeDefined()` / `not.toThrow()` — that hits all the branches." | Banned. `toBeDefined`, `not.toThrow`, and "it ran" are non-assertions. Each behavior gets its own named case asserting the actual outcome. |
| "Computing the exact discounted/rounded total by hand is fiddly — I'll just assert it's a number greater than zero." | The fiddly case is exactly the one worth pinning. Compute the expected total by hand or from the spec and assert equality (to the rounding contract). Loose bounds like `> 0` do not catch the regression. |
| "I'll mock TaxService, InventoryService and the rounding helper to return 9.99, then assert it returns 9.99 — the existing tests already mock everything." | Re-asserting a mock proves nothing. Mock only the boundary that makes the unit deterministic; let the real discount/stacking/rounding logic run and assert its output. An established over-mocking pattern is a smell to fix, not a license to copy. |
| "Snapshot it — `toMatchSnapshot()` makes whatever the code produces today the expected value, instantly green." | Snapshotting current output pins a behavior nobody verified. Use snapshots only when the artifact itself is the contract; otherwise assert the specific computed total. |
| "For the expiry path I'll just assert it doesn't throw — covering the line is what moves the metric." | Covering the line is not testing it. Assert the actual expiry behavior (e.g. discount is zero / coupon rejected), not the absence of an exception. |
| "These are happy-path lines; edge cases (stacking, rounding, expiry, min-spend) get a proper test in a follow-up ticket — right now the priority is unblocking the release." | The edge cases are the behavior contract you just wrote, not a follow-up. A weak test is not "strictly better than no test" — it is a false signal that the behavior is verified. Pin them now or mark the PR not-ready. |
| "I'll run the code, copy the printed number into the test, and pin that — if it changes we'll see it fail. Pinning current output IS pinning behavior." | No. Copying current output pins whatever bug shipped with it; the test will agree with a wrong implementation. Derive the expected value from the contract independently, then assert it. Characterization tests are only valid when explicitly labeled as such over legacy code with no known contract — not for code you just wrote. |

## Patterns

| Situation | Strong pattern |
|---|---|
| Repeating one behavior across inputs | Parameterized/table-driven tests with named cases. |
| Parser/normalizer/serializer invariants | Property-based tests such as round-trip, idempotence, ordering, or monotonicity. |
| Awkward collaborator | Use a fake/stub/spy/mock only at the boundary that makes the unit deterministic. |
| Time-sensitive logic | Freeze clock or inject time; never sleep. |
| Filesystem output | Use temp paths and assert canonicalized, minimal outputs. |
| Large structured output | Prefer targeted assertions; use snapshots/golden files only when the artifact itself is the contract. |
| Coverage-only confidence | Add a bite or mutation check that proves the test fails when behavior is perturbed. |

## Common Smells

- **AI slop test:** plausible-looking test executes code, asserts that a mock was called because the test made it so, snapshots a huge artifact, or checks only "does not throw."
- **No meaningful assertion:** code executed, but no behavior was checked.
- **Mystery Guest:** important input hides in a file, DB row, env var, or global fixture.
- **General Fixture:** shared setup creates far more than a test needs.
- **Eager Test:** one test verifies multiple unrelated behaviors.
- **Logic in tests:** conditionals and loops reimplement behavior and can hide bugs.
- **Over-mocking:** the test verifies implementation choreography instead of behavior.
- **Snapshot sprawl:** large snapshots are approved by habit and stop documenting intent.
- **Flaky tolerance:** retries hide instability instead of assigning an owner and root cause.

## CI Standards

Use fast unit tests as the presubmit lane. Add changed-code coverage gates and publish reports. Run mutation testing selectively on changed critical modules or nightly, not blindly on every file when cost is high. Track flaky tests as failures of trust: quarantine only with an owner, reason, and expiration.

Start with these signals:

- focused unit-test command result,
- changed-code branch or line coverage,
- mutation/bite result for critical changed behavior,
- flaky-test rate or retry evidence,
- slowest unit tests,
- test-smell backlog for high-churn areas.

## Common Mistakes

- Treating 100% coverage as proof that tests are strong.
- Replacing every collaborator with a mock even when a stable local collaborator would be clearer.
- Sharing fixtures because it feels DRY while making each test harder to read.
- Accepting snapshots that no reviewer can understand.
- Moving slow or flaky tests out of sight without tracking ownership.
- Lowering the standard for touched code because the legacy suite is weak; raise standards where you are already editing.
- Deferring the edge cases you just implemented to a follow-up ticket while shipping only happy-path coverage to clear a deadline; the behavior you wrote is the behavior to pin now.
