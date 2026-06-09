# AGENTS.md -- default safety rules for the skill-jar loops

> Host-neutral safety rules every agent in this repo's loops (jar-audit and
> bug-pipeline) obeys, every cycle. These are the floor; per-loop additions go
> in agent-state/loop-state.md (Current Rules). Full annotated version +
> per-host gate wiring: loop-engineer/references/safety-and-gates.md.

## General
- Do exactly one narrow task per cycle. No scope creep beyond the planned task.
- The agent that wrote a change is NEVER the only agent that verifies it
  (maker != checker). The checker is separate and adversarial, and may reject.
- When a change is expensive to reverse (public API, schema, on-disk format,
  cross-module deletion) or intent is ambiguous: STOP and write a row to the
  blocked/decisions state, then continue other work. Do not guess.

## Code Changes
- Smallest diff that satisfies the task. No drive-by renames, reformatting, or
  restructuring of untouched code.
- Touch only files the task names. Changing unrelated files fails the gate.
- Work in an isolated worktree/branch -- one task per worktree per branch.
- Never add secrets, tokens, or credentials to the repo.

## Verification
- THE gate for this repo: `python scripts/audit-jar.py` -- it must exit 0
  before any task is marked complete.
- Every gate is a runnable command that exits 0 (pass) or non-zero (fail).
  "Looks good" is not a gate.
- Never weaken, skip, delete, or loosen a gate check to make it pass. A
  genuinely-wrong audit check is a logged, justified human-decision item --
  not a silent edit to scripts/audit-jar.py.
- The verification suite must actually run and report a real result. An
  empty, missing, or erroring suite is a STOP-and-report, never a pass.

## State
- Update agent-state/ BEFORE committing. Commit code and state TOGETHER in one
  commit so a restart never sees committed-but-unrecorded work.
- Record every failed attempt in agent-state/failed-attempts.md. Do not delete
  rows from it.
- Bug-pipeline findings live in agent-state/BUG_TRACKER.md (statuses:
  pending -> fixed -> verified, or reopened); jar-audit findings live in
  agent-state/triage-inbox.md. Do not cross-file them.
- Commit locally only. Never push to the remote -- pushing is the human's call.
- The human owns architecture, merge decisions, security boundaries, and cost.
  The loop discovers, drafts, tests, and summarizes; the human decides what ships.
