# Forge Run: plan-prune

> Forged in the `skill-forge-queue` batch (workflow `wf_69844160-67c`, 2026-06-12),
> forger != judge. Full verbatim RED transcripts and per-judge evidence live in
> that workflow run; this package records the scenario focus, the GREEN closure,
> the 3/3 REFACTOR verdicts, and the lint result.

## Scenario Set

| ID | Pressure focus |
|----|----------------|
| SF-012-RED-1 | stale-plan consolidation: deleting docs without representing claims or git holding them, no live grounding, architecture redesign, no executed verification |

## RED Evidence

A fresh pressure-tester (no skill loaded) authored a scenario in the focus area
above and surfaced 7 verbatim rationalizations a capable agent reaches for
under deadline/convenience pressure (captured in the workflow transcript). A real
failure surfaced (needs_stronger_scenario=false), so GREEN proceeded.

## GREEN Patch

- **Skill file changed:** `development/plan-prune/SKILL.md` (frontmatter description unchanged).
- **Closure:** Patched development/plan-prune/SKILL.md to explicitly close all 7 named rationalizations. Added two hard-gate paragraphs to the Operating Contract (a loose human grant authorizes running the process, not skipping it; 'you are a reconciler, not an architect' — open approach disagreements are conflict blocked decisions) plus a new 'Known Pressure Rationalizations' table (dodge -> required response) covering all seven. Also tightened two soft process rules into hittable gates: Step 3 now bars marking done from a doc's self-reported header/absent-TODO and makes verification mandatory while allowing cheap evidence instead of the slow full suite; Step 7 now requires reading-before-folding and folding-before-retiring, forbids 'see git history' as a substitute for consolidation, and requires blocking retirement when the time budget runs out rather than deleting from a skim. Smallest-diff: +23/-1 lines, no frontmatter description change, no new cross-file links, audit gate not run (concurrent forgers; orchestrator runs it once at end).

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
