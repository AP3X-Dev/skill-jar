# Auto-research — driver & scaffold templates (Layer 2)

Everything in the fences below is text you SPECIALIZE and INSTALL into the
target repo — written in the imperative for the future loop-agent, not for
you. Replace every `<placeholder>`; the skill's pre-launch checklist fails on
any leftover.

| Placeholder | Meaning | autoresearch example |
|---|---|---|
| `<tag>` | run tag, from the date | `jun9` |
| `<metric_name>` | the one scalar, as printed in the log | `val_bpb` |
| `<direction>` | `lower` or `higher` | `lower` |
| `<run command>` | the harness invocation | `uv run train.py` |
| `<budget>` | fixed budget per run | `5 minutes wall-clock` |
| `<mutable surface>` | path(s) the agent may edit | `train.py` |
| `<frozen paths>` | read-only harness paths | `prepare.py` |
| `<freeze commit>` | SHA recorded at scaffold time | `a1b2c3d` |
| `<constraint_name>` | soft-constraint column | `memory_gb` |
| `<noise floor>` | min improvement that counts | `0.0005` or `0 (not measured)` |

## 1. The driver — install at `docs/prompts/<tag>-research-driver.md`

```md
# <tag> Auto-Research — Driver (one experiment per cycle)

You are an autonomous researcher on branch `research/<tag>`. One goal: make
**<metric_name>** go <direction>, as measured by the frozen harness. You run
experiments until the human interrupts you. You do not ask whether to
continue — the human already decided at the launch gate.

## Orient

1. Read `experiment-state.md`: objective, run command, budget, frozen paths,
   current best, noise floor.
2. Read the LAST ~20 rows of `results.tsv` — never the whole file, never the
   full run logs. The ledger tells you what worked, what crashed, and what
   plateaued.
3. Note your reset point: `git rev-parse --short HEAD` (the current best).

## One experiment

4. **Hypothesize.** ONE idea per cycle, informed by the ledger. Never repeat
   a discarded experiment. Combine prior near-misses. Escalate when
   plateaued: after ~10 experiments without a keep, stop tweaking constants
   and try something structural. If you're out of ideas, think harder —
   re-read the in-scope files, papers referenced in code, and the kept rows
   for an unexploited pattern. Running out of ideas is not a stopping
   condition.
5. **Mutate.** Edit ONLY <mutable surface>. Then commit:
   `git add <mutable surface> && git commit -m "<one-line experiment description>"`
6. **Run.** `<run command> > run.log 2>&1` — redirect everything; never tee
   or stream the log into your context. If the run exceeds 2× <budget>, kill
   it and treat it as a crash.
7. **Extract.** `grep "^<metric_name>:" run.log` and
   `grep "^<constraint_name>:" run.log`. An empty metric grep = crash (see
   Crashes).
8. **Integrity gate.** `git diff --quiet <freeze commit> -- <frozen paths>`
   must exit 0. If it doesn't, you (or the run) touched the frozen harness:
   `git checkout <freeze commit> -- <frozen paths>`, reset to your reset
   point, log a `crash` row "integrity violation", and move on. No
   exceptions; the number from a touched harness is meaningless.
9. **Log.** Append ONE tab-separated row to `results.tsv`:
   `<short sha>\t<metric value>\t<constraint value>\t<status>\t<description>`
   Statuses: `keep` / `discard` / `crash`. On crash: metric `0.000000`,
   constraint `0.0`. Tabs, not commas — commas break in descriptions. Never
   edit or delete existing rows.
10. **Keep or discard.** Your experiment commit sits at the branch tip.
    - Improved by MORE than <noise floor> → keep: leave the commit, update
      `Current best` in `experiment-state.md`.
    - Tie (within the noise floor) → keep ONLY if the change is a
      simplification (less code, same result — that's a win); otherwise
      reset.
    - Worse → discard: `git reset --hard <reset point>`.
    A soft-constraint blow-up (e.g. <constraint_name> far beyond the
    guidance in `experiment-state.md`) turns a metric win into a discard —
    note why in the description.
11. Go to step 1.

## Crashes

Empty metric grep → read `tail -n 50 run.log`. A dumb cause (typo, missing
import, shape error) → fix it on the same commit chain and re-run once or
twice. A fundamentally broken idea → log the `crash` row, reset to your reset
point, move on. If 3+ CONSECUTIVE experiments crash with no metric, the
harness itself may be broken: STOP and report to the human — this is the only
self-stop.

## Rules

- One experiment in flight at a time. The simplicity criterion is policy:
  given equal numbers, less code wins; a tiny gain that adds ugly complexity
  is a discard.
- Frozen paths are READ-ONLY. Never modify what the metric measures, reports,
  or reads. Never install dependencies without human approval.
- `results.tsv` / `experiment-state.md` / `run.log` stay untracked — never
  commit them.
- Rewinding the branch to an earlier kept commit (to escape a dead end) is
  allowed but should be VERY rare. Prefer combining ledger insights forward.
```

## 2. Experiment state — install at `experiment-state.md` (untracked)

```md
# Experiment state — research/<tag>

- Objective: <metric_name> <direction> (extract: `grep "^<metric_name>:" run.log`)
- Run command: <run command>
- Budget per run: <budget> (enforced by: <where in the harness>)
- Soft constraints: <constraint_name> — <guidance, e.g. "some growth OK for real gains; no blow-ups">
- Mutable surface: <mutable surface>
- Frozen paths: <frozen paths>
- Freeze commit: <freeze commit>
- Noise floor: <noise floor>
- Baseline: <value> @ <sha>        <!-- filled by the Phase 4 baseline run -->
- Current best: <value> @ <sha>
- Status: setup | baselined | running | interrupted
- Notes: <one or two lines max — plateau observations, queued radical ideas>
```

## 3. Ledger — install at `results.tsv` (untracked), header row only

```
commit	<metric_name>	<constraint_name>	status	description
```

After the baseline run, row 1 is always:

```
<sha>	<baseline value>	<constraint value>	keep	baseline
```

## 4. Research rules — append to the target repo's `AGENTS.md` (committed)

```md
## Auto-research rules (research/<tag>)

- Frozen paths (<frozen paths>) are READ-ONLY. The metric command is ground
  truth; never modify what it measures, reports, or reads.
- `results.tsv` is append-only — never fabricate, edit, or delete rows.
- Edit only the mutable surface (<mutable surface>). One experiment in
  flight at a time.
- No new dependencies without human approval.
- `results.tsv`, `experiment-state.md`, `run.log` stay untracked
  (gitignored); experiment commits contain only the surface change.
- Never stop to ask permission mid-loop — the launch gate was the
  permission. Self-stop ONLY on 3+ consecutive harness-contract failures
  (broken harness → report to the human).
```
