---
name: simplify-loop
description: "Autonomous loop that safely collapses LIVE, over-engineered code — one behavior-identity-gated cluster per cycle. A Scout files only structurally-provable single-use over-engineering (forwarding wrappers, single-caller indirection, config read at one constant, a factory with one product and no public/DI/plugin binding); a Collapser writes a characterization test first, then inlines it proving output byte-identical; an independent Validator re-checks the test wasn't loosened and a complexity/LOC ratchet fell. Builds and dry-runs, then OFFERS launch — never auto-collapses. Use when working code has accreted speculative abstraction and needless indirection to reduce continuously and safely. Requires a runnable test suite; ast-grep/FUGAZI sharpen detection. NOT for a deliberate seam or shallow-module reshape (use improve-architecture, human-owned), behavior-CHANGING cleanup or broad hardening (use optimization-loop), unreachable/dead code (use dead-code-reaper), or a defect (use diagnose-loop/bug-pipeline)."
---

# Simplify Loop

A specialized [loop-engineer](../loop-engineer/SKILL.md) loop that makes *reducing over-engineering in live code* safe to run unattended. It is the reduce-**live**-complexity counterpart to [dead-code-reaper](../dead-code-reaper/SKILL.md)'s reduce-**dead**-code loop: same three-role spine, same one-cluster-per-cycle discipline, same maker≠checker split — but the oracle is different. dead-code-reaper proves code is **unreachable** (a `trace` to zero importers) before deleting it; this loop proves a collapse is **behavior-identical** (a characterization test that still passes un-loosened, and byte-identical output) before shipping it. The code here is reached and working; the only license to touch it is proof that the observable behavior did not move.

**Output:** a running simplify loop in the target repo — a ledger, three role agents, a per-cycle driver — plus one verified cycle. Then it **offers** launch; it never auto-collapses. Collapsing live code is expensive to reverse, so the human owns the go.

## The one thing that makes this safe

This loop touches **only the mechanical, structurally-provable single-use subset** of over-engineering — the cases where "there is exactly one of it" is provable from the code's structure, not a matter of taste:

- **forwarding / delegating wrappers** — a function or method whose whole body forwards to one other with no added logic.
- **single-caller indirection** — a layer, adapter, or helper with exactly one caller. Inline it into that caller.
- **config-read-at-one-constant** — a config key / flag / option that is only ever set to one literal value. Inline the literal.
- **factory / abstraction with one product** — a factory, interface, or abstract base with exactly **one** implementation **and** zero external, plugin, DI, registry, or public binding.
- **hand-rolled stdlib** — a few lines re-implementing something the standard library or platform ships, where the replacement is behavior-for-behavior identical.

Everything that requires a **judgment call about whether a shape is a deliberate seam** is out of scope and routes to [improve-architecture](../improve-architecture/SKILL.md) (human-owned) — see When NOT to Use and Safety. This is the line between "speculative generality proven single-use by structure" (safe to automate, near dead-code-reaper's risk profile) and "a shallow module a human might reshape differently" (improve-architecture's turf). The loop never crosses it.

## When to Use

- Working code has accreted speculative abstraction — one-implementation factories, wrappers that only delegate, layers with a single caller, config nobody varies — and you want it reduced *continuously and safely*, one proven collapse at a time, in a reviewable ledger.
- Every collapse must be backed by a behavior-identity proof and a green suite, not a reviewer's taste.

[arch-drift-watch](../arch-drift-watch/SKILL.md) is the upstream detector whose `complexity` / `dupes` drift can route the *mechanical* single-use cases here; its structural-judgment findings go to improve-architecture instead.

## When NOT to Use

- **The shape might be a deliberate seam** — a public export, a registry/DI/plugin point, a documented extension, an interface kept for a second implementation that's coming. That is a direction call a human owns → **improve-architecture**. When in doubt, it is a seam.
- **A shallow module a human might reshape** (deepening, moving behavior behind a better interface) — that is structural judgment, not a mechanical collapse → **improve-architecture**.
- **The cleanup would change behavior** — tightening a bound, fixing a bug, hooking up a dead wire, adding validation. Any behavior change is out of scope here (the whole gate is byte-identity) → **optimization-loop** (metric-ratchet hardening) or **bug-pipeline** / **diagnose-loop** (defects).
- **The code is unreachable / dead** — an orphan file, an unused export, a dead dep. That is removal, not collapse → **dead-code-reaper**.
- **No test suite.** The behavior-identity oracle *is* the test suite. Without a runnable gate, "behavior unchanged" is a rumor; do not run this loop.
- **One obvious one-caller wrapper** — just inline it and run the tests. The loop is for a *continuous* stream, not a single symbol.

