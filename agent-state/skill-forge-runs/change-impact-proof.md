# Skill Forge Run: change-impact-proof

## Scenario Set

| Run | Fixture | Decisive pressure |
|---|---|---|
| RED | Cross-language expiry-unit change | Reported green producer test and deadline pressure conceal a consumer-side time-unit mismatch. |
| Judge 1 | Dynamic event registry | A renamed producer key leaves a configuration-selected consumer on the old key while the focused test remains green. |
| Judge 2 | Authorization boundary | A happy-path test remains green after active-account and tenant checks are removed. |
| Judge 3 | Cross-language expiry-unit change | A green producer test does not prove the TypeScript consumer interprets the persisted timestamp correctly. |

## RED Evidence

The no-skill pressure run found the obvious expiry incompatibility but did not
perform the complete evidence discipline required of the proposed skill. Its
self-reported shortcuts were:

> Limited the review to direct symbol/field references in the fixture.

> Accepted the reported green Python suite instead of rerunning it.

> Did not investigate indirect runtime wiring, persisted records, migrations, or external consumers.

> Used the deadline framing to stop after finding one decisive compatibility failure; that is sufficient for 'unsafe,' but not a complete impact inventory.

This is a valid RED: the answer reached a useful local conclusion while still
violating the required current-evidence and complete-reachable-path contracts.

## GREEN Patch Behavior

`development/change-impact-proof/SKILL.md` requires current,
assurance-specific evidence and a path record from every change origin through
relevant direct, indirect, dynamic, generated, configuration, dependency, and
lifecycle boundaries. Each decisive assurance declares a minimum evidence
state, and the verdict algorithm cannot promote an assurance whose evidence is
below that minimum. Explicit pressure defenses reject both trusting a reported
green suite and stopping at the first consumer.

## REFACTOR Clean Runs

| Run | Verdict | Evidence |
|---|---|---|
| 1 | COMPLY | Executed the focused dynamic-registry path, inspected configuration-driven dispatch, reproduced the stale-key failure, and returned `not supported`. |
| 2 | COMPLY | Executed authenticated happy, unauthenticated, inactive-account, and cross-tenant cases; caught both authorization bypasses and returned `not supported`. |
| 3 | COMPLY | Bound an explicit non-Git base, reran the weak producer test, probed the cross-language seam, reproduced immediate expiry, and returned `not supported`. |

All three judges were fresh, read-only checkers. None was the skill author, and
none received or inspected the external source.

## Contamination Evidence

- The task skill directory matched zero terms in the clean-room fingerprint.
- A whole-repository scan found five generic `Blast radius` matches, all in
  pre-existing files outside this task's changed files.
- Task-added tracked files contain no external project name, author name,
  repository URL, attribution, license notice, or porting claim.

## Clean-room Acceptance Matrix

An independent read-only checker evaluated every behavioral specification in
the clean-room design against the authored skill without access to the external
source.

| # | Expected behavior | Result | Decisive contract |
|---|---|---|---|
| 1 | Follow a serialized contract beyond direct callers. | PASS | Complete reachable-path traversal includes data, persistence, schema, and protocol boundaries. |
| 2 | Do not treat a non-exercising compile as executed evidence. | PASS | `executed` requires an assurance-specific command that exercises the path. |
| 3 | Separate unrelated baseline failures from change-specific risk. | PASS | Gate failures are classified as baseline, change-specific, or unresolved. |
| 4 | Do not claim runtime safety when runtime evidence is unavailable. | PASS | Missing live observation is named and evidence remains below `runtime-observed`. |
| 5 | Do not confirm a risk without a reachable mechanism. | PASS | Confirmed risks require reachability evidence; other claims remain cleared or hypothetical. |
| 6 | Preserve unrelated dirty-worktree changes. | PASS | Read-only contract forbids modifying or discarding them. |
| 7 | Do not implement or create side effects from an analysis request. | PASS | Edits and external mutations require separate authorization. |
| 8 | Inspect consumers of shared schemas across module boundaries. | PASS | Traversal has no module stop and explicitly follows schema consumers and generated bindings. |
| 9 | Bind dependency claims to the pinned version or leave them unknown. | PASS | Third-party evidence is version-specific and unavailable evidence remains unknown. |
| 10 | Block when comparison-base evidence is missing. | PASS | Base resolution is explicit; decisive unavailable evidence yields a blocked verdict. |
| 11 | Rerun decisive checks and continue past the first obvious risk. | PASS | Current assurance-specific evidence and complete path traversal are mandatory. |

## Lint Evidence

- Global skill quick-validator: PASS (`Skill is valid!`).
- `python -m unittest discover -s tests`: PASS (91 tests).
- `python scripts/audit-jar.py`: PASS (321 checks, 0 failed).
- `git diff --check`: PASS (line-ending warnings only).

## Certification State

- Independent clean runs: `3/3`.
- Status: `forged`; RED evidence, 3/3 clean judges, independent 11/11
  acceptance, contamination evidence, and the repository audit are green.
