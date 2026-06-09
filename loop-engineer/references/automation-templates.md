# Automation Templates — triggers, automation prompts, and the per-cycle driver

**Layer 2.** Everything inside the template fences below is text that goes INTO the loop system — written in the imperative for the future **loop-agent** that runs it cycle after cycle, not for you scaffolding the loop now. You author and adapt this text; you do not execute it.

These templates cover Phase 4 of the scaffolding process (author triggers + driver prompt). They assume the state files from [state-templates.md](state-templates.md) (`agent-state/loop-state.md`, `triage-inbox.md`, `completed.md`, `failed-attempts.md`, `decisions.md`) already exist, and they defer halt logic and the primitive-to-platform map to [loop-architecture.md](loop-architecture.md) rather than restating them.

Steps labelled **(MemBerry)** are an optional adapter — skip every one of them when no MemBerry tools exist in the environment. The state files are the required mechanism; the loop runs fully without MemBerry.

---

## 1. The narrow-job principle

An automation has ONE narrow job. The trigger prompt that opens a cycle is the easiest place for scope to rot, so write it to do a single discoverable thing and nothing else. The progression:

**BAD — a wish, not a job:**

```
Every morning, improve the codebase.
```

Unbounded. "Improve" names no inputs, no output, no stopping point. The loop-agent will edit random files and churn.

**BETTER — narrow, read-only, but still prose:**

```
Every morning, inspect CI failures, open issues, TODO comments, and recent commits;
write a prioritized triage report; do not modify code.
```

Bounded inputs, a named output, an explicit no-write rule. Good enough to be safe; still vague about *where* it reads and writes.

**BEST — numbered, file-exact, idempotent:**

```
Every morning, run a triage-only cycle. Do not modify production code.

1. Read agent-state/loop-state.md for the current objective and the verification commands.
2. Review CI failures from the last 24h (run: <repo CI-status command>).
3. Review open issues labeled `bug` (run: <repo issue-list command>).
4. Scan recent commits for newly failing tests and new TODO/FIXME comments
   (run: <repo log/grep command over the last 24h>).
5. Cross-check each finding against agent-state/completed.md and
   agent-state/failed-attempts.md; drop anything already done or already rejected.
6. Append only new, actionable findings to agent-state/triage-inbox.md, one task each,
   with files-to-touch and a runnable verification command.
7. If nothing actionable remains, write "no actionable findings — <date>" to the inbox
   and stop. Do not invent work.
```

Lesson: the BEST version is the BETTER version with the inputs turned into numbered commands, the writes pinned to exact files, and a clean no-op path. **One narrow job. Exact files. A stop condition.** Every template that follows is built to this bar.

---

## 2. Discovery / automation prompts

Three ready triggers. Each shares the same contract, so it is stated once here and not repeated in every fence:

- **Narrow job.** One discovery pass, named inputs, named output.
- **Reads state.** `agent-state/loop-state.md` for the objective, `agent-state/completed.md` and `agent-state/failed-attempts.md` to suppress repeats.
- **Writes one place.** Appends to `agent-state/triage-inbox.md` only.
- **Never modifies code.** Discovery is read-only by definition; execution is a different stage (the driver, §3).
- **Ignores done/rejected items.** Anything already in `completed.md` or `failed-attempts.md` is skipped, not re-filed.
- **Emits only verifiable tasks.** Every appended task names exact files, carries a runnable verification command that exits 0/1, and is small enough for one worktree. If it isn't, file it as "needs-decomposition" and do not let the loop pick it up.

Replace every `<...>` with the repo's real command discovered in Phase 0.

### 2a. Daily triage

```
Run a triage-only discovery cycle. Do not modify any code.

1. Read agent-state/loop-state.md (objective + verification commands).
2. Gather candidate work from all of:
   - CI failures, last 24h:        <ci-status command>
   - open issues labeled bug:      <issue-list command>
   - new TODO/FIXME, last 24h:     <log/grep command>
   - tests that started failing:   <test command, failures only>
3. For each candidate, check agent-state/completed.md and
   agent-state/failed-attempts.md. Discard already-completed and already-rejected.
4. For each surviving candidate, write ONE inbox task with:
   - title
   - files to touch (exact paths)
   - verification: a single command that exits 0 when fixed
   - source (which input it came from)
   Skip any candidate you cannot pin to specific files or a runnable check.
5. Append the new tasks to agent-state/triage-inbox.md. Touch nothing else.
6. If no candidate survives, append "no actionable findings — <date>" and stop.
```

