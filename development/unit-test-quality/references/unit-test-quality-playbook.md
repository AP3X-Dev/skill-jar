# Unit Test Quality Playbook

Use this reference when a task needs details beyond the main `unit-test-quality` workflow: metrics, smell triage, tool choices, and CI lanes.

## Quality Model

| Attribute | Practical check |
|---|---|
| Scope | One behavior per test. If the name needs "and", split it. |
| Speed | Track per-test p95 and total unit-suite runtime; optimize the slowest tests first. |
| Isolation | No uncontrolled network, DB, filesystem, env, clock, random, global cache, or order dependence. |
| Determinism | Same commit can pass repeatedly without retries. Any pass/fail on the same commit is flaky. |
| Diagnostic value | Failure message names the behavior and condition, not just a helper mismatch. |
| Defect detection | Tests fail when behavior is perturbed; mutation testing is stronger evidence than coverage alone. |
| Maintainability | Setup is explicit and narrow; helpers clarify intent instead of hiding it. |
| Low internal coupling | Prefer state/output assertions; use interaction assertions only for required effects. |
| Test data discipline | Keep input local and minimal. Version golden files and review them like code. |

## Metrics

| Metric | What it tells you | What it misses | Best use |
|---|---|---|---|
| Line/instruction coverage | Code executed during tests. | Assertion strength. | Find untested changed code. |
| Branch coverage | Decision paths executed. | Semantics inside a covered branch. | Gate risky condition-heavy changes. |
| Cyclomatic complexity | Where more paths may need tests. | Whether tests check the right thing. | Prioritize test cases. |
| Mutation score | Tests detect injected behavioral changes. | Tool cost; equivalent mutants need review. | Critical changed modules, nightly scans. |
| Flaky-test rate | Trustworthiness of test results. | Root cause. | Assign owners and stop silent retries. |
| Runtime percentiles | Feedback-loop health. | Semantic quality. | Keep unit tests inner-loop fast. |
| Test-smell count | Maintenance risk. | Immediate bug detection. | Review and refactoring backlog. |

Suggested starting thresholds are policy inputs, not universal truths:

- Changed-code branch coverage: warn below 90%, fail below the team's agreed floor.
- Mutation score on critical changed code: warn below 70%, block only where the team has accepted the cost.
- Flaky tests: treat new default-branch flakes as urgent; quarantine with owner and expiration.
- Unit-suite runtime: warn when the suite no longer runs comfortably in the developer inner loop.

## Tool Map

| Ecosystem | Coverage | Mutation | Notes |
|---|---|---|---|
| Java | JaCoCo | PIT | Mature coverage and mutation support. |
| Python | coverage.py, pytest-cov | mutmut | Good incremental mutation options. |
| JavaScript/TypeScript | Jest coverage, Istanbul/nyc | StrykerJS | Watch snapshot size and fake timers. |
| Go | `go test -cover` | go-mutesting/ooze-style tools | Native coverage is strong; mutation tooling varies. |
| .NET | Coverlet, dotnet-coverage | Stryker.NET | Good CI report integration. |

## Pattern Selection

| Need | Pattern | Guardrail |
|---|---|---|
| Many examples of same rule | Parameterized/table-driven tests | Give each case a diagnostic name. |
| Broad input space | Property-based tests | Assert invariants, not random examples. |
| Current legacy behavior before refactor | Characterization tests | Do not encode behavior you believe is a bug; file it. |
| Whole artifact is the contract | Golden/snapshot tests | Keep artifacts short, deterministic, and reviewed. |
| Remote or awkward dependency | Test double | Mock only the boundary needed for determinism. |
| Time/random/env behavior | Inject or freeze source | No sleeps, real clocks, or global randomness. |

## Smell Triage

| Smell | Symptom | Fix |
|---|---|---|
| No assertion | Test only calls code. | Assert returned value, state, event, or required interaction. |
| Mystery Guest | Important data comes from hidden files, DB, env, or global fixture. | Inline minimal data or name/version the artifact. |
| General Fixture | Shared setup creates objects most tests ignore. | Local setup, builders, or narrower fixtures. |
| Eager Test | One test validates a workflow of unrelated behaviors. | Split by behavior or move to integration suite. |
| Conditional logic | Test body computes expected behavior. | Parameterize or write explicit cases. |
| Over-mocking | Test breaks on harmless refactor. | Assert outcome; reserve interaction checks for contracts. |
| Brittle snapshot | Large diff nobody can review. | Replace with targeted assertions or smaller golden file. |
| Sleep/retry | Test hopes time passes. | Wait on a condition or inject deterministic scheduler/time. |

## CI Lanes

Use cost-appropriate lanes:

1. **PR presubmit:** focused unit tests, fast full unit suite, changed-code coverage, test report artifacts.
2. **Main branch:** full unit suite, trend coverage, flaky detection, slowest-test report.
3. **Nightly or scheduled:** selective mutation testing, broader smell scan, snapshot/golden review report.
4. **Quarantine process:** every quarantined test gets owner, reason, issue link, and expiration; retries do not make a flaky test healthy.

Minimal report set:

- JUnit or equivalent test report,
- coverage report for changed and overall code,
- mutation report when run,
- flaky/failed retry report,
- slowest test list.

## Review Prompts

Use these questions in PR review:

- What behavior does this test prove in one sentence?
- What regression would make this test fail?
- Could this pass if the implementation returned a constant, skipped a branch, or ignored a collaborator?
- Does it rely on uncontrolled time, random, order, environment, file paths, DB, or network?
- Is the setup readable without jumping through hidden fixtures?
- Is a mock verifying a public effect or just private choreography?
- If coverage improved, did assertion strength improve too?
