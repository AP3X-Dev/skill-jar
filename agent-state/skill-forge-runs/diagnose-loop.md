# Forge Run: diagnose-loop

> Forged in the `skill-forge-queue` batch (workflow `wf_69844160-67c`, 2026-06-12),
> forger != judge. Full verbatim RED transcripts and per-judge evidence live in
> that workflow run; this package records the scenario focus, the GREEN closure,
> the 3/3 REFACTOR verdicts, and the lint result.

## Scenario Set

| ID | Pressure focus |
|----|----------------|
| SF-008-RED-1 | premature fix: fixing before repro/minimize, multiple hypotheses at once, cause without boundary evidence, self-certified root cause, skipped regression test |

## RED Evidence

A fresh pressure-tester (no skill loaded) authored a scenario in the focus area
above and surfaced 8 verbatim rationalizations a capable agent reaches for
under deadline/convenience pressure (captured in the workflow transcript). A real
failure surfaced (needs_stronger_scenario=false), so GREEN proceeded.

## GREEN Patch

- **Skill file changed:** `development/diagnose-loop/SKILL.md` (frontmatter description unchanged).
- **Closure:** A real failure surfaced (the skill, run cold, would have let an agent ship an uninvestigated bundle of changes and call a dashboard drop "fixed"), so I patched diagnose-loop/SKILL.md with the smallest diff that turns each named dodge into a hittable gate. Added a "Known pressure rationalizations" table (8 rows, dodge -> required response) placed under Termination & escalation, where the authority-waiver and defer dodges belong. Tightened three existing rules into hard gates: (1) a new "One-change law" forbidding shotgun fixes and distinguishing mitigation from diagnosis (a labelled stopgap is allowed but never closes the incident); (2) a "traceback line is the crime scene, not the culprit" clause separating symptom location from root cause; (3) stage 1 (Reproduce) now states a prod traceback/dashboard is a symptom not a repro and "hard to repro" changes the kind of repro you build, not whether you need one; (4) stage 6 (Lock & fix) now states a post-deploy dashboard is monitoring not verification and cannot substitute for the regression test. No frontmatter description change (skills.json stays in sync); no new cross-file Markdown links (table references only same-file stages/laws); edited only this skill's SKILL.md; did not run the audit gate. All 8 named rationalizations are now explicitly closed.

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
