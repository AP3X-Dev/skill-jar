# Parallelism Audit

Use this whenever the sprint runner needs to decide what can run at the same
time. The output is `agent-state/sprint/parallelism-map.md`.

## Inputs

- Current sprint tickets or backlog items.
- Source PRP/PRD/plan snippets for each item.
- Repo entry points and module boundaries.
- Known gates and their cost.
- Current git status and active worktrees.
- Failed attempts and blocked decisions.

## Audit Steps

1. Dispatch read-only scoping per item. Each scoper may read files and run
   non-mutating discovery commands, but it must not edit, install, format,
   commit, or change state.
2. For each item, estimate:
   - likely files touched,
   - shared hot files,
   - required gates,
   - dependencies on other items,
   - whether it changes API, schema, config, persistence, auth, or shared state,
   - whether it needs the same verifier, environment, credential, port, fixture,
     data set, or external service.
3. Build a conflict graph where nodes are tickets and edges explain why two
   tickets cannot run in parallel.
4. Classify tickets into lanes.
5. Record confidence and invalidation triggers for every lane decision.

## Conflict Edges

Create an edge when two tickets share any of these:

- Same predicted write file, generated file, migration, lockfile, or snapshot.
- Same hot hub such as server bootstrap, router registry, schema root, shared
  config loader, global test fixture, or package boundary.
- Parent-child dependency: one ticket must define an interface before another
  can consume it.
- Shared external resource: port, database, account, credential, third-party
  quota, or stateful local service.
- Same expensive verifier bottleneck where concurrent runs would corrupt
  evidence or exhaust resources.
- API/schema/config/on-disk format change that makes downstream write sets
  uncertain.

No edge is needed for read-only scoping unless the scoping command itself uses a
scarce external resource.

## Lanes

| Lane | Meaning | Launch Rule |
|---|---|---|
| `parallel-scope` | Read-only investigation is safe. | Dispatch scopers only; no code writes. |
| `parallel-build` | Implementation appears disjoint. | One worktree and branch per ticket. |
| `batch-verify` | Tickets can share one expensive final gate after individual checks. | Run focused gates per ticket, then one full gate after the batch. |
| `serial` | Ordering is required. | Finish and verify the earlier ticket before starting the next. |
| `blocked` | Needs human decision or missing gate/resource. | Do not launch until resolved. |

## Confidence

- `high`: exact files are known, no shared hubs, no shared external resources,
  focused gates exist, and source intent is clear.
- `medium`: likely disjoint but predicted files are partial or one integration
  point is uncertain.
- `low`: predicted write set is broad, source intent is ambiguous, or a shared
  boundary may be touched.

Only `medium` or `high` tickets can enter `parallel-build`. Low-confidence items
can still enter `parallel-scope`.

## Invalidation Triggers

Refresh the parallelism map before launching more work if any active ticket:

- touches a file outside its predicted write set,
- changes a schema, migration, API contract, config contract, lockfile, generated
  artifact, or on-disk format,
- adds a new dependency,
- moves from focused tests to full-suite-only verification,
- consumes a shared external resource not listed in the map,
- discovers that source intent conflicts with another ticket.

## parallelism-map.md Template

```md
# Parallelism Map

## Summary
| Lane | Tickets | Confidence | Notes |
|---|---|---|---|
| parallel-scope | SPR-001, SPR-002 | high | read-only scoping |
| parallel-build | SPR-003, SPR-004 | medium | disjoint worktrees required |
| batch-verify | SPR-003, SPR-004 | medium | one full gate after focused gates |
| serial | SPR-005 -> SPR-006 | high | shared bootstrap file |
| blocked | SPR-007 | high | human decision needed |

## Conflict Graph
| A | B | Edge Type | Reason |
|---|---|---|---|
| SPR-005 | SPR-006 | hot-file | both likely touch apps/api/src/server.ts |

## Ticket Classifications
| Ticket | Lane | Confidence | Predicted Write Set | Gates | Invalidation |
|---|---|---|---|---|---|
| SPR-003 | parallel-build | medium | apps/worker/** | pnpm test worker | touches apps/api/src/server.ts |

## Launch Plan
1. Run parallel-scope scopers for <IDs>.
2. Start parallel-build worktrees for <IDs>.
3. Keep <IDs> serial until <dependency> lands.
4. Run <full gate> once after the compatible batch.

## Last Refreshed
- Date:
- Commit:
- Scopers:
```

## Example

| Item | Lane | Reason |
|---|---|---|
| M3.5 API bootstrap | serial | touches `apps/api/src/server.ts`, a hot hub |
| M4.4 API route wiring | serial | same hot hub as M3.5 |
| M3.4 worker | parallel-build | disjoint worker subsystem |
| M5.2 portal sales tracker | parallel-build | separate portal surface |
| next-item research | parallel-scope | read-only scoping only |
| full `pnpm verify` | batch-verify | fixed expensive gate after compatible batch |
