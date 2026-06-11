# Sprint Ticket Schema

Use these templates for `agent-state/sprint/`. Keep them short enough that a
fresh agent can read them at the start of every cycle.

## board.md

```md
# Sprint Board

## Objective
<one paragraph: what this sprint is trying to finish>

## Sources
| Source | Path / URL | Role | Freshness |
|---|---|---|---|
| <PRP / PRD / plan> | <path> | intent / feature / constraint | <date or commit> |

## Status Counts
| Status | Count |
|---|---:|
| backlog | 0 |
| scoped | 0 |
| ready | 0 |
| in-progress | 0 |
| review | 0 |
| verified | 0 |
| done | 0 |
| blocked | 0 |
| reopened | 0 |

## Active Lanes
| Lane | Tickets | Rule |
|---|---|---|
| serial | <IDs> | <why serialized> |
| parallel-build | <IDs> | <why disjoint> |
| parallel-scope | <IDs> | <read-only only> |
| batch-verify | <IDs> | <shared gate> |
| blocked | <IDs> | <decision/resource> |

## Next Action
<exact action a cold-start agent should take next>
```

## tickets/SPR-001.md

```md
# SPR-001: <title>

## Status
- Status: backlog | scoped | ready | in-progress | review | verified | done | blocked | reopened
- Priority: P0 | P1 | P2 | P3
- Source: <path / URL / user request>
- Owner: <maker agent or unassigned>
- Checker: <checker agent or unassigned>
- Branch/worktree: <name/path>

## Objective
<what changes when this ticket is done>

## Non-Goals
- <explicitly out of scope>

## Dependencies
| Kind | Item | Status |
|---|---|---|
| ticket | SPR-000 | blocked / done / n/a |
| decision | DEC-000 | open / resolved |

## Acceptance
Command:
<command that exits 0>

Expected evidence:
- <test count, route response, CLI output, screenshot path, etc.>

## Parallelism
- Lane: parallel-scope | parallel-build | batch-verify | serial | blocked
- Confidence: low | medium | high
- Predicted write set:
  - <file or glob>
- Hot files:
  - <shared file or module>
- Conflicts with:
  - <ticket ID and reason>
- Invalidates if:
  - <file/glob or behavior that forces lane refresh>

## Execution Notes
- Actual touched files:
  - <filled by maker>
- Gate results:
  - <command, exit, key output>
- Verifier result:
  - PASS | REJECT | NEEDS-DECISION
- Commit:
  - <sha or none>

## History
| Date | Actor | Event | Evidence |
|---|---|---|---|
| <date> | <agent> | created | <source> |
```

## decisions.md

```md
# Sprint Decisions

| ID | Ticket | Decision Needed | Options | Owner | Status | Resolution |
|---|---|---|---|---|---|---|
| DEC-001 | SPR-001 | <question> | <A/B/C> | human | open | |
```

## failed-attempts.md

```md
# Sprint Failed Attempts

| ID | Ticket | What Failed | Evidence | Do-Not-Retry Note |
|---|---|---|---|---|
| FA-001 | SPR-001 | <approach> | <command/diff/verdict> | <lesson> |
```

## handoff.md

```md
# Sprint Handoff

## Current State
<brief status summary>

## Next Action
<one concrete action for the next agent>

## Resume Checklist
- [ ] Read board.md.
- [ ] Read parallelism-map.md.
- [ ] Read in-progress/review/blocked tickets.
- [ ] Check git status and worktrees.
- [ ] Run or confirm the required gate before claiming progress.

## Last Verified Gate
| Command | Result | Date | Notes |
|---|---|---|---|
| <command> | pass/fail | <date> | <test count/key output> |
```
