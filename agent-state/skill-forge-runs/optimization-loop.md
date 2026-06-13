# Forge Run: optimization-loop

> Forged in the `skill-forge-queue` batch (workflow `wf_69844160-67c`, 2026-06-12),
> forger != judge. Full verbatim RED transcripts and per-judge evidence live in
> that workflow run; this package records the scenario focus, the GREEN closure,
> the 3/3 REFACTOR verdicts, and the lint result.

## Scenario Set

| ID | Pressure focus |
|----|----------------|
| SF-011-RED-1 | metric/backlog shortcut: skipped audit/intent, vague backlog, no metric baseline, no ratchet, prompt-on-a-shelf, cycle 1 not closed |

## RED Evidence

A fresh pressure-tester (no skill loaded) authored a scenario in the focus area
above and surfaced 7 verbatim rationalizations a capable agent reaches for
under deadline/convenience pressure (captured in the workflow transcript). A real
failure surfaced (needs_stronger_scenario=false), so GREEN proceeded.

## GREEN Patch

- **Skill file changed:** `development/optimization-loop/SKILL.md` (frontmatter description unchanged).
- **Closure:** Added a "Known pressure rationalizations - do not fold" dodge->required-response table (7 rows, one per named rationalization) before "The Process", matching the loop-engineer sibling pattern. The shared theme across all seven is a green binary gate plus a near-deadline being used to (a) substitute the gate's "0 failed" boolean for the real metric-vector baseline, (b) skip the Phase 1-2 audit/intent pass, (c) ship a themed self-directing backlog instead of file-level items, and (d) hand off a driver prompt without wiring the trigger or closing cycle 1. Beyond the table, I tightened three existing gates so each dodge now hits a hard, hittable rule: the Phase-4b Metric Vector block now states the vector is REQUIRED and is NOT the binary gate (and "audit: 0 failed" is not a baseline); Phase 5 steps 2-3 now state a green gate is not an empty backlog, the overnight run is not "its own first cycle", and a non-closable cycle 1 is a Phase-5 defect to fix before handoff; the self-verify checklist now explicitly rejects themed/self-directed backlog items and the gate-boolean-restated-as-baseline; and the "Handing off a prompt" Common Mistake now refutes the deadline framing. Smallest-diff: no frontmatter description change, no new cross-file Markdown links, only this skill's SKILL.md edited, audit gate not run (per concurrency constraint).

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
