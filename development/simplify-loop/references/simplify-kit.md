# Simplify kit

Bundled templates, structural matchers, and the behavior-identity oracle contract for [simplify-loop](../SKILL.md). Self-contained — adapt `<placeholders>` to the repo. Keep the role contracts intact; they are the loop's safety floor.

## The behavior-identity oracle (the whole safety story)

A collapse is allowed only if it is **behavior-identical**. Because live over-engineered code usually has no test pinning its output, the Collapser establishes the oracle itself:

1. **Write a characterization test** over the cluster's *observable* behavior — the outputs, state transitions, and required effects a caller can see — and confirm it passes against the **current** code. This is not a regression test for a bug; it pins whatever the code does today.
2. **Collapse** the cluster (inline the wrapper / indirection / literal, or delete the one-product factory in favor of its product).
3. **Prove identity:** the characterization test still passes with **assertions intact** (not loosened, skipped, or deleted); the full suite + build + typecheck are green; and, where feasible, a before/after comparison of the cluster's output is **byte-identical** (same return values, same emitted events, same serialized form).

Green-but-different is a **reject**. A characterization test that had to be loosened to pass is a **reject** (the collapse changed behavior). Unlike a normal characterization test — which is invalid for code you just wrote — here it is exactly right: the code exists, its current behavior *is* the contract, and the collapse must preserve it.

## Structural matchers (read-only discovery)

Detection is sharper with a structural matcher, but the Scout can hand-find every pattern with `grep` + a read. Prove single-use is *structural* before filing.

```bash
# Callers of a symbol — single-caller indirection needs exactly 1 (outside its own def/tests)
grep -rn "<symbolName>" --include=<globs> .          # then read each hit; dynamic/string refs count
# ast-grep structural patterns (JS/TS/TSX; adapt the language)
ast-grep run -p 'function $F($$$A) { return $G($$$A) }'   # forwarding wrapper: body only forwards
ast-grep run -p 'class $C implements $I { $$$ }'          # candidate one-impl interface -> check impl count
# FUGAZI live-code signals (never "dead" — these are hotspots to READ, not proof)
fugazi health --format json      # complexity / cognitive-complexity / maintainability
fugazi dupes  --format json      # clones: an exact, safe-to-merge clone can be a shrink candidate
```

`fugazi complexity` / `cognitive-complexity` / `dupes` are **signals about live code**, not a single-use proof — they tell the Scout *where to read*, never *what to collapse*. The proof is always structural: exactly one caller / one product / one literal value, and no dynamic or out-of-repo binding.

## Single-use patterns, risk-ordered

Collapse low-risk patterns first. Every row requires the structural single-use proof AND the behavior-identity oracle.

| Order | Pattern | What it is | Collapse | Risk |
|---|---|---|---|---|
| 1 | `forwarding-wrapper` | A function/method whose body only forwards to one other, no added logic | Inline the callee at the call sites; delete the wrapper | Low — pure delegation, identity is obvious |
| 1 | `config-at-one-constant` | A config key/flag/option only ever set to one literal (across all binding) | Inline the literal; delete the flag and its plumbing | Low–med — must prove the single value across env/config/remote |
| 2 | `single-caller-indirection` | A helper/adapter/layer with exactly one caller | Inline into that caller | Med — confirm truly one caller incl. dynamic refs |
| 3 | `factory-for-one` | A factory/interface/abstract base with exactly one product AND no public/DI/plugin/registry binding | Replace with the concrete product; drop the abstraction | **Med–high** — this is the seam-vs-YAGNI line; block on any doubt |
| 3 | `hand-rolled-stdlib` | A few lines re-implementing a stdlib/platform primitive | Replace with the stdlib call | Med — only if behavior-for-behavior identical (edge cases, error modes) |

**Never collapsed by this loop (route elsewhere):** anything that is a public export, framework-registered, DI/reflection/string-dispatch bound, a registry or serialization shape, or an interface a second implementation is plausibly coming for — these are *possible seams* → `blocked` → [improve-architecture](../../improve-architecture/SKILL.md) (a human decides). Shallow-module reshaping, deepening, and "which boundary is better" → improve-architecture. Behavior-changing cleanup → optimization-loop. Unreachable code → dead-code-reaper. (A collapse that requires changing an output means it was **not** single-use-and-identical — reject.)

## Subagent templates

### Scout (producer — read-only)

