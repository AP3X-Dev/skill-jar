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
| SF-004 | bug-pipeline | development | `development/bug-pipeline/SKILL.md` | forged | 3/3 | hunter/fixer/validator shortcut pressure | `agent-state/skill-forge-runs/bug-pipeline.md` | complete |
| SF-005 | clean-room | development | `development/clean-room/SKILL.md` | forged | 3/3 | firewall and parity-mode pressure | `agent-state/skill-forge-runs/clean-room.md` | complete |
| SF-006 | dead-code-reaper | development | `development/dead-code-reaper/SKILL.md` | forged | 3/3 | unsafe deletion pressure | `agent-state/skill-forge-runs/dead-code-reaper.md` | complete |
| SF-007 | design-panel | development | `development/design-panel/SKILL.md` | forged | 3/3 | single-design shortcut pressure | `agent-state/skill-forge-runs/design-panel.md` | complete |
| SF-008 | diagnose-loop | development | `development/diagnose-loop/SKILL.md` | forged | 3/3 | premature fix pressure | `agent-state/skill-forge-runs/diagnose-loop.md` | complete |
| SF-009 | improve-architecture | development | `development/improve-architecture/SKILL.md` | forged | 3/3 | shallow refactor pressure | `agent-state/skill-forge-runs/improve-architecture.md` | complete |
| SF-010 | loop-engineer | development | `development/loop-engineer/SKILL.md` | forged | 3/3 | vague-loop autonomy pressure | `agent-state/skill-forge-runs/loop-engineer.md` | complete |
| SF-011 | optimization-loop | development | `development/optimization-loop/SKILL.md` | forged | 3/3 | metric and backlog shortcut pressure | `agent-state/skill-forge-runs/optimization-loop.md` | complete |
| SF-012 | plan-prune | development | `development/plan-prune/SKILL.md` | forged | 3/3 | stale-plan consolidation pressure | `agent-state/skill-forge-runs/plan-prune.md` | complete |
| SF-013 | review-panel | development | `development/review-panel/SKILL.md` | forged | 3/3 | unverified finding pressure | `agent-state/skill-forge-runs/review-panel.md` | complete |
| SF-014 | skill-forge | development | `development/skill-forge/SKILL.md` | forged | 3/3 | self-forging rationalization pressure | `agent-state/skill-forge-runs/skill-forge.md` | complete |
| SF-015 | sprint-ticket-runner | development | `development/sprint-ticket-runner/SKILL.md` | forged | 3/3 | parallelism and sprint-drift pressure | `agent-state/skill-forge-runs/sprint-ticket-runner.md` | complete |
| SF-016 | test-backfill-loop | development | `development/test-backfill-loop/SKILL.md` | forged | 3/3 | non-biting test pressure | `agent-state/skill-forge-runs/test-backfill-loop.md` | complete |
| SF-017 | api-design | systems-design | `systems-design/api-design/SKILL.md` | forged | 3/3 | protocol and idempotency shortcut pressure | `agent-state/skill-forge-runs/api-design.md` | complete |
| SF-018 | data-store-selection | systems-design | `systems-design/data-store-selection/SKILL.md` | forged | 3/3 | brand-choice and shard-key pressure | `agent-state/skill-forge-runs/data-store-selection.md` | complete |
| SF-019 | design-system | systems-design | `systems-design/design-system/SKILL.md` | forged | 3/3 | premature complexity pressure | `agent-state/skill-forge-runs/design-system.md` | complete |
| SF-020 | production-readiness | systems-design | `systems-design/production-readiness/SKILL.md` | forged | 3/3 | launch-without-drill pressure | `agent-state/skill-forge-runs/production-readiness.md` | complete |
| SF-021 | unit-test-quality | development | `development/unit-test-quality/SKILL.md` | forged | 3/3 | AI slop tests, weak assertions, and coverage-metric pressure | `agent-state/skill-forge-runs/unit-test-quality.md` | complete |
| SF-022 | add-to-jar | development | `development/add-to-jar/SKILL.md` | forged | 3/3 | drop-in skill pressure | `agent-state/skill-forge-runs/add-to-jar.md` | complete |
| SF-023 | instrument-observability | development | `development/instrument-observability/SKILL.md` | forged | 3/3 | observability shortcut pressure | `agent-state/skill-forge-runs/instrument-observability.md` | complete |

## Run Package Rules

- Store per-skill evidence at `agent-state/skill-forge-runs/<skill-name>.md`.
- A row cannot move to `patched` without a RED rationalization recorded
  verbatim.
- A row cannot move to `forged` without 3/3 clean judge runs and
  `python scripts/audit-jar.py` exiting 0.
- If a public skill contract change is required, mark `blocked` and write the
  decision row before editing.
| SF-024 | simplify-loop | development | `development/simplify-loop/SKILL.md` | pending-red | 0/3 | drop-in skill pressure | - | RED scenario |
| SF-025 | spec-driven-change | development | `development/spec-driven-change/SKILL.md` | pending-red | 0/3 | drop-in skill pressure | - | RED scenario |
| SF-026 | rebuild-panel | development | `development/rebuild-panel/SKILL.md` | pending-red | 0/3 | drop-in skill pressure | - | RED scenario |
