# Forge Run: review-panel

> Forged in the `skill-forge-queue` batch (workflow `wf_69844160-67c`, 2026-06-12),
> forger != judge. Full verbatim RED transcripts and per-judge evidence live in
> that workflow run; this package records the scenario focus, the GREEN closure,
> the 3/3 REFACTOR verdicts, and the lint result.

## Scenario Set

| ID | Pressure focus |
|----|----------------|
| SF-013-RED-1 | unverified finding: acting on unverified findings, performative agreement, single reviewer, no dedupe/severity, findings without a trigger |

## RED Evidence

A fresh pressure-tester (no skill loaded) authored a scenario in the focus area
above and surfaced 8 verbatim rationalizations a capable agent reaches for
under deadline/convenience pressure (captured in the workflow transcript). A real
failure surfaced (needs_stronger_scenario=false), so GREEN proceeded.

## GREEN Patch

- **Skill file changed:** `development/review-panel/SKILL.md` (frontmatter description unchanged).
- **Closure:** A real failure surfaced: the skill had strong verify-before-act discipline but never made it a hard, deadline-proof gate, so all eight dodges slipped through by presenting unverified pattern-matches at full confidence, faking the panel, skipping the objective gate, and issuing a merge verdict on invented blockers.

Patched development/review-panel/SKILL.md with three minimal, surgical additions (frontmatter description untouched; no new cross-file Markdown links):

1. Operating Contract — added a "Hard gates (a deadline does not waive these)" block with four rules: (a) No verification → no severity (unverified findings ship tagged "Unverified hypothesis", never Critical/Important/Minor; status leads each finding) — closes dodges 1, 2, 8; (b) The verdict rests only on verified findings (no blocking on unverified X/Y) — closes dodge 5; (c) The panel is real reviewers, not one reviewer in four hats (forged-panel ban) — closes dodge 3; (d) Run the objective gate before the verdict (the repo's gate, e.g. scripts/audit-jar.py, PRODUCES findings) — closes dodge 7.

2. Severity model — added an explicit "Unverified hypothesis" tier as the only pre-step-5 tier, reframed severity as decided by the step-5 trace (not subjective eyeballing) — closes dodge 6 — and added that a false positive is not harmless (costs a verification cycle, erodes trust) — closes dodge 4.

3. Added a "Known pressure rationalizations" table (dodge → required response) immediately above Common Mistakes, mapping all eight named rationalizations one-to-one to their non-negotiable rebuttal as a single hittable lookup.

scripts/audit-jar.py is referenced only as inline code (the repo's gate), not as a Markdown link.

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
