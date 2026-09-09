# Skill Forge Run: handoff-recovery

## RED evidence

The multi-worktree no-skill response provisionally selected the task-named
branch because it contained staged work before task-to-worktree identity was
bound. Its proposed commands retained unresolved worktree placeholders.

The stale-handoff response reached a cautious bounded conclusion, but represented
recovery as prose rather than a stable typed record. It did not provide complete
check input identity, explicit evidence/freshness/custody promotion rules, or
typed references tying the continuation to its proof. It also suggested broad
reflog, stash, and editor-history inspection without first bounding repository,
paths, time range, fields, permission, privacy, retention, cost, and stop rule.

Those observed omissions are the captured RED behavior. No additional failure
or unseen rationale is attributed to either evaluator.

### Raw evaluator custody

| Response | SHA-256 |
|---|---|
| RED stale handoff | `b7fd0988f162d14ae54b9dbe1cf52bc97d31fb783c6c1f3c0b226f776e04d309` |
| RED multi-worktree | `cd998813444001f2a1363dd8f21bf2c936d5efc4c37a72dc5c0cac2bc0094073` |
| Stale-handoff scenario judge | `e3a69b12c7465561ea47bcbb7787de0b61c70d1b4bd9cfabdbfe60430a9f3b7f` |
| Multi-worktree scenario judge | `b037bda3706180cc8092c6c8efabb168e1786c8459f936419e072d7c15a8c271` |
| Proof-boundary scenario judge | `6aa431a03aa1ecd480b931c9eb0b6f9691962428a3cfce633b28024e47b050c0` |
| Schema-promotion judge | `bf58bae44e3c0fc7606db93ae71d38ac7a9d6b2888ed10dd317c49d3f3a1c0c4` |
| Final acceptance | `e95baac967a54cf459afca65102cc984e31e3c2ffe4dd67daab9e282eaec861f` |

## GREEN behavior

`development/handoff-recovery/SKILL.md` defines a read-only recovery workflow
that binds the request before choosing a repository, inventories every relevant
worktree and Git operation, preserves and classifies all local changes, and
reconciles durable state with current source and checks.

The canonical `handoff-recovery/v1` record requires nine ordered tables, one
global ID namespace, typed resolved references, exact command and cwd, complete
check input identity, SHA-256/Git object bindings, proof boundaries, freshness
and weakest-link strength, custody overlap, material conflicts, decision gates,
and exactly one continuation. Explicit pressure defenses reject provisional
branch selection, placeholder commands, prose-only recovery, stale-gate
promotion, inferred change ownership, and unbounded sensitive-history reads.

## Independent evaluation

- Independent clean runs: `3/3` COMPLY.
- Stale handoff and dirty-tree judge: COMPLY.
- Multi-worktree and operation-state judge: COMPLY.
- Proof-boundary and completion judge: COMPLY.
- Schema and verdict-promotion check: COMPLY.
- Final acceptance: PASS (`16/16`).

## Local gates

- Global skill quick-validator: PASS (`Skill is valid!`).
- Unit suite: PASS (91 tests).
- Jar audit: PASS (334 checks, 0 failed).
- Diff check: PASS.
- Allowlist: PASS (11 changed paths, 0 violations).
- Contamination scan: PASS (0 prohibited identifier matches).
- Protected-input verification: PASS (9 files).

## Certification state

- Status: `forged`.
- Clean runs: `3/3`.
- Next action: human review and approval of the exact local commit message. Do
  not commit, merge, or push without that approval.
