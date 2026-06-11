---
name: unit-test-quality
description: "Use when writing, reviewing, hardening, or setting CI standards for unit tests and test suites; when tests need to be fast, isolated, deterministic, behavior-focused, mutation-resistant, low-flake, or free of test smells; or when coverage numbers need interpretation instead of blind maximization. NOT for test-first feature work itself (use TDD), continuous coverage backfill (use test-backfill-loop), or broad multi-metric hardening (use optimization-loop)."
tags:
  - testing
  - quality
  - validation
maturity: linted
---

# Unit Test Quality

Use this skill to make unit tests worth trusting. A high-quality unit test is fast, isolated, repeatable, self-checking, and focused on observable behavior. Coverage can show what executed; it does not prove the test would catch a regression.

**Output:** a test-quality judgment or improvement plan with concrete file/test references, the commands that prove the suite ran, and the next smallest changes to improve diagnostic value, determinism, and defect-detection strength.

## When to Use

- Writing tests for code that already has a known behavior contract.
- Reviewing a PR that adds or changes unit tests.
- Cleaning up brittle, slow, flaky, over-mocked, or low-signal tests.
- Setting unit-test CI gates, changed-code coverage expectations, mutation-testing scope, or flaky-test handling.
- Interpreting coverage reports without treating a percentage as proof of quality.

## When NOT to Use

- New feature or bugfix implementation that needs test-first discipline — use TDD.
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
3. **Check isolation and determinism.** Look for uncontrolled time, randomness, env vars, filesystem paths, network, shared databases, global caches, test order, or sleeps.
4. **Check assertion strength.** Prefer observable outputs and state. Use interaction assertions only when the interaction is part of the contract.
5. **Check setup shape.** Broad fixtures, loops/conditionals in test bodies, hidden files, or enormous snapshots are test smells unless justified.
6. **Run the right command.** The suite must execute and report real results. For changed tests, run the focused test command; for review completion, run the repo's declared gate.
7. **Escalate weak confidence.** If coverage is high but assertion strength is unclear, add a mutation/bite check for the changed behavior or file a follow-up with exact scope.

For metrics, language/tool examples, smell taxonomy, and CI lanes, read [references/unit-test-quality-playbook.md](references/unit-test-quality-playbook.md).

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
