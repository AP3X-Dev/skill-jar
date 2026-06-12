# drop-in skill hooks ecosystem -- design

**Date:** 2026-06-11
**Status:** approved design, pre-implementation
**Reference:** Hermes/AG3NT lifecycle hooks and self-improvement substrate

## What this is

Skill Jar should let a maintainer drop any valid skill folder into the repo and
have that skill join the jar ecosystem automatically. The required input is a
category folder containing `SKILL.md`. A deterministic sync path discovers the
new skill, updates generated metadata, registers it for pressure testing, and
ensures future usage and failure events can become self-improvement evidence.

The hooks system is repo-internal first. It borrows the useful Hermes pattern:
typed lifecycle events, JSON payloads, a small dispatcher, append-only evidence,
and a separate judge/checker for improvement decisions. It does not copy
Hermes's full event bus or general-purpose shell hook surface in v1.

## Decisions made during brainstorming

| Decision | Choice | Rationale |
|---|---|---|
| Scope | Repo-internal first | Improve Skill Jar itself before making hooks portable to downstream installs. |
| Default behavior | Drop-in reconciliation | A user should not remember a manual "add" sequence after placing a skill in the jar. |
| Hook power | Observe and queue | Hooks record evidence and queue candidates. They do not rewrite skills directly. |
| Self-improvement path | Route through `skill-forge` | Skill edits still require RED evidence, maker/checker separation, and the audit gate. |
| Automation boundary | Deterministic sync script plus audit | The script performs mechanical reconciliation; `python scripts/audit-jar.py` proves the ecosystem is consistent. |

## Core guarantee

If a user adds:

```text
development/example-skill/SKILL.md
```

then runs the sync/audit path, the repo should reconcile itself into a valid
state:

- `skills.json` includes the skill.
- Category plugin manifests include the skill path.
- `agent-state/SKILL_FORGE_TRACKER.md` has a `pending-red` row for the skill,
  unless a durable row already exists.
- Generated agent packs remain in sync.
- Default hook/evidence paths exist.
- The jar audit gate passes or reports concrete failures.

A plain skill does not execute hooks by itself. It becomes discoverable,
plugin-installable, tracked for pressure testing, and eligible for usage/failure
evidence. If the skill later declares generated roles, those roles inherit
default usage/failure hooks from the generator.

## Architecture

### 1. Drop-in reconciler

Add `scripts/sync-jar.py` as the one command that absorbs filesystem changes.
It should be idempotent and safe to run after every skill edit.

Responsibilities:

1. Discover valid skills through the same `jarlib.discover_skills()` path used
   by existing generators.
2. Run or call the existing index/plugin generators instead of duplicating their
   logic.
3. Add missing `SKILL_FORGE_TRACKER.md` rows as `pending-red`.
4. Preserve existing tracker rows, evidence history, failed attempts, and
   completed tasks.
5. Ensure `agent-state/skill-usage.md` exists with stable headings.
6. Run `scripts/gen-agent-packs.py` when agent manifests are present.
7. Report a concise summary of created, updated, preserved, and blocked items.

The reconciler must not delete tracker rows automatically. If a skill folder is
removed while a tracker row remains, it records or reports a human-decision item
instead of erasing history.

### 2. Hook declarations

Hooks live in agent role definitions, not in every skill body. There are two
sources:

- Hand-authored repo-local roles under `.claude/agents/`.
- Generated category agent roles under `<category>/agents/manifest.json`.

The generated agent-pack script owns default hooks so future generated roles get
them automatically:

- `after_task` -> record usage evidence.
- `on_error` -> record failure evidence and queue review.
- `on_reject` -> record rejection evidence where checker roles use it.

Skill-specific hooks can be added later through the manifest, but v1 should not
require them for ordinary skills.

### 3. Hook dispatcher

Add `scripts/dispatch-agent-hooks.py` as a narrow dispatcher for repo state
updates. It should accept arguments like:

```text
python scripts/dispatch-agent-hooks.py --agent <role> --event after_task --skill <skill> --note "<summary>"
```