## What it needs

- **Required: a runnable test suite** — the behavior oracle. The loop re-runs it every cycle and the collapse must leave it green with assertions intact.
- **Recommended: a structural matcher** — [ast-grep](https://ast-grep.github.io/) for the single-use patterns (JS/TS/TSX and more), and/or [FUGAZI](https://github.com/AP3X-Dev/FUGAZI) (`fugazi` / `fugazi-mcp`) for `complexity` / `cognitive-complexity` / `dupes` signals about live code. Detection is *sharper* with these; it is not gated on them — a Scout can hand-find the mechanical patterns with grep and a read.

## The three roles

| Role | Job | Writes | Never |
|---|---|---|---|
| **Scout** (producer) | Find single-use over-engineering read-only; for each, prove single-use is *structural* (exactly one caller/product/value, no public/DI/plugin/registry binding); file high-confidence clusters with the pattern + `file:line` + the single-use evidence | The ledger only | Collapses code; files a candidate whose single-use rests on judgment, or that could be a seam |
| **Collapser** (maker) | Take ONE `pending` cluster; **write a characterization test first** over its observable behavior and confirm it green; inline/collapse with the smallest diff in a worktree; prove output byte-identical; run the repo gate | Code + the ledger | Collapses two clusters; loosens/deletes a test; collapses a shape that could be a seam; changes behavior |
| **Validator** (checker, different model) | Re-run the gate (suite + build + typecheck green); confirm the characterization test was **not loosened** and before/after output is **identical**; re-measure the complexity/LOC ratchet; inspect the diff for smuggled behavior change; promote `verified` or reopen | The ledger + failed-attempts | Collapses anything itself; approves without re-running the gate and confirming byte-identity |

Run the Validator on a **different model/provider** than the Collapser where the host allows — a collapse that "looks behavior-preserving" to one brain is exactly what the other should catch.

## The ledger — `SIMPLIFICATION_LEDGER.md`

Shared state, default `agent-state/SIMPLIFICATION_LEDGER.md`. Statuses change; rows are never deleted (a reopened collapse is a lesson, not garbage).

```md
# SIMPLIFICATION_LEDGER.md

## Meta
| Field | Value |
|---|---|
| Last Scout Scan | <timestamp> |
| Complexity baseline (cyclomatic + cognitive) | <n> |
| Clusters collapsed / LOC removed / clusters verified | <n> / <n> / <n> |

## Candidates

### SIMP-1 — <one-line: the over-engineering>
- **Pattern:** forwarding-wrapper | single-caller-indirection | config-at-one-constant | factory-for-one | hand-rolled-stdlib
- **Location:** <file:line(s)>
- **Single-use proof:** <exactly one caller/product/value; grep/ast-grep evidence; and: no public export / DI / plugin / registry / serialization binding>
- **Behavior oracle:** <the characterization test that pins current output>   <!-- set by Collapser -->
- **Status:** pending → collapsed → verified  (or: reopened | blocked)
- **Collapser notes:** <what was inlined + byte-identity evidence>            <!-- set by Collapser -->
- **Validator notes:** <commands run + ratchet before→after + verdict>        <!-- set by Validator -->

## Scan Notes
<one entry per Scout sweep: what was found, what was filtered as a possible seam
and why — a sweep that files nothing is still a valid cycle>
```

**Status flow:** `pending` (Scout) → `collapsed` (Collapser) → `verified` (Validator), or `reopened` (Validator, logged to failed-attempts), or `blocked` (a possible seam — a human / improve-architecture decides).

## Discovery recipe

The Scout's read-only sweep. Exact matchers, the single-use pattern table, and the behavior-identity oracle contract live in [references/simplify-kit.md](references/simplify-kit.md); the shape:

1. **Scan** for the mechanical patterns — ast-grep for forwarding wrappers / one-product factories / one-caller helpers; grep for a config key's set-sites; `fugazi complexity`/`dupes` for hotspots to read. 
2. **Prove single-use is structural,** not taste: exactly one caller (`grep`/`ast-grep`/`fugazi` callers = 1), or exactly one product, or one literal value — *after* accounting for dynamic and out-of-repo binding.
3. **Filter possible seams:** public API, framework-registered points, DI/reflection/string-dispatch, registries, serialization shapes, anything a second implementation is plausibly coming for. A shape that *could* be a seam is **not** provably single-use → file it `blocked` (route to improve-architecture), never `pending`.
4. **File** at most a few high-confidence clusters with the single-use proof attached.

## The cycle (driver outline)

One cluster per cycle. Built on loop-engineer's spine; the collapse shape:

1. **Preflight** — `git status` clean; read the ledger and loop state; record the complexity baseline if not set.
2. **Discovery** — skip if `pending` candidates remain; else run the Scout for one sweep.
3. **Planning** — pick one `pending` cluster (prefer the lowest-risk pattern: forwarding-wrapper / config-at-one-constant before factory-for-one); check failed-attempts first.
4. **Execution** — the Collapser **writes the characterization test first** (live code rarely has one), confirms it green, then inlines the cluster in a worktree and confirms output byte-identical.
5. **Verification** — the Validator re-runs the gate, confirms the test wasn't loosened and output is identical, re-measures the ratchet, and promotes or reopens.
6. **State update** — ledger reflects the status; commit code and ledger **together** (`simplify(SIMP-N): <what>`).

**The ratchet:** total complexity (cyclomatic + cognitive), indirection/abstraction depth, and abstraction/interface/file count must be **≤** baseline and LOC **lower**, with the **full** suite, build, and typecheck green **and behavior-identity holding** (characterization tests green with assertions intact, before/after output identical). "Full" means the same gate the repo runs in CI. A collapse that raises any complexity metric, or that changes any output, is a ratchet break — **reject and reopen**, regardless of the gate's exit code (a green build that changed behavior means it wasn't a behavior-preserving collapse). Floors only advance.

