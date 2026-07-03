# Development Agent Packs

This folder contains generated, copy-ready sub-agent instructions for the
development skills.

The source of truth is `manifest.json`. Do not edit files under `claude/` or
`codex/` by hand. Regenerate them with:

```bash
python scripts/gen-agent-packs.py
```

The jar audit gate checks sync:

```bash
python scripts/gen-agent-packs.py --check
python scripts/audit-jar.py
```

## Layout

- `manifest.json` -- one host-neutral contract per role.
- `claude/*.md` -- generated Claude Code agents.
- `codex/*.toml` -- generated Codex agents.

## Install

Copy the generated files for your host into the target repo's runtime agent
directory:

```text
.claude/agents/<agent>.md
.codex/agents/<agent>.toml
```

Only install the roles the active skill needs. For example, a
`test-backfill-loop` instance usually needs `test-backfill-scout`,
`test-backfill-writer`, and `test-backfill-verifier`; a `review-panel` run may
dispatch only the lens agents for the risky surface under review.

## Roles

Every role below is defined in `manifest.json` and rendered to `claude/<role>.md`
and `codex/<role>.toml`. Grouped by the skill that owns them:

| Skill | Roles |
|---|---|
| `bug-pipeline` | `bug-pipeline-hunter`, `bug-pipeline-fixer`, `bug-pipeline-validator` |
| `dead-code-reaper` | `dead-code-reaper-scout`, `dead-code-reaper-reaper`, `dead-code-reaper-validator` |
| `test-backfill-loop` | `test-backfill-scout`, `test-backfill-writer`, `test-backfill-verifier` |
| `diagnose-loop` | `diagnose-investigator`, `diagnose-analyst`, `diagnose-fixer`, `diagnose-verifier` |
| `review-panel` | `review-correctness`, `review-security`, `review-simplicity`, `review-synthesizer` |
| `design-panel` | `design-explorer`, `design-designer`, `design-judge`, `design-skeptic` |
| `skill-forge` | `skill-forge-pressure-tester`, `skill-forge-forger`, `skill-forge-judge`, `skill-forge-linter` |
| `arch-drift-watch` | `arch-drift-watcher` |
| `improve-architecture` | `architecture-explorer`, `architecture-interface-designer`, `architecture-depth-checker` |
| `clean-room` | `clean-room-analyzer`, `clean-room-researcher`, `clean-room-gap-checker`, `clean-room-improvement-sweeper`, `clean-room-contamination-reviewer` |
| `autonomous-advisor` | `autonomous-advisor`, `autonomous-verifier` |

## Naming

Agent names are prefixed by the owning skill or job area. This avoids collisions
between generic role names like `validator`, `verifier`, and `scout` when
multiple loops are installed in the same repo.

## Scope

The packs cover development skills where a role has durable behavior worth
predefining:

- loop/pipeline makers and checkers
- parallel design, review, diagnosis, and skill-forge roles
- clean-room firewall roles
- architecture exploration and depth-check roles
- autonomous-advisor decision and verifier roles

`auto-research` intentionally does not ship a checker agent here. Its checker is
the frozen harness plus the frozen-path integrity gate.
