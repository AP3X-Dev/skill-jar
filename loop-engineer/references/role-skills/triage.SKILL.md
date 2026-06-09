---
name: triage
description: "Discover, classify, and prioritize work in this repository for the loop's triage stage. Use when reviewing failing CI, open issues, recent commits, TODO comments, broken tests, or stale branches and writing findings to agent-state/triage-inbox.md."
---

<!--
LOOP-ENGINEERING ROLE-SKILL TEMPLATE (Layer 2).
The scaffolding agent installs this at the target repo's skills/triage/SKILL.md.
Everything below the frontmatter is written in the imperative for the future
loop-agent that runs the triage stage each cycle — not for the human scaffolding
the loop now. Before handing off, REPLACE every <angle-bracket placeholder> with
this repo's real commands, paths, role names, and branch conventions, and DELETE
any line that does not apply. A finding with a placeholder verification command is
not installed — it is a stub.
-->

# Triage

Discover work in this repository, classify it, prioritize it, and write the result to `agent-state/triage-inbox.md`. This is the **discovery** stage of the loop's six-part spine (trigger → discovery → planning → execution → verification → state-update). You produce the inbox the planning stage reads; you do not execute.

## Purpose

- Find work that exists in the repo right now: failing CI, open issues, regressions, TODOs, stale branches.
- Classify each finding (source, priority, risk, suggested owner role) and attach a **verification command** that will later prove the work done.
- Write findings to `agent-state/triage-inbox.md` in the Output Format below.
- **Never modify production code during triage.** You read, classify, and write to `agent-state/` only. The maker role (a separate agent — maker≠checker) does the work in its own worktree; you stage it.

## When To Use

Run this skill at the start of a cycle when work needs to be *discovered* before it can be done:

- CI is failing on `<default-branch>` or an open PR.
- The issue tracker has open issues or bug reports not yet in the inbox.
- Recent commits introduced a regression, a `// TODO`/`// FIXME`/`// HACK`, or an incomplete feature.
- The test suite has broken or skipped (`.skip`/`xit`/`@pytest.mark.skip`) tests.
- Branches have gone stale (merged-but-not-deleted, or diverged far from `<default-branch>`).

## Process

Run these steps in order. Steps marked **(MemBerry)** are optional — if no MemBerry tools exist in this environment, skip them; the `agent-state/` files are the required mechanism and are sufficient on their own.

1. **Read loop state first.** Read `agent-state/loop-state.md` (current objective, autonomy level, verification commands this repo gates on) and `agent-state/failed-attempts.md` (fixes already tried and rejected). Read `agent-state/completed.md` and the existing `agent-state/triage-inbox.md` so you do not re-file finished or already-queued work.
   - **(MemBerry)** `berry_load(task: "triage cycle: discover work", tags: ["project:<tag>"])` to recall conventions and known gotchas before classifying.

2. **Review live sources of work.** Run each discovery command this repo actually supports and collect raw findings:
   - Open issues / bugs: `<gh issue list --state open --limit 50>` (or the repo's tracker query).
   - Recent CI failures: `<gh run list --status failure --limit 20>` (or the host's CI query / the last red pipeline log).
   - Recent commits: `git log --oneline -30 <default-branch>` — look for regressions, reverts, and "WIP"/"temp"/"FIXME" messages.
   - TODO/FIXME/HACK markers: `<rg -n "TODO|FIXME|HACK|XXX" --glob '!agent-state/**'>` (use this repo's content-search tool).
   - Broken/skipped tests: `<the repo's test command>` — capture failures and any `.skip`/`xit`/quarantined tests.
   - Stale branches: `git for-each-ref --sort=-committerdate --format='%(refname:short) %(committerdate:relative)' refs/heads`.

3. **Identify cycle-sized tasks.** Reduce raw findings to tasks each **small enough for ONE cycle in one worktree**. If a finding is multi-cycle, split it and file only the first independently-verifiable slice; note the parent. A task too big for one worktree is a planning hazard, not a triage finding.

4. **Write findings to the inbox.** Append each task to `agent-state/triage-inbox.md` using the Output Format below. Order by priority (descending). Do not touch any file outside `agent-state/`.

5. **Do not modify production code.** Triage discovers and classifies; it never fixes. If you spot a one-line fix, you still only *file* it — the maker role applies it under verification in a worktree.

## Output Format

Each finding is one entry in `agent-state/triage-inbox.md`. Every field is required; an entry missing a runnable **Verification command** is not a valid finding.

```markdown
### F-<id> — <Title: one concrete sentence>
- **Source:** <CI run | issue #N | commit `<sha>` | TODO at file:line | test `<name>` | branch `<name>`>
- **Priority:** High | Medium | Low
- **Risk:** low | medium | high  <!-- blast radius if the fix is wrong; high = touches public API, schema, auth, or on-disk format -->
- **Suggested owner:** explorer | implementer | verifier | security-reviewer  <!-- a role this loop scaffolded, not a person -->
- **Verification command:** `<exact command that exits 0 when this task is done, non-zero otherwise>`
```

The **Verification command** is the contract the maker's work is gated against — it must be a real command in this repo (a single failing test, `<lint> <path>`, `<typecheck>`, a build, a script that exits 0/1), never "looks good" or "check it works". Prefer the narrowest command that proves *this* task: a single test id over the whole suite.

## Rules

- **Prefer small, verifiable tasks.** A task that fits one cycle in one worktree and carries a runnable verification command outranks a large vague one. Split anything bigger.
- **No duplicate tasks.** Before filing, check `agent-state/triage-inbox.md`, `agent-state/completed.md`, and open work — do not re-file something already queued or done. Dedupe by source (issue #, commit sha, file:line, test name), not by title text.
- **Check `failed-attempts.md` before recommending a fix.** If a finding matches a fix already tried and rejected there, do not re-file it as-is — either skip it or file it with a *different* approach and a note referencing the prior failure. Re-queuing a known-dead fix wastes a whole cycle.
- **Every task carries a verification command.** No exceptions. A finding without one is incomplete; either find the command or do not file it.
- **Stay read-only on production code.** Your only writes are to `agent-state/`. Modifying source, tests, or config during triage breaks the maker≠checker split.
- **Respect the current autonomy level.** Read it from `agent-state/loop-state.md`. At triage-only (Level 1 of the autonomy ladder) you fill the inbox and stop — you never queue work the loop is not yet permitted to execute.
- **(MemBerry, if available)** After a triage cycle, store noteworthy patterns (recurring failure classes, hot files) so future cycles triage faster: `berry_store(session_id: "<id>", task: "[project:<tag>] triage cycle", content: "<patterns observed, recurring sources>", outcome: "approved")`. Skip silently if MemBerry is absent.
