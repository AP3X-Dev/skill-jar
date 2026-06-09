# Verification Gates, AGENTS.md, and What the Human Owns

This reference covers Phase 5 of the scaffolding process: the **hard stops** every cycle must clear before commit, the **`AGENTS.md`** default rules the loop-agent reads each cycle, and the **boundary** the developer never hands to the loop.

Everything inside a fenced block here is **Layer 2** — text that goes INTO the system, written in the imperative for the future loop-agent. You author it now; the loop-agent runs it later, cycle after cycle. Do not perform these steps yourself.

---

## 1. Verification gates (hard stops)

A gate is **a command that exits non-zero and STOPS the cycle.** It is not a vibe, not a self-grade, not "looks good." If a check cannot be expressed as a command with a 0/1 exit code (or an assertion that provably holds), it is not a gate — it's a hope, and hopes don't block bad commits.

This is the same discipline `optimization-loop` enforces with its Acceptance checks and no-regression ratchet: every claim of "done" is falsifiable or it doesn't count. Soft gates are the single most common way a loop ships plausible-but-wrong work.

### The gate set

Every cycle must clear ALL of these before the maker's work is committed. Each is stated as a falsifiable condition — phrased so a failure is unambiguous:

| # | Gate | Falsifiable condition (fails the cycle if…) |
|---|------|---------------------------------------------|
| 1 | **Tests pass** | the test command exits non-zero, OR reports 0 tests run, OR the suite is missing/errors before running |
| 2 | **Lint passes** | the lint command exits non-zero |
| 3 | **Typecheck passes** | the typecheck command exits non-zero (skip only if the repo has no type system) |
| 4 | **Build passes** | the build command exits non-zero (skip only if there is genuinely no build step) |
| 5 | **No unrelated files changed** | `git diff --name-only` lists a file outside the task's declared scope |
| 6 | **No secrets added** | the diff introduces a key, token, password, or `.env` value (a secret-scan command exits non-zero) |
| 7 | **No tests weakened** | a test was deleted, `.skip`/`xit`/`xdescribe`'d, commented out, or had its assertions loosened to make the suite green |
| 8 | **State updated** | `agent-state/loop-state.md` was not modified this cycle (the cycle left no restart trail) |
| 9 | **PR description carries verification evidence** | the PR/commit body has no recorded command output proving gates 1–4 ran (an empty "Verification" section fails) |

Gate 7 is non-negotiable and worth restating: **a genuinely-wrong test is a logged backlog item, never a silent edit.** If a correct fix breaks a test, the test is the suspect — verify which one encodes the right behaviour before touching either. Never revert a correct fix to appease a wrong test, and never delete a test to turn the suite green.

Gate 1's "0 tests run" clause matters: an empty or mis-targeted suite that exits 0 is a STOP-and-report, never a pass. A loop that gates on a suite running zero tests is gating on nothing.

**Scope the gates by cycle type.** Not every cycle writes code. Gate 8 (state updated) applies to **every** cycle — including a triage-only (Level 1) cycle whose only write is to `agent-state/`. Gates 1–7 apply to any cycle that changes code; gate 9 (PR carries evidence) applies only to cycles that open a PR (Level 2+), where the PR/commit body must carry the gate output. A triage-only cycle has no code diff and no PR, so it clears gate 8 alone — that is a complete, valid cycle, not a skipped gate.

### Make the gates host-real, then encode them

The gate set above is the *contract*. The *commands* are repo-specific — discover them in Phase 0 and confirm each one actually runs in this repo before you wire it. Record them once, in `agent-state/loop-state.md`, so every cycle (and every restarted agent) reads the same verification commands instead of guessing. A representative encoding the loop-agent runs:

```sh
# Layer 2 — the loop-agent's verification gate. Any non-zero exit STOPS the cycle.
set -e
<test-command>          # e.g. npm test  /  pytest -q  /  go test ./...
<lint-command>          # e.g. npm run lint  /  ruff check .  /  golangci-lint run
<typecheck-command>     # e.g. tsc --noEmit  /  mypy .   (omit if no type system)
<build-command>         # e.g. npm run build  /  cargo build --release   (omit if none)

# All diff gates below inspect the STAGED diff — `git add` this cycle's changes first,
# then run the gate, so every gate sees the same snapshot.

# scope gate: fail if any staged file is outside the declared task paths. The cycle's
# own state writes under agent-state/ are always allowed (every cycle updates state).
git diff --cached --name-only | grep -qvE '^(<declared-paths>|agent-state/.*)$' && { echo "GATE FAIL: unrelated files changed"; exit 1; }

# secret gate: fail if the staged diff adds a likely secret (use the repo's scanner if it has one)
git diff --cached | grep -nEi '(api[_-]?key|secret|password|token)[[:space:]]*[:=]' && { echo "GATE FAIL: possible secret"; exit 1; }

# state gate: fail if loop-state.md was not updated and staged this cycle
git diff --cached --name-only | grep -q '^agent-state/loop-state.md$' || { echo "GATE FAIL: state not updated"; exit 1; }
echo "ALL GATES GREEN"
```

`set -e` makes the first non-zero exit abort the script — that *is* the hard stop. Fill every `<placeholder>` with the command Phase 0 confirmed; do not ship a gate script with an unverified placeholder.

### Encode the gate as a host done-condition

Where the host supports a goal/done-condition primitive, bind the loop's continuation to the gate so the loop **cannot advance on an unverified cycle**. Give the gate to the host in its own form:

