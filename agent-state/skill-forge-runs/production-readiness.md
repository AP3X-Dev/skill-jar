# Forge Run: production-readiness

> Forged in the `skill-forge-queue` batch (workflow `wf_69844160-67c`, 2026-06-12),
> forger != judge. Full verbatim RED transcripts and per-judge evidence live in
> that workflow run; this package records the scenario focus, the GREEN closure,
> the 3/3 REFACTOR verdicts, and the lint result.

## Scenario Set

| ID | Pressure focus |
|----|----------------|
| SF-020-RED-1 | launch-without-drill: no executed drill or tested rollback, cause-metric alerts, PII/high-cardinality labels, TBD owners/routes, missing five runbooks |

## RED Evidence

A fresh pressure-tester (no skill loaded) authored a scenario in the focus area
above and surfaced 8 verbatim rationalizations a capable agent reaches for
under deadline/convenience pressure (captured in the workflow transcript). A real
failure surfaced (needs_stronger_scenario=false), so GREEN proceeded.

## GREEN Patch

- **Skill file changed:** `systems-design/production-readiness/SKILL.md` (frontmatter description unchanged).
- **Closure:** The pressure scenario surfaced 8 real dodges that the skill addressed only in spirit, so I patched systems-design/production-readiness/SKILL.md (note: the path is systems-design/, not development/systems-design/) with the smallest diff that turns each into a hard, hittable gate.

Two changes, both inside the "launch gate (runnable)" section, frontmatter description untouched and no new cross-file links:

1. Tightened 4 existing gate bullets so the dodges can't slip past: (a) alert routes must be symptom/SLO-based and "resource-utilization alerts do not satisfy this; they are dashboard panels" (closes dodge 3); (b) the five runbooks each need named first checks, named mitigations, and concrete rollback steps for THIS service, "a stub with 'investigate and roll back if needed' is not a runbook" (closes dodge 5); (c) rollback must be "executed against this service in a drill (reuse of a 'standard path' is an assumption until executed here)" (closes dodge 2); (d) drill must be run "for real, with the failure injected" and owner must be NAMED — "TBD/defaults to a channel is an empty box, not a green one" (closes dodges 1, 6). Added one prose line defining green: artifact exists + action ran, not "thought about" or footnoted-to-follow; checklist is the contract you sign (closes dodge 8).

2. Added a "Known pressure rationalizations" subsection: a one-row-per-dodge table (dodge -> required response) covering all 8, with a lead-in that a near-launch deadline manufactures these and each leaves the box red — meet the gate or report not ready; do not self-certify. The deadline-override dodge (7) is closed by directing the agent to state the verdict + smallest fix list and escalate the ship-with-gaps decision to the deadline owner rather than silently marking green.

No public-contract change was needed: the gate items and the ready/ready-after-fixes/not-ready verdict vocabulary already existed; I sharpened their definitions rather than altering the skill's interface. Did not run the audit gate (concurrent forgers).

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
