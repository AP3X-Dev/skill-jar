# Skill Forge Tracker -- skill-jar

Durable queue for running the jar's own `skill-forge` loop across every skill.
One cycle advances one row by one stage. Do not delete rows; if a skill is
removed or renamed, mark the row `blocked` and record the decision in
`agent-state/decisions.md`.

## Status Values

| Status | Meaning |
|---|---|
| `pending-red` | No failing pressure run has been captured yet. |
| `needs-stronger-scenario` | RED did not expose a realistic failure; improve the pressure. |
| `red-captured` | RED captured a shortcut/rationalization; GREEN patch is next. |
| `patched` | The skill was patched; judge runs are next. |
| `refactor-clean-N` | N clean judge runs have passed; continue until 3. |
| `forged` | RED evidence exists, 3/3 judge runs are clean, and the audit gate passed. |
| `reopened` | A forged or patched skill failed a new judge/pressure/lint pass. |
| `blocked` | Human decision required before the loop can continue this skill. |

## Queue

| ID | Skill | Category | Path | Status | Clean Runs | Pressure Focus | Last Evidence | Next Action |
|----|-------|----------|------|--------|------------|----------------|---------------|-------------|
| SF-001 | arch-drift-watch | development | `development/arch-drift-watch/SKILL.md` | forged | 3/3 | scheduled drift triage pressure | `agent-state/skill-forge-runs/arch-drift-watch.md` | complete |
| SF-002 | auto-research | development | `development/auto-research/SKILL.md` | forged | 3/3 | fixed-budget experiment shortcut pressure | `agent-state/skill-forge-runs/auto-research.md` | complete |
| SF-003 | autonomous-advisor | development | `development/autonomous-advisor/SKILL.md` | forged | 3/3 | hands-off PRP guardrail pressure | `agent-state/skill-forge-runs/autonomous-advisor.md` | complete |
| SF-004 | bug-pipeline | development | `development/bug-pipeline/SKILL.md` | pending-red | 0/3 | hunter/fixer/validator shortcut pressure | - | RED scenario |
| SF-005 | clean-room | development | `development/clean-room/SKILL.md` | pending-red | 0/3 | firewall and parity-mode pressure | - | RED scenario |
| SF-006 | dead-code-reaper | development | `development/dead-code-reaper/SKILL.md` | pending-red | 0/3 | unsafe deletion pressure | - | RED scenario |
| SF-007 | design-panel | development | `development/design-panel/SKILL.md` | pending-red | 0/3 | single-design shortcut pressure | - | RED scenario |
| SF-008 | diagnose-loop | development | `development/diagnose-loop/SKILL.md` | pending-red | 0/3 | premature fix pressure | - | RED scenario |
| SF-009 | improve-architecture | development | `development/improve-architecture/SKILL.md` | pending-red | 0/3 | shallow refactor pressure | - | RED scenario |
| SF-010 | loop-engineer | development | `development/loop-engineer/SKILL.md` | pending-red | 0/3 | vague-loop autonomy pressure | - | RED scenario |
| SF-011 | optimization-loop | development | `development/optimization-loop/SKILL.md` | pending-red | 0/3 | metric and backlog shortcut pressure | - | RED scenario |
| SF-012 | plan-prune | development | `development/plan-prune/SKILL.md` | pending-red | 0/3 | stale-plan consolidation pressure | - | RED scenario |
| SF-013 | review-panel | development | `development/review-panel/SKILL.md` | pending-red | 0/3 | unverified finding pressure | - | RED scenario |
| SF-014 | skill-forge | development | `development/skill-forge/SKILL.md` | pending-red | 0/3 | self-forging rationalization pressure | - | RED scenario |
| SF-015 | sprint-ticket-runner | development | `development/sprint-ticket-runner/SKILL.md` | pending-red | 0/3 | parallelism and sprint-drift pressure | - | RED scenario |
| SF-016 | test-backfill-loop | development | `development/test-backfill-loop/SKILL.md` | pending-red | 0/3 | non-biting test pressure | - | RED scenario |
| SF-017 | api-design | systems-design | `systems-design/api-design/SKILL.md` | pending-red | 0/3 | protocol and idempotency shortcut pressure | - | RED scenario |
| SF-018 | data-store-selection | systems-design | `systems-design/data-store-selection/SKILL.md` | pending-red | 0/3 | brand-choice and shard-key pressure | - | RED scenario |
| SF-019 | design-system | systems-design | `systems-design/design-system/SKILL.md` | pending-red | 0/3 | premature complexity pressure | - | RED scenario |
| SF-020 | production-readiness | systems-design | `systems-design/production-readiness/SKILL.md` | pending-red | 0/3 | launch-without-drill pressure | - | RED scenario |

## Run Package Rules

- Store per-skill evidence at `agent-state/skill-forge-runs/<skill-name>.md`.
- A row cannot move to `patched` without a RED rationalization recorded
  verbatim.
- A row cannot move to `forged` without 3/3 clean judge runs and
  `python scripts/audit-jar.py` exiting 0.
- If a public skill contract change is required, mark `blocked` and write the
  decision row before editing.