- **Claude Code** — `/goal` is a real command: it sets a completion condition that a separate evaluator model checks after every turn, and Claude keeps working until it holds (`/goal clear` cancels; works headless via `claude -p "/goal <condition>"`):
  > /goal the verification script printed `ALL GATES GREEN`, `git diff --cached --name-only` shows only files inside the declared task scope plus `agent-state/`, and `agent-state/loop-state.md` records the result — or stop after 20 turns
- **Codex** — `/goal` exists behind a feature flag (`codex features enable goals`); phrase it the same way: "Complete <the cycle> without stopping until <the gate condition holds>". It supports `pause`/`resume`/`clear` and stops on success, budget limit, or an unresolvable blocker.
- **Generic fallback** — when the host has no goal primitive, the runner wraps the cycle: it executes the gate script and only proceeds to commit/next-cycle on exit 0; any non-zero exit halts the loop and writes the failure to `agent-state/failed-attempts.md`.

A failed gate is not a quiet retry — it is a logged stop. Record the failing command and its output in `agent-state/failed-attempts.md` so the next cycle (or the human) sees what blocked, not just that something did.

> **(MemBerry)** — optional. When MemBerry is present, also store the gate failure as a session record so the *pattern* of failures accumulates across runs (`berry_store(... outcome: "failed", content: "gate <name> failed on <task>: <symptom>")`). The state files remain the required mechanism; if no MemBerry tools exist, skip this and rely on `failed-attempts.md` alone.

---

## 2. `AGENTS.md` template

Drop this at the repo root. It is the default rule set the loop-agent reads every cycle — host-neutral on purpose, so the same file governs the maker and the checker whether they run under Claude Code, Codex, or a generic runner. The body is Layer 2: imperative instructions for the agents that will run, not notes for the person scaffolding the loop.

```md
# AGENTS.md

Rules for any agent operating in this repository — maker, checker, or automation.
These are defaults. A task may add constraints; it may not relax these.

## General
- Prefer the smallest change that solves the task. No drive-by renames, reformatting, or restructuring.
- Never rewrite or reformat files unrelated to the task.
- Never delete, skip, or loosen a test to make a task pass. A wrong test is a logged backlog item, not a silent edit.
- Do not mark work complete without verification evidence (see Verification).
- Record every failed attempt in `agent-state/failed-attempts.md`: what was tried, the exact symptom, why it failed.
- Preserve the existing architecture and public contracts unless the task explicitly instructs otherwise. If a fix would change a public API, schema, config contract, or on-disk format, STOP and ask — do not guess.

## Code Changes
- Read a file before editing it. Understand the surrounding code; do not patch blind.
- For each file changed, be able to state in one line WHY it changed. If you can't, you changed too much.
- Keep commits focused — one task per commit. Do not bundle unrelated fixes.
- Add no new dependency (runtime or dev) without explicit approval. If a task seems to need one, stop and ask.

## Verification
- Before marking work complete, run — and show the output of — in this order:
  1. the linter
  2. the typecheck (skip only if the repo has no type system)
  3. the relevant tests (the suite must actually run and report a non-zero test count)
  4. the build (skip only if there is genuinely no build step)
- If any command cannot be run, do not silently skip it: state which command, and exactly why it could not run.
- A green suite that ran zero tests is a STOP-and-report, not a pass.
- Paste the verifying command output into the PR/commit description. "Tests pass" without evidence is not verification.

## State
- After every meaningful cycle, update `agent-state/loop-state.md` with the result and the next action.
- On completing a task, append it to `agent-state/completed.md` with its commit SHA.
- On a failed or abandoned attempt, append it to `agent-state/failed-attempts.md` with the symptom and cause.
- Commit code and state files together, in the same commit, so a restart never sees finished work that was never logged.
```

Adapt only the command names referenced under **Verification** to the repo's real toolchain (discovered in Phase 0). The rule bodies stay as written — they are the loop's safety floor, not suggestions. Keep the `agent-state/` paths exactly as the spine and `references/state-templates.md` define them.

---

## 3. What the developer still owns

Loop engineering moves the developer **up one level** — from prompting every step to designing the system that prompts, checks, and records. It does not remove their judgment. The loop can **discover** work, **draft** a change, **test** it against runnable gates, and **summarize** the result. The developer still decides **what ships.**

These stay with the human, every cycle, no matter how high the autonomy ladder climbs:

- **Architecture** — the loop fixes within the design; it does not get to redraw it. Structural decisions are human calls.
- **Review quality** — the checker gates correctness with evidence; the human still reads the diff that merges. Maker≠checker does not mean human≠nothing.
- **Merge decisions** — the loop opens the PR; the developer decides whether it lands. The merge gate is human by default.
- **Product judgment** — whether the change is the *right* change for the product is not something a verification command can exit 0 on.
- **Security boundaries** — what the loop may touch, what credentials it may see, what it may never modify. The loop operates inside a boundary the human draws.
- **Cost control** — how often the loop runs, how much compute it spends, when to throttle or stop. An unattended loop spends money; the human owns the budget.
- **Final accountability** — the loop has no accountability. Everything it ships is signed, in effect, by the developer who let it run.

The autonomy ladder grants the loop more of the *mechanical* work as it earns trust — discovery, then isolated implementation, then connectors, then semi-autonomous cycles. It never grants it the items above. When in doubt, the loop's default is the **When to Stop and Ask** posture: an expensive-to-reverse decision is escalated to the human, not guessed.

---

**Cross-reference:** the gate set here is the operational form of the Phase 5 hard stops and the "Before handoff — verify" checklist in `../SKILL.md`; the falsifiable-Acceptance and no-regression-ratchet discipline it mirrors lives in `../../optimization-loop/SKILL.md`. The `agent-state/` files these gates read and write are defined in `state-templates.md`; the worktree the cycle runs in is defined in `worktree-isolation.md`.
