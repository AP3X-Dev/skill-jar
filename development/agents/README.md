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
