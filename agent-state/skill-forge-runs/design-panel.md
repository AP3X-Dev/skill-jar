# Forge Run: design-panel

> Forged in the `skill-forge-queue` batch (workflow `wf_69844160-67c`, 2026-06-12),
> forger != judge. Full verbatim RED transcripts and per-judge evidence live in
> that workflow run; this package records the scenario focus, the GREEN closure,
> the 3/3 REFACTOR verdicts, and the lint result.

## Scenario Set

| ID | Pressure focus |
|----|----------------|
| SF-007-RED-1 | single-design shortcut: one design not two, skipping judge/skeptic, designer grading itself, spec before skeptic |

## RED Evidence

A fresh pressure-tester (no skill loaded) authored a scenario in the focus area
above and surfaced 7 verbatim rationalizations a capable agent reaches for
under deadline/convenience pressure (captured in the workflow transcript). A real
failure surfaced (needs_stronger_scenario=false), so GREEN proceeded.

## GREEN Patch

- **Skill file changed:** `development/design-panel/SKILL.md` (frontmatter description unchanged).
- **Closure:** Real failure surfaced: three of the seven dodges (keep-it-tight, existing-scaffolding, outsource-to-downstream-review) slipped past the skill entirely, and the others exploited ambiguity in steps 4/6 and the maker-checker rule. Patched with a minimal diff: (1) a 'four gates are non-negotiable' paragraph in the Operating Contract reframing deadline/brevity pressure as shrinking the artifact never the gates; (2) a 'Known pressure rationalizations' table mapping all seven named dodges to required responses; (3) tightened the Judge panel role row (independence is structural), step 4 (hunches and scaffolding don't collapse the design space; differentiate by shape), and step 6 (skeptic is a separate pre-spec pass, not folded into the spec or deferred to the review). Frontmatter description untouched; no new cross-file links; only this SKILL.md edited; audit gate not run per instructions.

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