### 2b. CI-failure review

```
Review CI failures and file fixable ones. Do not modify any code.

1. Read agent-state/loop-state.md for the verification commands.
2. List failed CI runs since the last triage: <ci-failed-runs command>.
3. For each failure, fetch the failing job log: <ci-log command>.
4. Classify: (a) reproducible test/build failure with a clear owning file,
   (b) flake (passes on re-run: <ci-rerun or local-rerun command>),
   (c) infra/credential failure (not a code task).
5. File ONLY class (a). Each inbox task names the failing test, the file under test,
   and verification = the exact command that reproduces then must pass.
6. Skip any failure already in agent-state/completed.md or failed-attempts.md.
   Note flakes in agent-state/decisions.md instead of the inbox — do not file them as tasks.
7. Append class-(a) tasks to agent-state/triage-inbox.md. If none, append
   "CI: no fixable failures — <date>" and stop.
```

### 2c. Stale-issue review

```
Review stale issues and file the actionable ones. Do not modify any code.

1. Read agent-state/loop-state.md (objective) and agent-state/failed-attempts.md.
2. List issues with no activity in the configured window: <stale-issue-list command>.
3. Keep only issues that are (a) still open, (b) labeled bug or accepted, and
   (c) reproducible from the description against the current tree.
4. Drop anything already in completed.md or failed-attempts.md, and anything that
   needs a product decision — those are for the human, not the loop.
5. For each kept issue, write ONE inbox task: title, exact files implicated,
   a verification command that exits 0 once resolved, and the issue id as source.
   Decompose multi-part issues into one task per worktree-sized slice.
6. Append to agent-state/triage-inbox.md. If nothing qualifies, append
   "stale issues: none actionable — <date>" and stop.
```

---

## 3. The driver prompt

This is the per-cycle prompt the loop-agent runs once per cycle. It walks the six-part spine — trigger / discovery / planning / execution / verification / state-update — for exactly ONE task, enforces maker≠checker, and ends by committing code and state together. The trigger is whatever fires the cycle (§4); discovery has usually already filled the inbox via §2, so the driver's job starts at planning.

Save it where the scaffolder puts it — `docs/prompts/<loop>-driver.md` — and point the host at that path (Claude Code: pass it to `/loop`; Codex: a prompt file or `codex exec` argument; generic: any file the runner pipes in). Replace `<...>` with the repo's real values from Phase 0.

