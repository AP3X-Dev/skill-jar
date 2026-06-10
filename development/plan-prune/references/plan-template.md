# Canonical Plan Template

Use this template when running [plan-prune](../SKILL.md). Adapt headings to the repo's convention, but keep every section represented.

## Canonical plan

```md
# Project Plan: <project>

Last reconciled: <YYYY-MM-DD>
Canonical plan path: <path>
Current commit: <sha>
Current branch: <branch>

## Current Objective
<one paragraph: what the project is trying to become now>

## Current Development State
- **Verified complete:** <features/areas backed by evidence>
- **Implemented but unverified:** <present in code, not proven>
- **Planned but not built:** <valid remaining work>
- **Changed from older plan:** <intent drift or accepted replacement>
- **Blocked:** <decisions, credentials, environments, expensive-to-reverse choices>

## Verification Evidence
| Check | Command / evidence | Result | Notes |
|-------|--------------------|--------|-------|
| Git state | `git status --short --branch` | <result> | <notes> |
| Recent history | `git log --oneline -10` | <summary> | <notes> |
| Tests/build/gate | <command> | <exit/result> | <notes> |

## Source Inventory
| Source | Type | Claims | Freshness signal | Disposition |
|--------|------|--------|------------------|-------------|
| <path> | roadmap/spec/prp/handoff/state | <current/next/done/blocked claims> | <commit/date> | canonical/supporting/superseded/archived/blocked |

## Reconciled Work Plan
| ID | Priority | Work item | Status | Evidence | Acceptance |
|----|----------|-----------|--------|----------|------------|
| P1 | Now | <task> | planned-not-built | <source paths + current-state evidence> | <runnable check or observable outcome> |

## Now
<the smallest coherent set of next actions>

## Next
<sequenced work after Now is complete>

## Later
<deferred work with reason>

## Verified Complete - Do Not Rework
| Item | Evidence | Source docs updated |
|------|----------|---------------------|

## Blocked Decisions
| ID | Question | Why blocked | Options | Owner |
|----|----------|-------------|---------|-------|

## Superseded Planning Docs
| Original path | Action taken | New path / removal evidence | Reason |
|---------------|--------------|-----------------------------|--------|

## Remaining Active Planning Surface
| Path | Why it remains active |
|------|-----------------------|

## Freshness Rules
- Update this file whenever planning scope changes, a milestone completes, or a restart/handoff doc is written.
- New planning docs must either update this file or explicitly declare themselves supporting references.
- Stale planning docs must be deleted, archived, or replaced by a tiny pointer stub.
```

## Pointer stub

Use this only when an old path must stay because links or project conventions depend on it:

```md
# Superseded

This planning document was consolidated into `<canonical-plan-path>` on <YYYY-MM-DD>.
Use that file as the current plan.
```

## Source inventory checklist

- README and project overview docs.
- `docs/**` plans, specs, PRPs, roadmaps, ADRs, handoffs, runbooks, status docs.
- `agent-state/**` completed, failed-attempts, trackers, triage inboxes.
- `.github/**` issue templates, workflows, release checklists.
- Recent commits and branch names that imply scope.
- Inline TODO/FIXME comments only when they represent planned work, not incidental cleanup.

## Disposition rules

| Disposition | Use when |
|---|---|
| `canonical` | This is the one current plan file. |
| `supporting` | Durable design detail remains useful but is not the plan. |
| `deleted` | The fragment was folded into the canonical plan and git history is enough. |
| `archived` | Historical detail remains useful but should not sit in the active planning surface. |
| `stubbed` | The old path must stay to preserve links; it contains only a pointer to the canonical plan. |
| `blocked` | The source raises a conflict that needs human direction. |

Every source gets exactly one disposition.
