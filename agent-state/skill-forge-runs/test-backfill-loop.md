# Forge Run: test-backfill-loop

> Forged in the `skill-forge-queue` batch (workflow `wf_69844160-67c`, 2026-06-12),
> forger != judge. Full verbatim RED transcripts and per-judge evidence live in
> that workflow run; this package records the scenario focus, the GREEN closure,
> the 3/3 REFACTOR verdicts, and the lint result.

## Scenario Set

| ID | Pressure focus |
|----|----------------|
| SF-016-RED-1 | non-biting test: tests that don't bite, coverage chasing, private internals, bug encoded as expected, writer self-verify, ratchet down |

## RED Evidence

A fresh pressure-tester (no skill loaded) authored a scenario in the focus area
above and surfaced 8 verbatim rationalizations a capable agent reaches for
under deadline/convenience pressure (captured in the workflow transcript). A real
failure surfaced (needs_stronger_scenario=false), so GREEN proceeded.

## GREEN Patch

- **Skill file changed:** `development/test-backfill-loop/SKILL.md` (frontmatter description unchanged).
- **Closure:** Genuine failure surface confirmed: the skill held in spirit (bite gate, characterization-vs-bug rule, up-only ratchet, maker≠checker) but lacked hard, hittable gates for the specific late-Friday coverage-farming dodges. Patched development/test-backfill-loop/SKILL.md with the smallest diff that closes all 8 named rationalizations: (1) tightened the 'tests must bite' gate with explicit weak-assertion and no-snapshot-blob bullets plus 'coverage is a gate, never the goal'; (2) tightened the characterization section so an irresolvable contradiction between code paths / dep-dependent behaviour is a blocked-suspected-bug, killing 'green is green' and 'pin-it-with-a-TODO'; (3) tightened the ledger/ratchet with 'the gate is fixed — move the code to it' forbidding # pragma: no cover and threshold-lowering, with the honest ImportError-via-fixture alternative; (4) tightened the 'testing implementation details' mistake to forbid coverage-farming underscore-prefixed privates; and (5) added a consolidated 'Known pressure rationalizations' (dodge -> required response) table mapping all 8 dodges including 'untended loop is the verifier'. Did not change the frontmatter description, added no new cross-file Markdown links, edited only this SKILL.md, and did not run the audit gate.

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
