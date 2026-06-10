# Designing the experiment harness

The harness is the half of the system the loop can NOT touch. Get it right
and the loop can run unattended all night; get it wrong and every number the
loop logs is noise. This guide covers the four definitions (objective,
budget, surface, frozen paths), the contract, and per-domain shapes.

## The contract

1. **One run command**, runnable from the repo root, e.g. `uv run train.py`,
   `python bench.py`, `npm run eval`.
2. **The budget is enforced INSIDE the harness** — a wall-clock timer, an
   iteration cap, an API-call cap, a token budget. Never rely on the agent
   to stop a run; the harness stops itself.
3. **Greppable metrics**, one per line, stable names:
   `val_bpb: 0.997900` / `accuracy: 0.8125` / `ops_per_sec: 1204231`.
   Print the soft constraint the same way (`memory_gb: 44.0`).
4. **Crashes are loud**: nonzero exit or no metric line. A run that fails
   silently but prints a number poisons the ledger.

## Choosing the objective

- ONE scalar, with a direction. If two numbers matter, either fold them into
  one formula inside the harness (then THAT formula is the objective and is
  frozen) or run two separate research runs.
- Prefer metrics that are budget-fair and config-independent. Karpathy uses
  bits-per-byte instead of per-token loss so vocab changes compare fairly —
  pick the variant of your metric that survives the mutations you expect.
- Soft constraints (memory, cost, latency) are recorded per run and given as
  guidance ("some growth acceptable for real gains, no blow-ups") — the
  keep/discard rule may veto on a blow-up, but never optimizes them.

## Choosing the budget

- Small enough for real throughput: a 5-minute budget ≈ 12 experiments/hour
  ≈ 100 experiments overnight. A 1-hour budget gets you 8 — barely a search.
- Big enough that the metric moves above the noise: if the signal needs 10
  minutes to appear, a 5-minute budget optimizes the wrong thing
  (fast-starters win over good-finishers).
- NEVER change the budget mid-run. It invalidates every prior ledger row.
  New budget = new run tag = new branch = new baseline.

## Choosing the mutable surface

ONE file when at all possible. It keeps diffs reviewable, resets clean, and
the agent's attention concentrated. If the experiment genuinely spans files
(prompt + few-shot examples), prefer merging them into one file over widening
the surface. Widen only after the ledger shows the surface is the bottleneck.

## Freezing the harness

- List frozen paths EXPLICITLY in `experiment-state.md` — "everything except
  the surface" is not auditable.
- Record the freeze commit SHA at scaffold time. The integrity gate is:
  `git diff --quiet <freeze commit> -- <frozen paths>` (exit 0 = intact).
- Data, eval sets, scorers, and metric-printing code are always frozen. If
  the eval is judged by an LLM, the judge prompt and model pin are frozen too.

## Noise floor

Run the baseline twice during setup. If the two numbers differ, the spread is
your noise floor: an "improvement" smaller than it is a coin flip, and the
keep rule should ignore it. ML training at fixed seed is near-deterministic
(floor ≈ 0); API-judged evals and wall-clock benchmarks are not. Record the
floor (or `0 (not measured)`) in `experiment-state.md`.

## Domain shapes

| Domain | Objective (direction) | Budget | Mutable surface | Frozen harness |
|---|---|---|---|---|
| LLM training (autoresearch) | `val_bpb` (↓) | 5 min wall-clock | `train.py` | `prepare.py`, data shards, tokenizer |
| Prompt optimization | eval-set `accuracy` (↑) | N eval calls or $X | `prompt.md` | eval set, scorer/judge, model pins, sampling params |
| Algorithm performance | `ops_per_sec` (↑) | fixed iterations on a fixed workload | the hot module | benchmark runner, workload generator, correctness check |
| Compression | `compressed_bytes` (↓) with round-trip check | fixed corpus | the compressor | corpus, round-trip verifier |
| Query tuning | `p95_ms` (↓) | fixed query set, N repetitions | the query / index DDL | dataset, runner, timing code |

Two non-negotiables visible in every row: the harness includes a
**correctness check** where "better" could mean "broken" (compression that
doesn't decompress, a fast kernel that's wrong), and the workload/eval-set is
**fixed** so runs compare.

## Worked example — Karpathy's autoresearch

The reference implementation of this whole pattern
([github.com/karpathy/autoresearch](https://github.com/karpathy/autoresearch)):

- **Harness:** `prepare.py` — data download, tokenizer, dataloader, and the
  ground-truth `evaluate_bpb` eval. Read-only by rule.
- **Surface:** `train.py` — the full GPT model, optimizer, training loop.
  Everything in it is fair game.
- **Budget:** exactly 5 minutes of training wall-clock, enforced inside the
  training loop, regardless of platform — so any architecture change competes
  on equal footing.
- **Objective:** `val_bpb` ↓ (bits per byte: vocab-independent, so tokenizer
  and architecture mutations compare fairly).
- **Ledger:** `results.tsv`, untracked, statuses keep/discard/crash.
- **Loop:** the agent commits an idea, trains 5 minutes, greps `val_bpb`,
  advances the branch on improvement, resets on regression — all night.

## Tuning for small budgets / small machines

When the full-size problem won't show signal inside the budget, shrink the
PROBLEM, not the discipline: narrower data (e.g. TinyStories instead of web
text), smaller vocab/sequence length/model depth, fewer eval tokens. The loop
finds the best configuration for the platform you give it — a small, honest
setup beats a big one that never finishes a run.

## Anti-patterns

- A metric computed by the mutable surface (the fox guarding the henhouse —
  move metric computation into the harness).
- "The agent will know not to edit the eval" — it won't, reliably. The
  integrity gate is cheap; run it every cycle.
- A budget enforced by the driver prompt ("stop after about 5 minutes") —
  prompts drift; timers don't.
- An eval set the loop can see and memorize answers from — keep held-out data
  out of the mutable surface's reach.