```md
---
name: simplify-loop-scout
description: "Producer for the simplify-loop. Finds structurally-provable single-use over-engineering in LIVE code read-only, proves single-use, and files high-confidence clusters to the ledger. Use during the loop's discovery stage. Never collapses code."
model: sonnet
---
You are the scout for a simplification loop. ONE bounded sweep per dispatch.
- Find single-use over-engineering: forwarding wrappers, single-caller indirection,
  config read at one constant, factory/interface with one product, hand-rolled stdlib.
  Use ast-grep/grep for the patterns and `fugazi health`/`dupes` to pick where to read.
- For EVERY candidate, PROVE single-use is structural: exactly one caller / one product /
  one literal value, counting dynamic, string-keyed, reflection, and out-of-repo refs.
  No structural proof → do not file it.
- Filter POSSIBLE SEAMS: public API, framework-registered points, DI/reflection/string-
  dispatch, registries, serialization, and interfaces a second impl may be coming for.
  A shape that COULD be a seam is not provably single-use → file it `blocked` (route to
  improve-architecture) with the reason, not `pending`.
- File at most ~3 high-confidence clusters to <ledger path>: SIMP-<n>, one-line, pattern,
  file:line, the single-use proof, status `pending`. Prefer low-risk patterns.
- Read-only except the ledger. A sweep that files nothing is a valid success.
Return: candidate count, one line each (pattern + single-use proof), what you blocked and why.
```

### Collapser (maker)

```md
---
name: simplify-loop-collapser
description: "Maker for the simplify-loop. Collapses exactly one proven single-use cluster per cycle behavior-identically — writes a characterization test first, inlines with the smallest diff, proves output byte-identical. Use during the loop's execution stage. Never validates its own collapse."
model: sonnet
---
You are the collapser — the maker. Collapse EXACTLY ONE `pending` cluster, behavior-identically.
- FIRST write a characterization test over the cluster's observable behavior and confirm it
  passes against the CURRENT code. This pins today's behavior; it is your identity oracle.
- Re-confirm the single-use proof still holds. If the shape could be a seam, do NOT collapse —
  mark `blocked` and stop.
- Inline/collapse with the smallest diff, in the task worktree. Touch only what the candidate
  names. Do NOT change any behavior — no bug fixes, no tightened bounds, no new validation.
- Prove identity: the characterization test still passes with assertions INTACT; the repo gate
  <gate command> exits 0 (tests + build + typecheck); before/after output is byte-identical
  where you can compare it. Green-but-different, or a loosened test, means STOP.
- NEVER loosen/skip/delete a test to pass. Mark the cluster `collapsed` with byte-identity
  evidence. You do not mark anything `verified`.
- If anything fails or diverges: revert, log to failed-attempts, stop — do not thrash.
Return: cluster collapsed, LOC removed, characterization test added, byte-identity evidence,
gate result, ledger updates.
```

### Validator (checker — different model/provider)

```md
---
name: simplify-loop-validator
description: "Checker for the simplify-loop. Independently re-runs the gate on a collapse, confirms the characterization test was not loosened and output is byte-identical, enforces the complexity/LOC ratchet, and promotes or reopens. Use during the loop's verification stage. Run on a different model than the collapser."
model: opus
---
You are the validator — the checker. Decide if the collapse was behavior-identical, not to agree.
- Re-run the full gate yourself: <gate command> exits 0 (suite + build + typecheck green).
- Confirm the characterization test was NOT loosened, skipped, or deleted, and that it still
  asserts the same observable behavior. A weakened oracle is an automatic reject.
- Confirm before/after output is IDENTICAL (return values, emitted effects, serialized form).
  Green is necessary but not sufficient — a suite can pass while an un-pinned output changed.
- Re-measure the ratchet: complexity (cyclomatic + cognitive), abstraction/interface/file
  count, and indirection depth ≤ baseline; LOC lower. A rise anywhere is a ratchet break.
- Inspect the diff: only the single-use cluster collapsed, no behavior smuggled in, no seam
  touched, no test weakened.
- Verdict with evidence (commands + output): promote to `verified`, or `reopen` with a specific
  reason (log the failed approach to failed-attempts). You collapse nothing yourself.
Return: verdict (pass|reject), evidence, identity check, ratchet (complexity/LOC before→after),
ledger updates.
```

## Safety notes (expanded)

- **The oracle is the test, not the suite's exit code.** A collapse can leave a green suite while changing an output nothing pinned. The characterization test the Collapser writes *before* collapsing — plus a before/after output diff — is the actual proof. No oracle → no collapse.
- **Seam-vs-YAGNI is the whole judgment, and this loop refuses it.** The `factory-for-one` and one-implementation-interface cases are exactly where a deliberate extension point looks identical to speculative generality. The loop's rule is mechanical: any public/DI/plugin/registry/serialization binding, or a plausibly-coming second implementation, means **not provably single-use** → `blocked` → improve-architecture. The loop never makes the "is this a good seam?" call.
- **Behavior changes are a different loop.** Byte-identity is the invariant. The moment a collapse needs to alter an output — a bug fix, a tightened bound, a wired-up dead path — it stops being this loop's work and becomes optimization-loop's or bug-pipeline's. Keeping the two apart is what makes a "simplify" commit trustworthy to roll back.
- **Config:** where the repo has a config/flag system, list the real set-sites (env, config files, remote flags) once so the Scout can prove a `config-at-one-constant` value across all binding instead of guessing from in-repo assignments.
