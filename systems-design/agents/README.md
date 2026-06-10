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

## Scope

Systems-design roles are mostly design and review specialists:

- `design-system`: intake, topology design, and topology skepticism
- `api-design`: contract design, compatibility review, and abuse review
- `data-store-selection`: access-pattern analysis, store design, and gate review
- `production-readiness`: SLO/alerting, runbook drafting, and launch review

These roles do not replace the human's product and architecture judgment. They
make the evidence and gates sharper so the final design decision is better
grounded.
