# Forge Run: unit-test-quality

> Forged in the `skill-forge-queue` batch (workflow `wf_69844160-67c`, 2026-06-12),
> forger != judge. Full verbatim RED transcripts and per-judge evidence live in
> that workflow run; this package records the scenario focus, the GREEN closure,
> the 3/3 REFACTOR verdicts, and the lint result.

## Scenario Set

| ID | Pressure focus |
|----|----------------|
| SF-021-RED-1 | AI slop tests: execute-only/tautology assertions, over-mocking, coverage chasing, flaky/order-dependent, accepting AI tests that don't pin behavior |

## RED Evidence

A fresh pressure-tester (no skill loaded) authored a scenario in the focus area
above and surfaced 8 verbatim rationalizations a capable agent reaches for
under deadline/convenience pressure (captured in the workflow transcript). A real
failure surfaced (needs_stronger_scenario=false), so GREEN proceeded.

## GREEN Patch

- **Skill file changed:** `development/unit-test-quality/SKILL.md` (frontmatter description unchanged).
- **Closure:** A real failure surfaced: under a Friday coverage-gate deadline, all 8 named dodges produce tests that raise the number without pinning behavior. The skill addressed this in spirit (does-not-throw smell, over-mocking smell, tautology in the Quality Bar) but lacked hard, hittable gates against the specific dodges. Smallest-diff patch, edited only this SKILL.md: (1) tightened the slop-test rejection gate (step 3) with a load-bearing rule — the expected value must be derived independently from the contract (by hand/spec/reference), never copied from current output; coverage is a diagnostic, and a line executed without a pinned expected result does not count as covered. (2) Added a 'Known Pressure Rationalizations' table mapping each of the 8 named dodges -> required response (gate is a floor not proof; toBeDefined/not.toThrow banned as non-assertions; compute the fiddly total and assert equality; mock only the boundary, don't re-assert mocks or copy an over-mock pattern; snapshots only when the artifact is the contract; assert real expiry behavior not absence of throw; edge cases you wrote are pinned now not deferred; copying current output pins shipped bugs — characterization tests valid only when labeled over legacy code, not freshly-written code). (3) Added one Common Mistakes bullet closing the follow-up-ticket deferral. Frontmatter description unchanged (no skills.json desync); no new cross-file links added; no public-contract change; audit gate not run (concurrent forgers).

## REFACTOR Verdicts

| Run | Verdict | Notes |
|-----|---------|-------|
| 1 | COMPLY | independent judge; named dodges refused by concrete rules + the pressure table |
| 2 | COMPLY | independent judge |
| 3 | COMPLY | independent judge |

3/3 clean -> forged.

## Lint Evidence

- **Command:** `python scripts/audit-jar.py`
- **Result:** GREEN over the full batch: 208 checks, 0 failed.
