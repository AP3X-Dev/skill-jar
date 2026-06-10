# auto-research skill — design

**Date:** 2026-06-09
**Status:** approved design, pre-implementation
**Reference:** Karpathy's autoresearch repo (local copy: `C:\Users\Guerr\Downloads\autoresearch-master\autoresearch-master`)

## What this is

A new skill at `development/auto-research/` — the jar's third specialized loop,
alongside `optimization-loop` and `bug-pipeline`, built on `loop-engineer`
conventions. It scaffolds a **Karpathy-style auto-research loop** into a target
repo: an agent autonomously runs fixed-budget experiments against a frozen
evaluation harness to optimize ONE scalar metric — hypothesize → mutate the
experiment surface → run → keep or discard by the metric → log → repeat
indefinitely.

The pattern generalizes the autoresearch repo (a nanochat-derived LLM training
speedrun: agent edits `train.py`, runs 5-minute trainings, chases lower
`val_bpb`) to **any domain with a runnable metric**: model training, prompt
optimization, algorithm performance, compression ratio, benchmark scores.

## Decisions made during brainstorming

| Decision | Choice | Rationale |
|---|---|---|
| Scope | Fully general | Any "optimize one number" setup, not just ML training. The autoresearch repo becomes the worked example. |
| Harness | Skill includes a harness-design phase | Most target repos lack a frozen eval + fixed-budget runner; building it is the skill's biggest value-add. Collapses to verification when one exists. |
| Handoff | Build everything, run the baseline, then **ask** before launching | Human-in-the-loop on spend. Never auto-launch; experiments cost real compute. |
| Shape | Standalone sibling skill, minimal scaffold | Separate trigger surface beats a mode inside optimization-loop (forked logic, doubled context tax, weakened routing). Full agent-state spine rejected: the pattern carries its own state. |

## Why not the full loop-engineer spine

The autoresearch pattern already contains its state, minimally:

