# Worktree Isolation

Isolating parallel loop work. **One task per branch, one loop-agent per worktree.** Parallel agents on a single working tree corrupt each other — two makers editing the same checkout race on the index, stomp each other's uncommitted changes, and trip each other's gates. Isolation makes each cycle's diff attributable to exactly one task, so the checker reviews one change against one branch.

**Open a worktree whenever:**
- More than one agent may touch the repo concurrently (a maker + a separate checker, or several makers draining the inbox in parallel).
- The loop runs **unattended** (scheduled / `/loop` / CI) — an isolated tree means a bad cycle is abandoned by deleting a directory, never by untangling `main`.
- Phase 7's dry-run cycle, and every real cycle after it: trigger → discover → plan → maker → checker → state, all inside one worktree.

If the loop is strictly single-agent, human-supervised, and one cycle at a time, a plain branch on the main checkout is enough — but the moment a checker runs alongside the maker, isolate.

## The workflow (Layer 2 — the loop-agent runs this per cycle)

Tie the worktree and branch names to the **TASK-id** the planning step pulled from the state file (`agent-state/triage-inbox.md` / `loop-state.md`). One state-file task → one branch → one worktree. The id is the through-line: it appears in the directory name, the branch name, the commit subject, and the `completed.md` / `failed-attempts.md` entry, so any artifact can be traced back to the task that produced it.

### Create — one worktree per task

```bash
# TASK-001 is the id from agent-state/triage-inbox.md
git worktree add ../<repo>-task-001 -b task/TASK-001
cd ../<repo>-task-001
```

`git worktree add <path> -b <branch>` creates a new linked checkout at `<path>` on a fresh branch, sharing the original repo's `.git`. Branch off the loop's integration branch (`main`, `dev`, or whatever the state file records), not off another task's branch.

### Work — the maker stays inside its own tree

```bash
# inside ../<repo>-task-001
# read the exact files named in the TASK-001 state entry, make the smallest diff that does the work
git status            # confirm you are on task/TASK-001 and the tree is yours alone
```

Touch only files the task names. Do not reach into another task's worktree directory — each branch is a sealed unit of work.

### Verify — the checker gates this tree before anything merges

```bash
# inside ../<repo>-task-001
git status                 # nothing unexpected staged
git diff main...task/TASK-001 --stat   # the change is scoped to the task's files
<test command>             # e.g. npm test  |  pytest -q  |  go test ./...
<lint command>             # e.g. npm run lint
<typecheck command>        # e.g. tsc --noEmit  |  mypy .
```

Substitute the repo's real verification commands — the ones Phase 0 confirmed actually run. Each must exit `0`; a non-zero exit stops the cycle. This is the maker≠checker boundary: the **separate** checker agent (or the same gate run under the checker role) requires every command to pass on evidence, not assertion. No "looks good" — a gate is a command that exits 0/1.

### Commit — focused, one task per commit

```bash
# inside ../<repo>-task-001, only after every gate exited 0
git add <files the task changed> agent-state/
git commit -m "task(TASK-001): <one-line summary of the change>"
```

Bundle the code change with its `agent-state/` update in the same commit, so a restart never sees finished work that the state file doesn't record. Keep the diff to this one task. No trailers, no co-author lines.

### Merge or open a PR

```bash
# autonomy permitting, integrate; otherwise open a PR and let the human own the merge

# direct merge (low-risk loops):
git checkout main
git merge --no-ff task/TASK-001

# OR open a PR (default — the human owns the merge decision):
git push -u origin task/TASK-001
# then open the PR with the host's CLI, e.g.:
# gh pr create --base main --head task/TASK-001 --title "task(TASK-001): <summary>" --body "<what + why + gate output>"
```

The loop opens the PR; the developer still decides what ships. Record the merge/PR result and the commit SHA back into `agent-state/completed.md` against TASK-001.

### Cleanup — remove the worktree when the task closes

```bash
# after merge, or when the task is abandoned
git worktree remove ../<repo>-task-001
git branch -d task/TASK-001     # use -D if the branch was abandoned unmerged
git worktree prune              # drop any stale administrative entries
```

On abandonment, capture the reason in `agent-state/failed-attempts.md` before removing the tree, then remove it the same way.

## Native isolation (agent-agnostic)

The branch-per-task + checker-before-merge discipline is identical on every host; only the mechanism that hands the agent a clean tree differs. Detect the host and use its native primitive:

- **Claude Code** — isolate via git worktrees, and run the maker inside a worktree-isolated subagent so its filesystem and branch are its own. (The `superpowers:using-git-worktrees` skill provides this when present.)
- **Codex** — each thread gets a built-in worktree; let the thread's own tree be the task's isolation boundary and still branch per task within it.
- **Generic / CI host** — plain `git worktree` as scripted above; the CI job clones or adds the worktree, runs the gate commands, and tears the worktree down at the end of the job.

Whatever the host, the rules don't change: one task per branch, one agent per tree, and a separate checker passes the gate before the change reaches the integration branch. Keep the TASK-id naming consistent across hosts so the state files stay portable when the platform switches.

**Caution:** an auto-created worktree (Codex thread tree, Claude Code subagent tree, or a scripted one) must be removed when its task merges or is abandoned — otherwise stale worktrees and dangling `task/*` branches accumulate, slow `git status`, and leave orphaned checkouts that a later cycle may mistake for live work. Prune on close, every time.

---

See [loop-architecture.md](loop-architecture.md) for where isolation sits in the six-part spine (execution stage), and [building-optimization-loops](../../building-optimization-loops/SKILL.md) for the specialized optimization loop, which runs its sessions on a single `opt/` branch — a one-agent, one-branch instance of the same discipline.
