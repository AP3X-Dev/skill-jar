# Architecture guardrail state -- __PROJECT__

## Objective

Discover and install only human-approved architecture rules, prove each rule
with adversarial fixtures, then hand the accepted pack to arch-drift-watch.

## Autonomy

Level 1 -- read-only discovery. Record the human decision that authorizes any
promotion before changing this level.

## Base

- Source commit: pending
- Worktree/branch: pending
- Existing repository gates: pending
- Canonical verifier: `python scripts/architecture/verify.py`
- Drift source mode: `guardrail-pack`
- Drift adapter: `python scripts/architecture/watch_guardrail.py`

## In-flight packet

None.

## Approved rules ready for installation

None.

## Next action

Run read-only discovery and populate `.architecture/evidence.md`; do not install
blocking rules until the architecture owner approves exact statements and scope.
