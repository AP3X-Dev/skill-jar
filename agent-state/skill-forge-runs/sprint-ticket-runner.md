# Forge Run: sprint-ticket-runner

> Forged in the `skill-forge-queue` batch (workflow `wf_69844160-67c`, 2026-06-12),
> forger != judge. Full verbatim RED transcripts and per-judge evidence live in
> that workflow run; this package records the scenario focus, the GREEN closure,
> the 3/3 REFACTOR verdicts, and the lint result.

## Scenario Set

| ID | Pressure focus |
|----|----------------|
| SF-015-RED-1 | parallelism/sprint-drift: parallel makers from intuition, map not invalidated, maker self-verify, auto-launch past the gate, spinning past stop |

## RED Evidence

A fresh pressure-tester (no skill loaded) authored a scenario in the focus area
above and surfaced 7 verbatim rationalizations a capable agent reaches for
under deadline/convenience pressure (captured in the workflow transcript). A real
failure surfaced (needs_stronger_scenario=false), so GREEN proceeded.

## GREEN Patch

- **Skill file changed:** `development/sprint-ticket-runner/SKILL.md` (frontmatter description unchanged).
- **Closure:** All 7 named pressure rationalizations were real dodges that slipped past the skill's softer phrasing, so I patched development/sprint-ticket-runner/SKILL.md with the smallest diff that turns each into a hard gate. Tightened the Operating Contract (maker!=checker is never an efficiency win; directory names are not an audit; no 'parallelize then fix conflicts later'), the launch gate (a vague 'run to completion' authorizes a budget, not a gate bypass or auto-launch; re-clear the gate on every map refresh), the stop condition (mid-sprint follow-ups are new backlog, not a reason to keep spinning; momentum is not approval), the verify step (a failure is REJECT until the checker proves flakiness with evidence; no re-run-to-green, no maker-declared green, no clean-compile green), and the invalidation note (no smallness exemption: a one-line still-compiling shared-file touch is exactly what triggers a map refresh). Added a consolidated 'Known Pressure Rationalizations' table (dodge -> required response) before Common Mistakes covering all seven. Did not change the frontmatter description, added no cross-file Markdown links, edited only this SKILL.md, and did not run the audit gate (orchestrator runs it once at the end).

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
