# Forge Run: design-system

> Forged in the `skill-forge-queue` batch (workflow `wf_69844160-67c`, 2026-06-12),
> forger != judge. Full verbatim RED transcripts and per-judge evidence live in
> that workflow run; this package records the scenario focus, the GREEN closure,
> the 3/3 REFACTOR verdicts, and the lint result.

## Scenario Set

| ID | Pressure focus |
|----|----------------|
| SF-019-RED-1 | premature complexity: multi-region/mesh/sharding/polyglot with no requirement, skipped SLOs/capacity, survey/menu, components without owner/SLI/cost |

## RED Evidence

A fresh pressure-tester (no skill loaded) authored a scenario in the focus area
above and surfaced 7 verbatim rationalizations a capable agent reaches for
under deadline/convenience pressure (captured in the workflow transcript). A real
failure surfaced (needs_stronger_scenario=false), so GREEN proceeded.

## GREEN Patch

- **Skill file changed:** `systems-design/design-system/SKILL.md` (frontmatter description unchanged).
- **Closure:** Patched systems-design/design-system/SKILL.md to close all seven named pressure rationalizations with the smallest viable diff and no frontmatter/description change. Two edits: (1) tightened the Operating Contract so the SLO+capacity stage and stop conditions are non-waivable by the requester — deadline, "just a diagram/board deck," "keep it impressive," and "skip the boring ops stuff" are explicitly named as scoping pressures, not permission; banned the architecture-menu dodge ("commit to one topology"); and made owner/failure/cost a hard per-component gate ("no backfill owners later"). (2) Added an explicit "Known pressure rationalizations" table (dodge -> required response) covering all seven dodges verbatim, plus a paragraph tightening the stop-conditions gate: the named requirement must be a measured/projected workload number with a source, not an adjective — "impressive," "shows maturity," "built to scale," "investors love it," "richer diagram" are named as rejected justifications, and "over-provisioning architecture" is reframed as unowned operational surface rather than safety. No new cross-file links added; audit gate not run (concurrent edits); only this skill's SKILL.md edited.

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