## Safety

- **Behavior-IDENTITY, not just green.** The gate exiting 0 is necessary but not sufficient — a collapse can pass the suite while quietly changing an output no test pinned. The proof is a characterization test the Collapser writes over the cluster's observable behavior *before* touching it, plus a before/after output comparison. Green-but-different is a **reject**.
- **Write the test first — and never loosen it.** Live over-engineered code usually has no characterization test; the Collapser writes one, confirms it passes against the *current* code, then collapses. Weakening, skipping, or deleting that test to make a collapse pass is the exact failure this loop exists to prevent. The Validator independently confirms the test was not loosened.
- **A possible seam is not provably single-use → blocked, and it is yours to defend.** A single-implementation interface, a one-product factory, a config flag — any of these can be a *deliberate* extension point: a public export, a registry (`handlers[name]`), a DI binding, a plugin surface, an interface awaiting a second implementation. "There's only one today" does not make it mechanical. If a shape *could* be a seam, block it and route it to improve-architecture; the cost of collapsing a real seam is yours, not the author's. This mirrors the rule: never silently drop a supported extension point.
- **Judgment belongs to improve-architecture.** This loop does not decide module boundaries, does not deepen shallow modules, does not pick which abstraction "should" exist. Those are direction calls a human owns. The loop only removes an abstraction whose single-use is *provable from structure*. When the choice is "which shape is better," it is out of scope — file it for improve-architecture and move on.
- **Behavior changes belong elsewhere.** If collapsing tempts you to also fix a bug, tighten a bound, or wire something up — stop. That is a behavior change, out of scope here (it breaks byte-identity by design). File it to optimization-loop or bug-pipeline. One collapse does one thing: remove mechanism, keep behavior.
- **One cluster per cycle — deadlines do not relax this.** Batched collapses make the Validator's byte-identity check ambiguous and rollbacks expensive. A freeze is a reason to be *more* careful, not to inline 20 wrappers in one commit.

### Known pressure rationalizations

A fresh agent under deadline pressure reaches for these. Each is wrong here; the required response is the gate.