The dispatcher reads hook declarations from the relevant role file, builds a
typed payload, and applies supported actions:

- `record_usage` appends to `agent-state/skill-usage.md`.
- `queue_improvement` appends a candidate to the same file's improvement queue.
- `log_failed_attempt` appends to `agent-state/failed-attempts.md`.
- `append_note` appends a scoped note to an existing tracker/inbox.
- `update_tracker` updates a single `SKILL_FORGE_TRACKER.md` row when a
  skill-forge stage has already produced the evidence.

Unsupported actions fail closed with a nonzero exit. Hook failures should not be
silently treated as successful self-improvement.

### 4. Usage and improvement evidence

Add `agent-state/skill-usage.md` with stable sections:

```text
# Skill Usage -- skill-jar

## Usage Entries

## Improvement Queue
```

Usage entries are append-only and deduplicated by exact row. Improvement queue
entries are also append-only. A queue entry is a candidate for a future
`skill-forge` cycle, not an instruction to edit a skill immediately.

Example entry shape:

```text
- [development/example-skill/fixer/on_error] failed to follow TDD red phase; queued for skill-forge pressure scenario.
```

The queue should capture enough context to reproduce pressure:

- skill name
- role or loop that used it
- event name
- short failure or success signal
- pointer to the state file, run package, or command output that holds evidence

### 5. Driver wiring

Update repo driver prompts so loop stages dispatch hooks after they update their
source-of-truth state:

- `docs/prompts/jar-audit-driver.md`
- `docs/prompts/bug-pipeline-driver.md`
- `docs/prompts/skill-forge-driver.md`

The drivers still own the loop order. Hooks do not replace the state files or
the audit gate. They remove repeated manual note-writing and create a single
evidence stream for future skill hardening.

## Safety model

Hooks may:

- append evidence
- queue an improvement candidate
- update a single declared tracker row after a stage has produced evidence

Hooks must not:

- edit `SKILL.md` files directly
- weaken `scripts/audit-jar.py`
- delete state rows
- push to a remote
- mark a skill `forged`
- validate a maker's own work

The only path from hook evidence to skill changes is:

1. Evidence lands in `agent-state/skill-usage.md` or a tracker.
2. A `skill-forge` cycle selects one candidate or tracker row.
3. RED captures the actual shortcut or failure.
4. GREEN patches only the named loophole.
5. REFACTOR gets independent judge passes.
6. `python scripts/audit-jar.py` exits 0.
7. Code and state commit together.

## Generated agent behavior

`scripts/gen-agent-packs.py` should validate optional hook blocks in
`agents/manifest.json`, render them into both Claude and Codex role files, and
inject default usage/failure hooks into every generated role.

This is what makes future generated roles automatic. A new skill with role
agents adds or updates its manifest; the generator handles hook text and the
audit gate proves generated files are current.

## Audit integration

The authoritative gate remains:

```text
python scripts/audit-jar.py
```

The audit should continue checking generated metadata and agent-pack sync. It
may later add hook-specific checks once the dispatcher exists:

- hook events/actions in manifests are known
- generated hook text matches the manifest
- dispatcher script compiles
- required state files exist
- a small smoke dispatch appends to a temp copy or temp repo state without
  corrupting markdown sections

The first implementation should avoid weakening the audit script. If a desired
hook check conflicts with existing behavior, log a decision item instead of
loosening the gate.

## Out of scope for v1

- A portable hook runtime for downstream repos.
- General shell hooks, arbitrary commands, or a full Hermes-style decision
  protocol.
- Automatic direct edits to skills based only on usage logs.
- Scheduler/cron execution.
- Remote push or PR creation.
- Deleting stale tracker rows when a skill disappears.

## Definition of done for implementation

- Dropping a new valid `SKILL.md` and running the sync path registers it in the
  generated index, plugin metadata, and `SKILL_FORGE_TRACKER.md`.
- Generated agent roles receive default usage/failure hooks automatically.
- Repo-local loop roles can dispatch hook events into append-only state.
- Failure events create improvement queue entries without editing skills.
- `python scripts/audit-jar.py` exits 0.
- Code and state changes commit locally only.
