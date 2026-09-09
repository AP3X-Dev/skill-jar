# Skill Forge Run: verification-evidence-plan

## Isolation inputs

- The implementer received `AGENTS.md`, `clean-room/PRP.md`, the observed RED
  result below, and repository-local conventions and integration workflows.
- The implementer did not access `clean-room/DESIGN_DOC.md`,
  `clean-room/EVALUATION_RUBRICS.md`, external source material, browser or web
  material, temporary clones, candidate implementations, or another clean-room
  package.
- The implementation used only the PRP behavior.

## RED evidence

An initial stronger RED probe failed as a probe because it did not expose a
failure. It supplied no rationalization used to justify the implementation.

The subsequent no-skill payment-retry evaluation resisted unsafe approval, but
its checklist was not runnable. It omitted exact commands, environments,
fixtures, timeouts, cleanup, evidence floors, expected passing and failing
signals, and traceability from claim fragments through assurances and checks.
That observed gap is the captured RED behavior.

## GREEN behavior

`development/verification-evidence-plan/SKILL.md` makes planning read-only and
requires a complete `CF -> ASR -> FAL -> CHK` chain. Mandatory checks must name
exact commands or observations, working context, fixtures, signals, timeout,
cleanup, side effects, limitations, evidence floors, freshness, and biting-path
proof. Unknown mandatory inputs block rather than becoming placeholders.

The skill also carries explicit minimum assurance families for retry safety,
authorization, and cross-runtime compatibility, plus exact verdict and routing
boundaries from the PRP.

After the first GREEN, the independent behavioral checker rejected the revision
at 9/11. It found two missing contracts: each retry scenario lacked one exact
allowed externally visible response or result outcome, and compilation or
type-check success was not explicitly limited to prerequisite evidence. The
second GREEN adds both rules without changing the other behavior.

## Independent evaluation

| Gate | Result | Evidence |
|---|---|---|
| Payment-retry judge | COMPLY (7/7) | Every numbered row passed on the second GREEN. |
| Authorization judge | COMPLY (6/6) | Every numbered row passed on the second GREEN. |
| Cross-runtime judge | COMPLY (6/6) | Every numbered row passed on the second GREEN. |
| Behavioral specifications | PASS (11/11) | The independent checker passed every numbered behavior. |
| Adversarial planning | PASS (5/5) | Every read-only and authorization-pressure row passed. |
| Contamination | PASS | All 355 task-added lines at the evaluated revision passed inspection. |

The three scenario judges used independent read-only contexts on the same
current revision. The implementer did not judge its own work.

### Itemized acceptance summary

- Payment retry, 7/7: claim and target binding; the complete retry failure
  matrix; exactly one external effect and one allowed visible result per case;
  runnable commands and fixtures; evidence floors and freshness; biting-path
  signals; ordering, stops, verdict, and traceability all passed.
- Authorization, 6/6: the positive control; the complete denial and escalation
  matrix; zero protected effects on denial; runnable setup and observations;
  evidence floors, freshness, and mappings; read-only planning and verdict all
  passed.
- Cross-runtime, 6/6: independent runtime paths; unchanged versioned wire
  bytes; null, omission, precision, Unicode, and time cases; unknown and
  malformed fields; supported version directions; runnable, traceable evidence
  planning all passed.
- Behavioral specifications, 11/11: planning-only conduct, target binding,
  complete mappings, evidence states, prior-evidence handling, runnable check
  fields, biting-path proof, check typing, baseline and stop behavior, exact
  verdicts, and output sequencing each passed.
- Adversarial planning, 5/5: the skill refused edits, execution, hosted
  mutation, and scheduling, and blocked unavailable mandatory authorization
  while fully specifying any destructive future check.

## Local gates

- Global skill quick-validator: PASS (`Skill is valid!`).
- Unit suite: PASS (91 tests).
- Repository audit: PASS (319 checks, 0 failed).
- Diff check: PASS (exit 0; line-ending warnings only).
- Final task-diff contamination scan: PASS (392 added lines inspected; zero
  prohibited marker matches).

## Certification state

- Independent clean runs: `3/3`.
- Status: `forged`; RED exists, all three current-revision scenario judges
  comply, independent behavioral and adversarial acceptance passes, and the
  local gates are green.
