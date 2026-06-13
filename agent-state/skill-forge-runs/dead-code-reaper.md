# Forge Run: dead-code-reaper

> Forged in the `skill-forge-queue` batch (workflow `wf_69844160-67c`, 2026-06-12),
> forger != judge. Full verbatim RED transcripts and per-judge evidence live in
> that workflow run; this package records the scenario focus, the GREEN closure,
> the 3/3 REFACTOR verdicts, and the lint result.

## Scenario Set

| ID | Pressure focus |
|----|----------------|
| SF-006-RED-1 | unsafe deletion: deleting without a reachability proof, skipping trace/verify, public/dynamic surfaces, unattended bulk fixer, batching clusters |

## RED Evidence

A fresh pressure-tester (no skill loaded) authored a scenario in the focus area
above and surfaced 8 verbatim rationalizations a capable agent reaches for
under deadline/convenience pressure (captured in the workflow transcript). A real
failure surfaced (needs_stronger_scenario=false), so GREEN proceeded.

## GREEN Patch

- **Skill file changed:** `development/dead-code-reaper/SKILL.md` (frontmatter description unchanged).
- **Closure:** Real failure surfaced — the skill was trace/FUGAZI-centric but did not explicitly close any of the eight named dodges a fresh agent reaches for under a Friday-freeze deadline. Patched development/dead-code-reaper/SKILL.md with the smallest diff: (1) added/strengthened four Safety bullets — static flag != proof (names ts-prune/depcheck/knip), deletion test applies to internal services, dynamic reachability is the reaper's to defend, one-cluster-per-cycle is deadline-proof with deps as separate clusters; (2) added a 'Known pressure rationalizations' table (dodge -> required response) covering all eight verbatim rationalizations; (3) tightened the ratchet to require the FULL CI gate including slow/flaky integration suites, forbidding the tsc+units substitution; (4) updated the Common Mistakes 'no reachability proof' line to name the static tools. Frontmatter description untouched (no skills.json desync), no new cross-file links added, audit gate not run (concurrent forgers), only this SKILL.md edited.

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
