---
name: sprint-ticket-runner
description: "Use when running a long development sprint, autonomous coding cycle, or multi-ticket implementation push that needs a local Linear-style board, durable ticket state, worktree isolation, maker-checker verification, and first-class parallelism detection. Turns PRPs/PRDs/plans/user requests into executable tickets, keeps `agent-state/sprint/` current across restarts, classifies what can run in parallel, and prevents agents from drifting during multi-hour or multi-day work. NOT for a single bug, one-off edit, plan cleanup (use plan-prune), or generic quality loop (use optimization-loop)."
---

# Sprint Ticket Runner

Run a long development cycle from local, repo-visible tickets. This skill gives
the agent a lightweight Linear-style workflow without depending on Linear: every
ticket, lane decision, verifier result, failed attempt, and handoff lives under
`agent-state/sprint/` so a fresh session can resume from files instead of chat
memory.

**Output:** a maintained sprint board, ticket files with acceptance checks,
`parallelism-map.md`, decision and failed-attempt logs, per-cycle verifier
evidence, and a cold-start handoff. For execution cycles, code changes are done
in isolated worktrees/branches and the board is updated before the cycle is
considered complete.

## Operating Contract

Act like the sprint's local issue tracker and execution controller. The sprint
state is authoritative for what is in flight; the source PRP/PRD/roadmap remains
authoritative for product intent. A validated [spec-driven-change](../spec-driven-change/SKILL.md)
change folder is an accepted intent source — its `tasks.md` seeds tickets and its
`openspec/specs/` is the authoritative requirements the board points at. Do not
merge planning fragments or rewrite the roadmap here. If planning sources conflict, record a blocked planning issue and
recommend [plan-prune](../plan-prune/SKILL.md); keep the sprint runner focused
on ticketed execution.

Every ticket must be small enough to verify, must name files or discovery steps,
and must carry a runnable acceptance command before it moves to `ready`.
Maker and checker stay separate — always, regardless of time pressure or how
well a maker "understands" its own code; a maker verifying its own ticket is
never allowed and never an efficiency win. Parallel work is allowed only from the
parallelism audit and is invalidated when actual touches exceed the predicted
write set. Disjoint-looking directory names are not an audit: never substitute
eyeballing paths for tracing real imports, consumers, and shared state. Never
launch two tickets in parallel planning to "resolve merge conflicts later" — a
foreseeable conflict means they are `serial`, not `parallel-build`.

**Launch gate — this skill OFFERS launch, it never auto-launches.** Before
launching any code-writing maker (Phase 4 onward), present the parallelism map
and the first-cycle plan and get an explicit human "go". A compute-spending
execution loop starts only on an explicit human yes; ticket creation and the
parallelism audit (Phases 0–3) and Analysis-Only Mode need no such approval. A
vague standing instruction ("run them", "parallelize", "run to completion",
"keep going until it's done") is NOT the launch-gate go and is NOT a license to
auto-launch the next maker the moment one finishes: it authorizes a budget, not
a bypass. You still present the map, get the explicit go, and re-clear the gate
whenever the map is refreshed.

**Stop condition.** Repeat the execute → verify → update cycle only until one of
these holds, then write the Closeout and stop — never spin cycles past an empty
`ready` lane or an approved budget:

- no `ready` tickets remain;
- a `blocked` / `NEEDS-DECISION` ticket needs a human; or
- the human-approved budget (cycle count, wall-clock, or cost) is exhausted.

Work that surfaces mid-sprint (follow-up fixes, easy wins, dependency
fallout) is new backlog, not a reason to keep the loop spinning. Having
cycles or momentum left does not extend the sprint: file the new items as
tickets and stop at the marker. New unticketed work never runs without going
back through ticket creation, the audit, and the launch gate.

## State Layout

Create or maintain these files:

```text
agent-state/sprint/
  board.md
  parallelism-map.md
  decisions.md
  failed-attempts.md
  handoff.md
  tickets/
    SPR-001.md
```

Use the templates in [references/ticket-schema.md](references/ticket-schema.md).
Use [references/parallelism-audit.md](references/parallelism-audit.md) whenever
building or refreshing `parallelism-map.md`.

## Process

### 0. Preflight

Check git status, current branch, existing `agent-state/`, README/AGENTS/CLAUDE
rules, and the repo's real verification commands. If `agent-state/sprint/`
exists, read `handoff.md`, `board.md`, `parallelism-map.md`, open tickets, and
failed attempts before doing anything else. Recover or close any half-written
ticket state before starting new work.

### 1. Ingest Intent

Read the source of work: PRP, PRD, canonical plan, issue export, roadmap slice,
or direct user request. Extract only actionable development items. Preserve each
item's source link/path in the ticket. If source documents disagree on what the
product should do next, add a row to `decisions.md` instead of guessing.

### 2. Create or Refresh Tickets

Write one file per ticket. Each ticket needs:

- ID, title, status, priority, source, and current owner.
- Objective and non-goals.
- Dependencies and blocked decisions.
- Predicted write set and known hot files.
- Acceptance command that exits 0 when done.
- Maker, checker, branch/worktree, evidence, and commit fields.

Statuses are: `backlog`, `scoped`, `ready`, `in-progress`, `review`,
`verified`, `done`, `blocked`, `reopened`.

Do not move a vague item to `ready`. Split oversized work into smaller tickets.

### 3. Run the Parallelism Audit

Before launching makers, classify the ticket set with the required audit in
[references/parallelism-audit.md](references/parallelism-audit.md). The audit
must estimate predicted write sets, shared hot files, gates, dependencies,
schema/API/config/state changes, verifier/resource constraints, and confidence.

