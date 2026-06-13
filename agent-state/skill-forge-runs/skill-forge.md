# Forge Run: skill-forge

> Forged in the `skill-forge-queue` batch (workflow `wf_69844160-67c`, 2026-06-12),
> forger != judge. Full verbatim RED transcripts and per-judge evidence live in
> that workflow run; this package records the scenario focus, the GREEN closure,
> the 3/3 REFACTOR verdicts, and the lint result.

## Scenario Set

| ID | Pressure focus |
|----|----------------|
| SF-014-RED-1 | self-forging rationalization: taste-only rewrite, forger judging itself, forged without K judge runs or gate, skipped RED, bloated description |

## RED Evidence

A fresh pressure-tester (no skill loaded) authored a scenario in the focus area
above and surfaced 7 verbatim rationalizations a capable agent reaches for
under deadline/convenience pressure (captured in the workflow transcript). A real
failure surfaced (needs_stronger_scenario=false), so GREEN proceeded.

## GREEN Patch

- **Skill file changed:** `development/skill-forge/SKILL.md` (frontmatter description unchanged).
- **Closure:** Real failure surfaced: the skill had the rules (Operating Contract, iron law, maker!=checker, K clean runs, LINT) but offered no explicit closure for the named carve-outs a forger uses to skip them on a "small/deadline" edit. Made the smallest body-only diff to development/skill-forge/SKILL.md closing all 7 named dodges. (1) Tightened the Operating Contract with a 'no small-change exemption' clause: a behavioural skill's words ARE its behaviour, so wording/trigger/rule edits get the full loop; 'RED N/A' declared an invalid rationale field (no captured RED = RED hasn't run); deadline is honoured by forging a smaller change, not stamping an unforged one. (2) Tightened the REFACTOR exit: K applies to every change, a flaky/slow harness never lowers K, one pass proves nothing. (3) Tightened the LINT exit: gate runs on every forge regardless of size, naming the skills.json-desync/trigger-bloat/broken-link risks a wording edit can introduce. (4) Tightened the description lint bullet: more trigger phrases widens the match surface and CAUSES mis-triggering; tighten + add 'NOT for' exclusions, prove via RED. (5) Added a 'Known pressure rationalizations' dodge->required-response table after the Operating Contract covering all 7, including maker-equals-checker-is-fine-when-small mapped to the structural maker!=checker rule. Constraints honoured: frontmatter description unchanged (792 chars, no skills.json desync); no new cross-file Markdown links; audit gate NOT run (left to orchestrator); only this skill's SKILL.md edited.

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
