# State Templates

The state file is what makes the loop **restartable**. Without it, every run starts cold: a fresh loop-agent re-discovers finished work, re-runs completed fixes, and loses what the last cycle found. These files live in `agent-state/` and are the loop's REQUIRED restart spine — the loop works with nothing else. They are **authoritative for loop STATE**: what the objective is, what gate proves a task, what's open, what's done, what failed, and what runs next. MemBerry, when present, adds a learning layer on top (see the last section) — but state files alone are sufficient to continue, and a loop with no state file is not restartable.

Everything inside the fences below is **Layer 2** — text the future loop-agent reads and acts on, not instructions for you scaffolding the loop now. Drop each block into `agent-state/` under the named file and fill the placeholders with this repo's real objective and commands.

---

## 1. `loop-state.md`

The control file for the current run. One narrow objective, the exact gate commands for THIS repo, and the live task tables. A restarting loop-agent reads this first.

```md
# Loop State

## Current Objective

<One narrow job in a single sentence. Not "improve the codebase" — "triage new CI
failures and open bugs into the inbox each cycle" or "clear the open-tasks table,
one task per cycle, gate-verified.">

## Verification Commands

The gate. Each command must exit 0 to pass and non-zero to fail — no "looks good"
judgement. Fill these in with the exact commands this repo runs; delete any line the
repo does not have. A task is never COMPLETED unless the relevant commands here exit 0.

- Tests:      <e.g. `npm test` | `pytest -q` | `go test ./...` | `cargo test`>
- Lint:       <e.g. `npm run lint` | `ruff check .` | `golangci-lint run`>
- Typecheck:  <e.g. `npm run typecheck` | `tsc --noEmit` | `mypy .`>
- Build:      <e.g. `npm run build` | `cargo build --release` | `make`>

## Open Tasks

| ID | Task | Owner | Status | Files | Acceptance (exits 0) |
|----|------|-------|--------|-------|----------------------|
|    |      |       | PENDING / IN PROGRESS / BLOCKED |  |  |

## Completed Tasks

| ID | Task | Cycle | Commit | Result |
|----|------|-------|--------|--------|
|    |      |       | `<short sha>` | gate green: tests/lint/typecheck pass |

## Failed Attempts

| ID | Task | What Failed | Lesson |
|----|------|-------------|--------|
|    |      |             |        |

## Current Rules

- Don't rewrite stable modules without a stated reason tied to a task or a defect.
- Prefer small PRs — one task per cycle, smallest diff that passes the gate.
- Always run the Verification Commands before marking a task COMPLETED. Gate exits 0, or it isn't done.
- Record every failed attempt in `failed-attempts.md` so a future cycle doesn't retry a known bad path.
- <Add repo-specific rules: protected paths, no schema/API changes without a Block, dependency constraints.>

## Next Run Instructions

Continue from the highest-priority IN PROGRESS or PENDING task in **Open Tasks**.
If a task is IN PROGRESS, recover its partial work or revert to the last gate-green
commit before starting. If Open Tasks is empty, run Discovery (write findings to
`triage-inbox.md`) and stop — do not invent work.
```

---

## 2. `triage-inbox.md`

Where **Discovery** writes findings before they become tasks. Discovery proposes; Planning promotes a finding into `loop-state.md` Open Tasks. Keep findings small enough that one fits in a single cycle in a single worktree.

```md
# Triage Inbox

Discovery appends findings here. Before adding one:
- Read `failed-attempts.md` — if this exact path already failed, do not re-add it.
- Scan existing findings and Open Tasks — do not create a duplicate.
- Only add a finding small enough to execute in **one cycle, in one worktree**.
  If it's larger, split it or mark it as needing a human to break it down.

## Findings

### F-<id> — <Title: one concrete sentence>
- **Source:** <CI run | issue #N | commit `<sha>` | TODO at file:line | test `<name>` | branch `<name>`>
- **Priority:** High | Medium | Low
- **Risk:** low | medium | high  <!-- blast radius if the fix is wrong; high = touches public API, schema, auth, or on-disk format -->
- **Suggested owner:** explorer | implementer | verifier | security-reviewer
- **Verification command:** <the exact runnable check that would PROVE a fix —
  e.g. `pytest tests/test_auth.py::test_expiry` exits 0, or `npm run lint` is clean.
  A finding with no provable check is not ready to become a task.>

<...more findings...>
```