- `results.tsv` **is** the ledger (completed work + failed attempts in one table)
- the **git branch** is the keep/discard memory (advance on improvement, reset on regression)
- the **driver prompt** is the per-cycle program (Karpathy's `program.md`)

We add exactly one new piece — a small `experiment-state.md` — so a cold
restart can resume (the original assumes one warm session). Laying down
`triage-inbox.md` / `completed.md` / `failed-attempts.md` / `decisions.md`
would duplicate what the ledger and branch already encode.

## Skill identity

- **Name:** `auto-research`
- **Path:** `development/auto-research/SKILL.md`
- **Description (routing, to be tuned at implementation):** Use when the user
  wants a Karpathy-style auto-research loop — an agent autonomously running
  fixed-budget experiments against a frozen evaluation harness to optimize ONE
  scalar metric: hypothesize → mutate → run → keep/discard by the metric → log
  → repeat indefinitely. Generalizes the autoresearch/nanochat pattern to any
  domain with a runnable metric (model training, prompt optimization,
  algorithm perf, compression, benchmarks). Builds the harness if missing,
  scaffolds the loop on loop-engineer conventions, runs the baseline, then
  OFFERS launch (never auto-launches). Triggers: "karpathy loop",
  "autoresearch", "auto-research loop", "overnight experiments", "optimize
  this metric autonomously". NOT for correctness/quality hardening
  (optimization-loop), defect repair (bug-pipeline), or non-experiment loops
  (loop-engineer).

## File structure

```
development/auto-research/
  SKILL.md                          # Layer 1 process + routing + adapted conventions + common mistakes
  references/driver-template.md     # full Layer 2 driver with <placeholders>
  references/harness-design.md      # metric/budget/frozen-harness design per domain;
                                    # autoresearch worked example; small-compute tuning tips
```

No `scripts/` — three small files don't justify a scaffolder, and
loop-engineer's `scaffold-loop.py` lays the wrong spine for this pattern.

## Layer 1 — the process the skill-runner walks

1. **Phase 0 (optional, MemBerry):** `berry_load` prior context; skip when the
   tools are absent. Same convention as siblings.
2. **Phase 1 — Define the experiment.** Four questions, answered with the
   user/repo:
   - **Objective:** exactly ONE scalar with direction (val_bpb ↓, tokens/sec ↑,
     accuracy ↑). Multi-metric objectives are a routing error → optimization-loop.
   - **Mutable surface:** ideally ONE file the loop may edit. Karpathy's
     strongest design choice — keeps diffs reviewable and reset semantics clean.
   - **Frozen harness:** eval/data/metric code declared read-only, listed by
     explicit path.
   - **Budget:** fixed wall-clock / iterations / cost per run so every
     experiment is comparable. Fixed budget also means the loop finds the best
     configuration *for this platform and budget*.
3. **Phase 2 — Build or verify the harness.** If missing, build it: one run
   command that (a) enforces the budget internally, (b) prints metrics
   greppably (`metric_name: value`, one per line), (c) exits nonzero on crash.
   Name soft constraints here too (memory, cost — "some increase acceptable
   for meaningful gains, no blow-ups"). If a harness exists, verify the
   contract instead of building.
4. **Phase 3 — Scaffold.**
   - Branch `research/<tag>` (tag from date, e.g. `jun9`); must not already exist.
   - Driver at `docs/prompts/<tag>-research-driver.md`, specialized from
     `references/driver-template.md`.
   - `results.tsv` ledger — header row only (untracked).
   - `experiment-state.md` (untracked).
   - Research-rules section appended to the target repo's `AGENTS.md` (committed).
5. **Phase 4 — Baseline run.** Run the unmodified code for real; row 1 of
   `results.tsv` is always `baseline`. Doubles as proof the harness contract
   holds — never hand off unproven (loop-engineer Phase 7 discipline).
6. **Phase 5 — Launch gate (human-in-the-loop).** Present: budget per
   experiment, estimated experiments/hour, trigger options (`/loop` in-session,
   local cron + headless CLI), cost implications. **Ask** whether to launch.
   Yes → wire the trigger and start the loop. No → hand off with exact launch
   instructions.

## Layer 2 — the driver (generalized program.md)

Imperative, addressed to the future loop-agent. One cycle:

1. **Orient.** Read `experiment-state.md`, the last ~20 rows of `results.tsv`,
   current branch/commit. Never load full history into context.
2. **Hypothesize.** ONE idea, informed by the ledger: combine near-misses,
   never repeat a discarded idea, escalate radicality when plateaued. The
   "think harder" rule: re-read in-scope files, papers referenced in code,
   combine previous winners — running out of ideas is not a stopping
   condition.
3. **Mutate.** Edit only the mutable surface. Commit with a message describing
   the experiment.
4. **Run.** `<run command> > run.log 2>&1` — never tee, never flood context.
   Kill at 2× budget → treat as crash.
5. **Extract.** Grep the metric pattern from the log. Empty → crash path: read
   the log tail; dumb fix (typo, import) → fix and re-run; fundamentally
   broken idea → log `crash` row, reset, move on.
6. **Integrity gate.** `git diff` over the frozen paths against the
   harness-freeze commit must be empty — the anti-reward-hacking check.
   Violated → reset, log, no exceptions.
7. **Log.** Append one TSV row:
   `commit  metric  soft_constraint  status  description`
   (tab-separated — commas break in descriptions; statuses `keep` / `discard`
   / `crash`; metric `0.000000` and constraint `0.0` on crash).
8. **Keep or discard.** The experiment commit already sits at the branch tip
   (step 3). Metric improved → keep it there and update current-best in
   `experiment-state.md`. Equal or worse → `git reset --hard` to the
   pre-experiment commit. **Simplicity criterion** as tiebreaker: equal result
   with less code = keep; tiny gain + ugly complexity = discard.
9. **Never stop.** No "should I continue?" mid-loop — the human may be asleep;
   the loop runs until interrupted. Rewinding to an earlier kept commit (to
   escape a dead end) is allowed but very sparingly.

## Scaffolded artifacts

### `experiment-state.md` (untracked, ~15 lines)

Run tag • objective + direction • run command • metric grep pattern • budget •
frozen paths + freeze-commit SHA • soft constraints • baseline value • current
best (value + commit) • status. This is the cold-restart anchor the original
pattern lacks.

### `results.tsv` (untracked)

Header: `commit	metric	soft_constraint	status	description`. The column
header for `metric` / `soft_constraint` is specialized at scaffold time to the
real names (e.g. `val_bpb`, `memory_gb`).

### `AGENTS.md` research rules (committed)

Frozen paths are read-only • never fabricate or edit existing ledger rows •
the metric command is ground truth — never modify what it measures or reports
• one experiment in flight at a time • no new dependencies without human
approval.

## Untracked-ledger decision (and its honest limitation)

`results.tsv` and `experiment-state.md` stay **untracked**, faithful to the
original: it is what makes `git reset --hard` discard semantics safe — the
ledger survives resets, and experiment commits contain only the code change.

Consequence, stated plainly in the SKILL.md: this loop is best run
**in-session (`/loop`) or via local cron** on the machine that holds the
working tree. Cloud Routines clone fresh from the default branch and would see
neither ledger nor state. This differs from loop-engineer's
commit-state-with-code rule; the deviation is deliberate and documented.

## Maker≠checker, adapted honestly

The jar's rule exists so no agent grades its own work. In this loop the grader
is the **frozen harness** — an objective, deterministic command whose verdict
the agent cannot argue with — plus the frozen-paths diff gate proving the
harness wasn't touched. A second verifier agent would add cost without rigor
when the verdict is a number printed by frozen code. The SKILL.md states this
adaptation explicitly so the deviation from the sibling skills reads as
designed, not forgotten.

## Cross-routing edits (existing files)

- `development/loop-engineer/SKILL.md` — third bullet under "Specialized loops
  this skill can scaffold."
- `development/optimization-loop/SKILL.md` — NOT-for addition:
  metric-experimentation on a frozen harness → auto-research.
- `README.md` — table row under development; update the skill count line.
- `skills.json` — regenerate via `scripts/gen-index.py`.

## Common mistakes (each earned from the reference repo)

- Mutable surface too broad (multi-file experiments → unreviewable diffs,
  messy resets).
- Metric not greppable from the log (extraction becomes guesswork).
- Comparing runs across different budgets (numbers stop meaning anything).
- Letting the agent "fix" the eval (reward hacking; the integrity gate exists
  for this).
- Committing the ledger (breaks reset semantics).
- Multi-metric objectives (wrong skill — optimization-loop).
- Stopping mid-loop to ask permission (the launch gate was the permission).

## Verification (definition of done for implementation)

- `python scripts/audit-jar.py` exits 0 (frontmatter parses, description
  carries triggers, name matches directory, links resolve).
- README and `skills.json` updated and consistent.
- All three skill files written; cross-routing edits in place.
- Committed locally on a branch; never pushed (human's call, per AGENTS.md).

## Out of scope

- A scaffolder script.
- Cloud-Routine support for the loop (untracked ledger makes it a poor fit;
  documented limitation, not a feature gap to close).
- Multi-objective or Pareto-front experimentation.
- Parallel experiment lanes (multiple GPUs/branches at once) — possible future
  extension, not v1.