Write the result to `agent-state/sprint/parallelism-map.md` with lanes:

- `parallel-scope`: read-only research can run in parallel.
- `parallel-build`: implementation can run concurrently in separate
  worktrees/branches.
- `batch-verify`: changes are disjoint enough to share one expensive gate.
- `serial`: order is required because of hot files, dependencies, or shared
  state.
- `blocked`: human decision, missing gate, or risky ambiguity.

The parallelism map is a prediction, not a license to ignore reality. If a
ticket touches files outside its predicted write set, changes a shared schema or
config, or introduces a new dependency, pause new parallel launches and refresh
the map. There is no smallness exemption: a one-line, still-compiling touch to a
shared file is exactly the case the invalidation triggers exist for. "It
compiles" is not "it is safe to parallelize" — refresh the map before launching
the remaining tickets.

### 4. Execute One Cycle

Only after the launch gate (Operating Contract) is cleared, pick the next ticket
from the board. For a `parallel-build` lane, create one
worktree/branch per ticket and run only one maker per worktree. For a serial
lane, finish and verify the earlier ticket before starting the next.

The maker reads the ticket, source docs, named files, and relevant failed
attempts before editing. It applies the smallest diff that satisfies the ticket,
updates actual touched files, runs the focused acceptance command, and moves the
ticket to `review`. It does not mark the ticket verified.

### 5. Verify With a Separate Checker

The checker independently reads the ticket and diff, re-runs the acceptance
command and the repo gate required by the ticket, checks scope against predicted
and actual touched files, and returns `PASS`, `REJECT`, or `NEEDS-DECISION`.

On `PASS`, move the ticket to `verified` or `done` according to the repo's
integration policy and record evidence. On `REJECT`, reopen the ticket, record
the failed approach in `agent-state/sprint/failed-attempts.md`, and do not retry
the same path blind. On `NEEDS-DECISION`, move the ticket to `blocked` and add
the decision to `decisions.md`.

A failing test is `REJECT` until the checker proves otherwise with evidence.
"Probably flaky CI" is a hypothesis, not a verdict: do not dismiss a failure,
re-run until it passes, or call a ticket green to make the sprint close on time.
Only the checker declares green, only on recorded passing evidence — never the
maker, and never on a clean compile alone.

### 6. Update the Board and Handoff

After every cycle, update:

- `board.md`: status counts, lane summary, next tickets.
- The ticket file: actual files, evidence, verifier result, commit/branch.
- `parallelism-map.md`: invalidations, lane changes, completed items.
- `handoff.md`: the exact next action for a cold restart.

If committing, commit code and sprint state together. Never leave committed code
without the ticket state that explains it.

## Analysis-Only Mode

If the user only asks what can run in parallel, do Phases 0 through 3 and stop.
Produce `parallelism-map.md` plus a concise lane table. Do not launch makers or
edit product code.

## Closeout

When the sprint is done or paused, write a closeout section in `handoff.md`:
completed tickets with commits, open tickets, blocked decisions, rejected
approaches, gates run, and plan drift found. If drift means the canonical plan is
now stale or contradictory, recommend `plan-prune` as follow-up rather than
solving it inside this skill.

## Known Pressure Rationalizations

Time pressure and "just go" instructions produce predictable dodges. Each of
these is a violation, not a shortcut:

| Rationalization | Required response |
|---|---|
| "Write sets look disjoint at a glance — different directories, so fire all makers in parallel; no need to trace imports." | Directory names are not a conflict graph. Run the audit: trace real imports, consumers, and shared state. No `parallel-build` without it. |
| "These two tickets are 'different areas' (cart vs checkout) — run them together and sort out any merge conflict later." | A foreseeable shared touch or producer/consumer dependency (e.g. a util wired into a consumer) is a conflict edge → `serial`. Never launch parallel planning to fix conflicts later, and never ignore the dependency chain. |
| "The maker that wrote this understands it best, so let it verify its own ticket — a separate checker is overkill under time pressure." | Maker ≠ checker, always. The author's familiarity is the bias, not the qualification. Pull in a separate checker every time. |
| "The lead said 'run to completion,' so auto-launch the next maker the instant one finishes — no need to pause at a launch gate." | A standing "go fast" authorizes a budget, not a gate bypass. Present the map, get the explicit go, and re-clear the gate on every map refresh. |
| "A ticket touched a shared file outside its write set, but it's one line and still compiles — let the morning's map stand." | Out-of-write-set touch is an invalidation trigger with no smallness exemption. Pause new launches and refresh the map before continuing. |
| "We're past the sprint-done marker but follow-ups surfaced and I have momentum — keep the loop spinning." | Stop at the marker. New work is new backlog: file tickets, then re-run audit and launch gate. Momentum is not approval. |
| "A test broke — probably flaky CI, not my change — re-run and call it green so the sprint closes on time." | A failure is `REJECT` until the checker proves flakiness with evidence. No re-run-to-green, no maker-declared green, no clean-compile green. |

## Common Mistakes

- Treating the board as a summary instead of the source of execution state.
- Launching parallel makers from intuition instead of the conflict graph.
- Forgetting to invalidate the parallelism map after real touched files differ
  from predicted files.
- Moving vague roadmap bullets straight to `ready`.
- Letting the maker verify its own ticket.
- Updating code but not the ticket state, leaving the next session to guess.
- Absorbing plan-prune work and turning the sprint board into another roadmap.