---

## 3. `completed.md`

Append-only log of finished tasks. Never edited, never reordered — the durable record of what shipped and where to find it.

```md
# Completed Tasks (append-only)

| ID | Task | Cycle | Commit | Result |
|----|------|-------|--------|--------|
|    |      |       | `<short sha>` | gate green: tests/lint/typecheck pass |
```

---

## 4. `failed-attempts.md`

Append-only. **This file exists so future cycles don't burn time retrying a path that already failed.** When a fresh loop-agent restarts, it has no memory of the dead ends a previous agent hit — this file is that memory. Before a cycle commits to an approach, it reads here; if the same task/approach is logged as failed, it picks a different path or escalates instead of repeating the loss.

```md
# Failed Attempts (append-only)

Future cycles read this BEFORE attempting a task. If your task and approach match a
row below, do not retry it as-is — choose a different approach or escalate to the human.

| ID | Task | What Failed | Lesson |
|----|------|-------------|--------|
|    |      | <approach + how it failed: gate red, broke X, wrong assumption> | <what to do instead next time> |
```

---

## 5. `decisions.md`

Durable decisions and conventions the loop established — the choices that should outlive any single cycle so later cycles stay consistent instead of re-litigating settled questions.

```md
# Decisions & Conventions

| Decision | Rationale | Cycle |
|----------|-----------|-------|
| <e.g. "Error handling uses Result<T,E>, not exceptions"> | <why this was chosen> | <N> |
| <e.g. "DB migrations live in /migrations, never inline"> | <consistency / past breakage> | <N> |
```

---

## State protocol

**One cycle is the atomic unit.** Commit the code change AND the state-file update in the **same commit** — never the code in one commit and the `loop-state.md` / `completed.md` update in another. If they split, a crash or restart between them leaves the loop with a committed-but-unlogged task: the next cycle re-does work that's already in the tree.

```
git add <changed source files> agent-state/loop-state.md agent-state/completed.md
git commit -m "<task ID>: <what changed>"
```

Three hard invariants every cycle obeys:

- **Verify before completing.** Never move a task to **Completed Tasks** unless the **Verification Commands** in `loop-state.md` exited 0 for the change. Gate green, or the task stays IN PROGRESS.
- **Log code and state together.** The single commit above keeps the record and the tree in sync, so a restart never sees a finished-but-unrecorded task — or a recorded-but-unbuilt one.
- **State is authoritative for what's next.** A restarting loop-agent decides the next task from `loop-state.md`, not from chat history, not from a MemBerry marker that lacks a commit SHA in `completed.md`.

---

## (MemBerry) learning layer — optional, skippable when absent

**Skip this entire section if no MemBerry tools exist in the environment.** The files above are the required mechanism and are fully sufficient on their own. MemBerry adds a cross-session *learning* layer; every step here is optional and labelled **(MemBerry)**.

When MemBerry is present, its memory tiers map onto the loop like this:

| MemBerry tier / block | Loop use |
|-----------------------|----------|
| **Core: `current_objective`** | The loop's one narrow job — mirrors `loop-state.md` ## Current Objective |
| **Core: `project_state`** | Loop health / metrics — pass rate, open-task count, cycles run |
| **Working: `working_state`** | This cycle's in-flight task, for crash recovery (what was mid-edit when it died) |
| **Working: `open_questions`** | Blocked or ambiguous items the loop couldn't resolve and skipped |
| **Archive (`berry_store`)** | Each cycle's decisions, root causes, and conventions — the *why* |

**Division of labor:** the **state files track WHAT'S DONE**; **MemBerry remembers WHAT WAS LEARNED**. `completed.md` and `loop-state.md` are the source of truth for loop state (tasks, gate results, commit SHAs); `berry_store` captures the reasoning the files don't — root causes, conventions, tradeoffs, signals against prior knowledge. **Never paste a state-file log entry into a `berry_store` call** — store the decision and its rationale, not the punch-list row. On any disagreement about state, trust the files and correct MemBerry.
