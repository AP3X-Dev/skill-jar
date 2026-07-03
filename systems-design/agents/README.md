# Systems-Design Agent Packs

This folder contains generated, copy-ready sub-agent instructions for the
systems-design skills.

The source of truth is `manifest.json`. Do not edit files under `claude/` or
`codex/` by hand. Regenerate them with:

```bash
python scripts/gen-agent-packs.py
```

The jar audit gate checks every category agent pack:

```bash
python scripts/gen-agent-packs.py --check
python scripts/audit-jar.py
```

## Layout

- `manifest.json` -- one host-neutral contract per role.
- `claude/*.md` -- generated Claude Code agents.
- `codex/*.toml` -- generated Codex agents.

## Install

Copy only the roles needed by the active design review into the target repo's
runtime agent directory:

```text
.claude/agents/<agent>.md
.codex/agents/<agent>.toml
```

## Roles

Every role below is defined in `manifest.json` and rendered to `claude/<role>.md`
and `codex/<role>.toml`. Grouped by the skill that owns them:

| Skill | Roles |
|---|---|
| `design-system` | `system-intake-analyst`, `system-topology-designer`, `system-topology-skeptic` |
| `api-design` | `api-contract-designer`, `api-compatibility-reviewer`, `api-abuse-reviewer` |
| `data-store-selection` | `data-access-analyst`, `data-store-designer`, `data-gate-reviewer` |
| `production-readiness` | `readiness-slo-operator`, `readiness-runbook-writer`, `readiness-launch-reviewer` |

## Scope

Systems-design roles are mostly design and review specialists:

- `design-system`: intake, topology design, and topology skepticism
- `api-design`: contract design, compatibility review, and abuse review
- `data-store-selection`: access-pattern analysis, store design, and gate review
- `production-readiness`: SLO/alerting, runbook drafting, and launch review

These roles do not replace the human's product and architecture judgment. They
make the evidence and gates sharper so the final design decision is better
grounded.
