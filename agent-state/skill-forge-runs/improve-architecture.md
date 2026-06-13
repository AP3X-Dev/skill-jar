# Forge Run: improve-architecture

> Forged in the `skill-forge-queue` batch (workflow `wf_69844160-67c`, 2026-06-12),
> forger != judge. Full verbatim RED transcripts and per-judge evidence live in
> that workflow run; this package records the scenario focus, the GREEN closure,
> the 3/3 REFACTOR verdicts, and the lint result.

## Scenario Set

| ID | Pressure focus |
|----|----------------|
| SF-009-RED-1 | shallow refactor: rename/move called a deepening, AI choosing direction, skipped depth-check, ADR/CONTEXT not updated, autonomous instead of human-in-the-loop |

## RED Evidence

A fresh pressure-tester (no skill loaded) authored a scenario in the focus area
above and surfaced 7 verbatim rationalizations a capable agent reaches for
under deadline/convenience pressure (captured in the workflow transcript). A real
failure surfaced (needs_stronger_scenario=false), so GREEN proceeded.

## GREEN Patch

- **Skill file changed:** `development/improve-architecture/SKILL.md` (frontmatter description unchanged).
- **Closure:** Real failures surfaced; the skill had the right principles but not hard, hittable gates against deadline/absent-lead dodges. Added a 'Known pressure rationalizations' table (7 rows, one per named dodge -> required response) right under the Operating Contract, and tightened three existing rules so the dodges can't slip past: (1) the Human-in-the-loop contract now explicitly states that 'I trust your judgment'/'no design ceremony'/'just ship something better' is tactical authorization only and that autonomous-and-green is a failure, not a win — stop at the migration gate if the decider is absent; (2) the Ship depth check is now a written gate (name before/after interface, apply deletion test per module) that fails topic-splits-through-the-same-surface AND any barrel re-export by construction; (3) the migration's behaviour-preserving rule now bars opportunistic behaviour changes (backoff/retry/rounding) and requires re-reading the governing ADR (e.g. ADR-0007) before touching that code. Frontmatter description untouched (no skills.json desync); no new cross-file links; audit gate not run (concurrent forgers).

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