```md
# Driver — one loop cycle

You run ONE cycle of the loop, then stop. Do the smallest correct thing and record it.
Operate only inside agent-state/ and the code the chosen task names. Never widen scope.

## 0. Preflight (recover before you start)
- Check out the working branch: `git checkout <loop-branch>` (or create it if missing).
- Run `git status`. If the tree is dirty from a crashed prior cycle, recover the in-flight
  task: read its entry in agent-state/loop-state.md, then EITHER finish it from the partial
  diff OR `git checkout .` back to the last good commit. Log the recovery action to
  agent-state/loop-state.md either way. Do not start new work on a dirty tree.

## 1. Load context
- (MemBerry) `berry_load(task: "<objective> — next loop task", tags: ["project:<tag>"])`.
  Pull conventions, past decisions, and known gotchas for the area you are about to touch.
  If no MemBerry tools exist, skip this step.
- Read agent-state/loop-state.md (current objective + verification commands),
  agent-state/failed-attempts.md (do not retry a rejected approach), and
  agent-state/completed.md (do not redo finished work).

## 2. Planning — pick ONE task
- Read agent-state/triage-inbox.md. Choose the single highest-priority task that is
  worktree-sized and not present in completed.md or failed-attempts.md.
- If the inbox is empty or every task is blocked, go to End condition.
- Restate the chosen task in agent-state/loop-state.md as the in-flight task, with its
  files and verification command, so a crash mid-cycle is recoverable.

## 3. Execution (maker: read, then implement the smallest fix)
- Read every file the task names before editing anything.
- Implement the smallest diff that satisfies the task's verification command. No drive-by
  renames, reformatting, or unrelated edits. Do not delete or skip tests to pass.
- Where practical, add or adjust a test that fails before the fix and passes after.

## 4. Verification (checker: a SEPARATE agent gates this)
- Hand the diff to the checker/verifier subagent (see subagent-templates.md). The maker
  does not grade its own work. The checker runs the task's verification command and the
  repo gate, inspects the diff for scope creep, deleted/skipped tests, and unrelated files,
  and decides PASS or REJECT — with evidence (the command output), never "looks good".
- On REJECT: append the task, the approach tried, and the rejection reason to
  agent-state/failed-attempts.md, revert the diff (`git checkout .`), and go to End condition.
  Do not loop on the same task within one cycle.

## 5. Re-run the gate (confirm green before recording)
- Run the full gate yourself: <test command> && <lint command> && <typecheck/build command>.
- All must exit 0. Confirm `git status` shows no unrelated files changed and no secrets added.
  If anything is red, treat it as a REJECT (step 4) — never record a red cycle as done.

## 6. State update
- Move the task from agent-state/triage-inbox.md to agent-state/completed.md with its commit
  reference and a one-line result. Clear it from the in-flight slot in loop-state.md and set
  the next-action note. Record any decision worth keeping in agent-state/decisions.md.

## 7. Commit — code and state together
- Stage the code changes AND the updated agent-state/ files, then commit as one unit:
  ```
  git add <changed code files> agent-state/
  git commit -m "loop: <task title>

  <one-line root cause or summary>."
  ```
- Committing state in the same commit means a restart never sees a committed-but-unrecorded
  task. If the gate is not green, do not commit — revert and record the rejection instead.

## 8. (MemBerry) Store learnings
- `berry_store(session_id: "<id>", task: "[project:<tag>] loop: <task title>",
  content: "[project:<tag>] Fixed <what> (<short sha>). Root cause: <why>. Convention: <if any>.",
  outcome: "approved", entities: ["<affected-modules>"])`.
- If a fix confirmed or contradicted existing MemBerry knowledge, include the signal.
- Skip this entire step if no MemBerry tools exist.

## 9. Choose next / End condition
- If agent-state/triage-inbox.md still holds actionable, unblocked tasks, this cycle is done —
  the next cycle's trigger will pick up the next task. Stop here.
- Stop when the inbox is empty (nothing actionable remains), OR escalate to the human when a
  halt trigger fires. Do not re-list the halt triggers here — apply the ones defined in
  loop-architecture.md (the halt-triggers section). A halt writes the blocking item and reason
  to agent-state/loop-state.md, then stops the loop cleanly.
```

---

## 4. Wiring triggers to the host

The driver above is host-neutral; what fires it is host-specific. Below are the minimal forms per platform. For the full primitive-to-platform map (which automation primitive maps to which platform, and the autonomy-ladder gate at each level), see [loop-architecture.md](loop-architecture.md) — do not duplicate that table here. Pick the form your host supports and point it at the driver from §3.

**cron (generic / any Unix host).** Run the driver once per schedule via the host's headless agent CLI:

```cron
# 07:00 daily — run one loop cycle, log output
0 7 * * *  cd /path/to/repo && <agent-cli> run --prompt docs/prompts/<loop>-driver.md >> agent-state/loop.log 2>&1
```

**GitHub Actions (CI-only host).** A scheduled workflow that runs the driver headless:

```yaml
name: loop-cycle
on:
  schedule:
    - cron: "0 7 * * *"   # daily at 07:00 UTC
  workflow_dispatch: {}     # allow manual runs
jobs:
  cycle:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - name: Run one loop cycle
        run: <agent-cli> run --prompt docs/prompts/<loop>-driver.md
        # provide the agent's API key via secrets, e.g. env: { API_KEY: ${{ secrets.AGENT_API_KEY }} }
```

**Claude Code (`/loop`).** Re-run the driver on an interval from inside a session:

```
/loop 1h <driver-prompt-or-command>
```

The interval (`1h`) is the cycle cadence; the argument is the driver prompt from §3 or a slash command that invokes it. Omit the interval to let the agent self-pace between cycles.

**Codex (scheduled task / cron).** Codex has no `/loop`; schedule its headless runner instead — a cron line or scheduled task invoking `codex exec` (or the host's task scheduler) against `docs/prompts/<loop>-driver.md`, using the cron form above with `<agent-cli>` = the Codex CLI.

**A `/goal`-style done condition (where the host supports goal-bounded runs).** Instead of a fixed interval, bound the run by a falsifiable completion check so the loop stops itself when the work is actually finished:

```
Continue until all tests in test/<area> pass, lint is clean, no unrelated files are
modified, and agent-state/loop-state.md is updated. Then stop.
```

Every clause is a runnable check, not a vibe — the same gate the driver's step 5 enforces, hoisted to the trigger so the host can decide when to halt.