| Rationalization (the dodge) | Required response |
|---|---|
| "The suite is green after inlining, so behavior is obviously preserved — I don't need to write a characterization test." | Green ≠ identical. The existing suite may not pin the output this abstraction produced. Write the characterization test over the observable behavior first, confirm it against current code, then collapse. Green-but-different is a reject. |
| "This interface has one implementation, so it's a YAGNI abstraction — inline it." | One implementation today is not proof it's not a seam. A public export, DI binding, registry entry, or plugin point is single-use *now* and load-bearing anyway. Could-be-a-seam → `blocked` → improve-architecture, not a `pending` collapse. |
| "While I'm inlining this wrapper I'll also fix the off-by-one I noticed — same area, one diff." | Out of scope. A collapse is behavior-identical by definition; a bug fix is a behavior change. File the off-by-one to bug-pipeline/diagnose-loop. The collapse must leave output byte-identical or it isn't this loop's work. |
| "The characterization test is failing after collapse on one weird input — I'll relax that assertion, the case is contrived." | Relaxing the assertion is loosening the test to hide a behavior change — banned. A failing characterization test means the collapse was *not* behavior-preserving. Revert, log to failed-attempts, stop. |
| "The config key is only set to `true` anywhere I can see, so I'll inline `true` and delete the flag." | "Anywhere I can see" must include dynamic/out-of-repo set-sites: env overrides, config files, feature-flag services, other repos. Prove the single literal across all binding, or block it. |
| "arch-drift-watch flagged this as complex — that's my signal to refactor the module shape here." | This loop does not reshape modules. A complexity finding is a *read-here* signal; if the fix is a structural deepening, that's improve-architecture (human-owned), not a mechanical collapse. Only collapse provable single-use. |
| "Batch all the one-line forwarding wrappers into one 'inline delegations' commit — they're trivial." | One cluster per cycle, one commit per cluster. Each collapse gets its own characterization test and byte-identity check; batching makes a regression un-attributable and rollback expensive. |

## Build, then offer launch

Scaffold via [loop-engineer](../loop-engineer/SKILL.md) (state spine, `AGENTS.md`, driver — `scaffold-loop.py` ships in `../loop-engineer/scripts/` in your skill-jar checkout), drop the three agents (templates in [references/simplify-kit.md](references/simplify-kit.md)), pin the gate, and **dry-run exactly one cycle**. Then stop and **offer** the human launch — a scheduled `/loop` or a cron cold-start. Do not auto-launch a loop that rewrites live code; the spend and the risk are the human's call. Start at autonomy Level 2: the loop commits locally; a human reviews diffs and pushes.

## Generated agents

Copy-ready generated agents live in [../agents/README.md](../agents/README.md) and are sourced from [../agents/manifest.json](../agents/manifest.json). Install only the roles needed for the active simplify run: `simplify-loop-scout`, `simplify-loop-collapser`, `simplify-loop-validator`.

## Common Mistakes

- **Collapsing on a green suite without pinning behavior.** The existing tests may not cover the output the abstraction produced. Write the characterization test first; byte-identity is the proof, not the suite's exit code.
- **Collapsing a seam.** Deleting a one-implementation interface that was a deliberate extension point is the expensive mistake. Could-be-a-seam → block it and ask / route to improve-architecture.
- **Smuggling a behavior change into a "simplification."** A tightened bound or a bug fix inside a collapse breaks byte-identity and hides a real change in a cleanup diff. Keep them separate.
- **Reshaping modules.** Deciding a better boundary is improve-architecture's human-owned job; this loop only removes provably single-use mechanism.
- **Batching collapses.** One cluster per cycle keeps each diff attributable and each rollback cheap.

---

*A loop built on [loop-engineer](../loop-engineer/SKILL.md) conventions, in the same shape as [dead-code-reaper](../dead-code-reaper/SKILL.md) — three roles, a shared ledger, a runnable gate, maker≠checker — but specialized for behavior-identity-gated collapse of provably single-use over-engineering. Its sibling boundary: [dead-code-reaper](../dead-code-reaper/SKILL.md) removes what's unreachable, [improve-architecture](../improve-architecture/SKILL.md) reshapes what a human decides to, [optimization-loop](../optimization-loop/SKILL.md) changes behavior to move a metric — this loop keeps behavior byte-identical and only removes mechanism.*
