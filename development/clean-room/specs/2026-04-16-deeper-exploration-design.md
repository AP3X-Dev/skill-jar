# Clean-Room Deeper Exploration — Design / PRP

**Date:** 2026-04-16
**Target skill:** `C:\Users\Guerr\.claude\skills\clean-room\SKILL.md`
**Scripts:** `C:\Users\Guerr\.claude\skills\clean-room\scripts\extract-inventory.py`, `diff-inventory.py`, `enrich-inventory.py`, `generate-coverage.py`

---

## 0. Problem Statement

Clean-room rewrites run by this skill silently lose functionality. Observed failure modes, ranked by pain:

- **E — Cross-module flows broken (worst).** Each module looks correct in isolation; the wires between them don't carry signal. Symptom examples from recent parity runs:
  - `client_sop_text=""` — SOP loader existed, pipeline existed, but nothing threaded loader output into the Stage 1 parameter.
  - Per-speaker streams populated on `Session` but never read by `Stage1Runner`.
  - `AssistStateClassifier` classified input but its output never reached the SOP registry.
  - `TradeScanner` keyword scan existed, was never called from the main pipeline.
  - `SopFeed` offsets advanced per-tick, but the registry only kept the latest chunk — the interface and its consumer disagreed.

- **B — Symbol exists, wrong behavior (next).**
  - Stage 1 system prompt: 89 lines in original, 4 lines in rewrite.
  - Stage 3 system prompt: 98 lines in original, 4 lines in rewrite.
  - `CallSopState.apply_alerts` accumulated `matched_*_types` across calls instead of rebuilding per chunk.
  - `membership_tier` first-write-wins instead of latest-wins.
  - `normalize_trade()` returned `None` for non-canonical values instead of passing through.

- **C — Private helpers lost (constant supporting cast).**
  - Time-period fallback filter, fee-tier amount collapse, compact-SOP builder, `_apply_classification`, 70% word-overlap threshold in restatement filter, `expand_visible_for_final_review`.
  - Tiny private functions encoding real behavior; rewrite either skipped them or stubbed them.

Current skill (`clean-room` v1) has Pass 1b AST symbol extraction and a parity-gap differ. Those catch **whole-symbol** misses (A) well. They miss E, B, and C because:

1. Only top-level / class-level `exported` symbols are tracked; private helpers (C) aren't gated.
2. No call-graph — cross-module wires (E) can't be mechanically detected.
3. No argument-binding data — "always passes empty" (E's `client_sop_text=""`) is invisible.
4. No field read/write tracking — "written but never read" (E — per-speaker streams) is invisible.
5. No content snapshots — 4-line-vs-89-line prompt drift (B) isn't flagged.
6. No semantic `op_detail` on assignments — `append`-every-call vs `assign`-per-chunk (B's `apply_alerts` bug) isn't flagged.

## 1. Goals

- Catch E / B / C failure modes mechanically, before Phase 3 dispatch, via inventory extensions + differential reports.
- Keep the skill's five supported languages (Python, JavaScript, TypeScript, Go, Rust) on equal footing — no per-language branching in consuming passes.
- Backward-compatible with v1 inventories; gradual adoption by in-flight projects.
- Bound the runtime overhead: Pass 1b stays within ~2× current baseline on a 50k-LOC repo.

## 2. Non-Goals

- No full type inference or language-server integration. Name-based resolution only; dynamic dispatch marked `unresolved`.
- No runtime / dynamic call tracing. Pure static analysis.
- No retroactive scanning of already-merged rewrites. In-flight projects can regenerate Phase 1b with the new extractor.
- No expansion of `LANGUAGES` beyond the current five in this iteration.

## 3. Success Criteria

- **E-pattern regression test:** a curated fixture with a `client_sop_text=""` bug wired exactly as in the parity run causes `diff-inventory.py` to exit non-zero and name the dead parameter.
- **B-pattern regression test:** a prompt-template drift fixture (89 → 4 lines) emits a `critical` `content-diff` entry.
- **C-pattern regression test:** private helpers present in the original and missing in the rewrite show up in the `missing` section.
- **Runtime:** Pass 1b on a 50k-LOC reference repo completes in ≤ 2× current baseline wall time.
- **Language parity:** the regression fixture suite runs and passes on Python, JS, TS, Go, Rust.
- **Backward compat:** v1 inventories diff against v2 inventories without crashing; new reports are skipped with a clear note.

## 4. Architecture

Three layers of change, each independently testable.

### 4.1 Extraction layer (`extract-inventory.py`)

Today: one AST walk per file emits one symbol record per top-level / class-level declaration.

Change: three structured passes over the same tree, producing three top-level arrays in `inventory.json`.

#### Pass E1 — Symbol pass (existing, extended)

- Capture nested and local functions, lambdas assigned to names, closures, inner classes. Whereas v1 stopped at top-level / class-level, v2 walks into function bodies.
- New field `visibility: public | private | nested`:
  - `public` = default for exported / non-`_`-prefixed / `pub`-declared.
  - `private` = `_`-prefixed (Python), non-exported (Go lowercase first letter, Rust non-`pub`, TS/JS not exported), `private` keyword (TS).
  - `nested` = defined inside another function's scope (regardless of visibility keyword).
- New field `parent_id` — the enclosing class/struct symbol, or `null`.
- New field `enclosing_scope` — the enclosing function symbol if nested, else `null`.
- `shape` vocabulary extended with `prompt-template | regex | threshold | config-const`. Detection heuristic:
  - `prompt-template`: string constant > 200 chars and (name matches `/PROMPT|TEMPLATE|SYSTEM|INSTRUCTION/i` OR multi-line triple-quoted with > 10 lines).
  - `regex`: string assigned to a name matching `/REGEX|PATTERN|RE_/i`, or passed directly to a regex compile call.
  - `threshold`: numeric constant with name matching `/THRESHOLD|CUTOFF|MIN_|MAX_|RATIO|PERCENT/i`.
  - `config-const`: collection literal (dict/list) at module level whose name matches `/CONFIG|DEFAULTS|SETTINGS|OPTIONS/i`.
- `content_snapshot` added for `shape: prompt-template | regex`:
  ```json
  { "sha256": "…", "length": 2847, "line_count": 89, "token_count_estimate": 612 }
  ```
  Token estimate: `ceil(length / 4)` (no tokenizer dependency). Raw content written to `clean-room/content/<sha256>.txt`.

#### Pass E2 — Edge pass (new)

For every `Call` node, emit a `call_edge` record:

```json
{
  "id": "edge:py:src/pipeline/runner.py:run_pipeline:42:call:0",
  "caller_id": "py:src/pipeline/runner.py:run_pipeline",
  "callee_name": "Stage1Runner.run",
  "receiver_hint": "self.stage1",
  "file": "src/pipeline/runner.py",
  "line": 42,
  "arg_bindings": [
    { "param": "session", "kind": "variable", "expr": "session" },
    { "param": "client_sop_text", "kind": "literal", "expr": "\"\"", "literal_value": "" }
  ],
  "resolution": "resolved",
  "resolved_callee_id": "py:src/pipeline/stage1.py:Stage1Runner.run"
}
```

Field rules:
- `arg_bindings[].kind`: `literal | variable | default | complex-expr | spread`.
  - `literal` captured when the AST node is a primitive literal (string, number, bool, None/null/nil, empty list/dict).
  - `literal_value` populated only when the literal is "empty-ish": `""`, `None`/`null`/`nil`, `0`, `false`, `[]`, `{}`, `()`. Other literals set `kind: literal` but omit `literal_value` (not the dead-param signal we care about).
  - `default` used when the call site omits an arg entirely and relies on the signature default.
  - `complex-expr` for anything else (method chain, arithmetic, conditional).
  - `spread` for `*args` / `**kwargs` / `...args`.
- `resolution`:
  - `resolved` — callee name matches exactly one `location: source` symbol in the inventory.
  - `ambiguous` — matches multiple (e.g., two classes with a same-named method; receiver type unknown).
  - `unresolved` — matches zero (likely stdlib, third-party, or dynamic dispatch).
- Resolution algorithm (language-agnostic, name-based):
  1. If receiver_hint indicates `self.` or `this.`, scope lookup to methods of the caller's `parent_id` class.
  2. Else try fully-qualified match (`module.func`).
  3. Else try filename-scoped match.
  4. Else try global name match across inventory.
  5. If > 1 candidate: `ambiguous`, record all `candidate_ids`. If 0: `unresolved`.

#### Pass E3 — Field I/O pass (new)

For each class/struct and each module-level name, emit reads and writes:

```json
{
  "id": "io:py:src/state/call_sop.py:CallSopState.matched_trade_types:87:write",
  "owner_id": "py:src/state/call_sop.py:CallSopState",
  "field": "matched_trade_types",
  "op": "write",
  "op_detail": "append",
  "context_symbol_id": "py:src/state/call_sop.py:CallSopState.apply_alerts",
  "file": "src/state/call_sop.py",
  "line": 87
}
```

- `op`: `read | write | delete`.
- `op_detail` (writes only): `assign | append | extend | inplace-op | destructure | augmented-assign | setitem | method-mutation`.
  - `assign` — `x.f = v`
  - `append` — `x.f.append(v)` / `x.f.push(v)` / `x.f << v`
  - `extend` — `x.f.extend(xs)` / `x.f += xs` where `f` is a list/slice
  - `inplace-op` — `x.f += 1` where `f` is scalar
  - `destructure` — `x.f, y.g = a, b`
  - `augmented-assign` — any `+=`, `-=`, `|=`, etc. not covered above
  - `setitem` — `x.f[k] = v`
  - `method-mutation` — other mutation methods (`clear`, `pop`, `remove`, `update`, etc.) — detected by a known method list per language
- Reads: any expression-position access `x.f` that is not being assigned to.

Module-level state handled the same way; `owner_id` points at the module symbol.

#### Output schema — v2 top level

```json
{
  "schema_version": "2",
  "extracted_at": "2026-04-16T…",
  "repo": "…",
  "symbols": [ … ],
  "call_edges": [ … ],
  "field_io": [ … ]
}
```

Consumers of v1 keys (`symbols`) unchanged. New consumers opt into `call_edges` / `field_io`. A v1 inventory in the wild still diffs without error (degraded reports).

#### Artifacts

```
clean-room/
  inventory.json
  inventory.rewrite.json           # Parity Mode
  content/                         # gitignored
    <sha256>.txt
  enrichment-prompts/              # existing
  enrichment-responses/            # existing
  triage.yaml                      # new — see §4.2
```

### 4.2 Diff layer (`diff-inventory.py`)

Five new report sections appended to `PARITY_GAPS.md` in addition to the existing five (`missing`, `extra`, `kind-drift`, `signature-drift`, `tag-drift`).

#### 4.2.1 `call-graph-delta`

For each public entry point in the original, compute the transitive callee set (BFS over resolved `call_edges` starting from the entry point). Compare against the rewrite's transitive callee set for the corresponding entry point (matched by `qualified_name`).

Entry-point detection:
- `shape: entrypoint` symbols.
- Top-level `modifiers: exported` functions where `location: source` (CLI handlers, module exports).
- Symbols with framework-signature heuristics (Flask/FastAPI route decorators, Express route handlers, etc.) — detected via decorator name matching.

Delta classes:
- `missing-callee`: in original's closure, absent from rewrite's.
- `extra-callee`: in rewrite's closure, absent from original's (informational only, not a gate failure).

Report format:
```markdown
### call-graph-delta: `Stage1Runner.run`
- **missing-callee:** `SopLoader.load`
  - original path: `Stage1Runner.run → self.sop_loader.load`
  - rewrite path: (no edge from `Stage1Runner.run` to any symbol matching `sop_loader.load`)
  - triage: pending
```

#### 4.2.2 `dead-parameters`

For each parameter of each `location: source` function in the rewrite, compute `dead_ratio = count(call_edges where arg for this param is literal_value-empty or default) / total_call_sites`. Flag when `dead_ratio == 1.0` (severity: `critical`, gate-blocking) or `>= 0.9` (severity: `warning`, not gate-blocking but triage-visible).

```markdown
### dead-parameters
- **`Stage1Runner.run(client_sop_text)`** — 3/3 call sites pass `""`
  - src/pipeline/runner.py:42  → `self.stage1.run(session, "")`
  - src/pipeline/runner.py:78  → `runner.run(s, "")`
  - tests/test_stage1.py:15     → `runner.run(session, "")`
  - original comparison: `client_sop_text` sourced from `SopLoader.load_for_session(session)` in the original — wire is missing
  - triage: pending
```

"Original comparison" line populated in Parity Mode by tracing the original's call graph for the same parameter; omitted in full clean-room mode.

#### 4.2.3 `dead-reads`

For each field in `field_io` with `op: write` count > 0 and `op: read` count == 0 in the rewrite, flag.

```markdown
### dead-reads
- **`Session.per_speaker_streams`** — 2 writes, 0 reads
  - writes: src/session/builder.py:103, src/session/builder.py:118
  - original comparison: read in `Stage1Runner.run` and `AssistStateClassifier.classify` in the original
  - triage: pending
```

Caveat: reads via dynamic attribute access (`getattr`, bracket lookup with computed key) can't be detected statically. Report notes "may be read dynamically" if the class is ever passed to `getattr` / indexed-access sites. Lowers severity to `warning` when this applies.

#### 4.2.4 `orphan-methods`

For each `visibility: public` method/function in `location: source`, check whether it is in the transitive closure of any detected entry point. If not, flag.

Suppression rules:
- Symbol has `shape: entrypoint` → not orphan.
- Symbol has framework-decorator signature (routes, handlers, plugins registered by decorator) → not orphan.
- Symbol has `modifiers: exported` and the target is a library (detected via top-level `__init__.py` re-export / `index.ts` barrel / Rust `pub use`) → not orphan.

```markdown
### orphan-methods
- **`TradeNormalizer.normalize_trade`** — defined, not reached from any entry point
  - defined: src/trade/normalize.py:24
  - original comparison: reached from `TradeScanner.scan → normalize_trade` in the original
  - triage: pending
```

#### 4.2.5 `content-diff`

For each pair of matched symbols (by `qualified_name`) with `shape: prompt-template | regex` and both having `content_snapshot`, compute deltas on `line_count` and `token_count_estimate`.

Severity:
- `critical` — any single dimension drops > 50%.
- `warning` — drops > 20%.
- `info` — drops > 5%.

```markdown
### content-diff
- **`STAGE1_SYSTEM_PROMPT`**
  - original: 89 lines, 612 tokens, sha256 abc…
  - rewrite:   4 lines,  28 tokens, sha256 def…
  - delta: line_count −95.5%, token_count −95.4%
  - severity: critical
  - triage: pending
```

Full content diff available on demand: `diff-inventory.py --show-content STAGE1_SYSTEM_PROMPT` pulls the sidecar files and emits a unified diff. Not automatically dumped to `PARITY_GAPS.md` to keep the report readable.

#### 4.2.6 Triage persistence — `clean-room/triage.yaml`

Sidecar format. Regenerating `PARITY_GAPS.md` preserves decisions.

```yaml
schema_version: 1
entries:
  - report: dead-parameters
    key: "Stage1Runner.run(client_sop_text)"
    triage: gap-to-close
    note: "wire missing; see PRP item #4"
    at: 2026-04-16T09:12:00Z
  - report: content-diff
    key: "STAGE1_SYSTEM_PROMPT"
    triage: gap-to-close
    note: "prompt content needs to be regenerated"
    at: 2026-04-16T09:13:00Z
  - report: orphan-methods
    key: "TradeNormalizer.normalize_trade"
    triage: intentional-divergence
    note: "replaced by inline canonicalization in Pipeline.run"
    at: 2026-04-16T09:14:00Z
```

Triage verbs:
- `gap-to-close` → flows to `PRP.md` as a requirement.
- `intentional-divergence` → logged in `IMPROVEMENTS.md` "Preserved Divergence" section.
- `false-positive` → recorded with reason (most common: dynamic dispatch, reflection, framework magic).

The diff script loads `triage.yaml` on start; re-running the diff re-renders `PARITY_GAPS.md` with triage state applied.

#### 4.2.7 Exit-code gate

`diff-inventory.py` exits:
- `0` — no `pending` or `gap-to-close` entries across all sections.
- `1` — one or more gate-relevant entries are `pending` or `gap-to-close`.
- `2` — usage error.

CLI flag `--mode=project-initialization` relaxes the gate on `dead-parameters`, `dead-reads`, and `orphan-methods` only (these are expected during initial scaffolding when wiring is not yet complete). `call-graph-delta` and `content-diff` remain hard-gated even in initialization mode.

### 4.3 Pass layer — new Pass 4.5 (Integration Seams)

**Runs in Wave 3**, after Pass 4 (Module-by-Module) completes and `inventory.json` + `call_edges` + `field_io` are available.

**Mechanical step (deterministic):**
- `scripts/generate-wire-ledger.py` walks `call_edges` from each entry point. For every `(caller → callee)` edge in the closure, it emits a "wire" entry with:
  - producer: the caller symbol
  - consumer: the callee symbol
  - carried data: the parameter names and their source at the producer site (literal / variable / chain of producers)
  - field interactions (from `field_io`): fields written by this edge's caller and read by its callee

- Output: `clean-room/wires.json` and a seeded `## §4.5 Integration Seams` section in `DESIGN_DOC.md` with one entry per wire, prose fields empty.

**Prose step (subagent):**
- Dispatch a research subagent (full clean-room) or analyzer subagent (transparent mode) with `wires.json` + repo access.
- Subagent fills prose-only fields per wire: `what_data_represents`, `invariant`, `if_broken_symptom`. Strict: no verbatim code, no new wires — it can only annotate the mechanically-generated list.
- Merged back into `DESIGN_DOC.md` §4.5.

**Why mechanical-first:** the LLM can't forget a wire because it's not the one enumerating them. The skeleton is complete by construction.

### 4.4 `COVERAGE.md` update

New section:

```markdown
## Wires (from §4.5)
- [ ] `Pipeline.__init__ → SopLoader.load` — `client_sop_text` produced and stored on `self.sop_text`
- [ ] `Pipeline.run → Stage1Runner.run(session, client_sop_text=self.sop_text)` — wire carries SOP text into stage 1
- [ ] `Stage1Runner.run → AssistStateClassifier.classify` — classification output read by SOP registry
- ...
```

`generate-coverage.py` updated: reads `wires.json` and emits the Wires section after §4 Modules.

Wire checkboxes transition to `[x]` only when the corresponding edge exists in the rewrite's `inventory.json` AND the parameter binding is not dead AND the consumer reads any produced state.

### 4.5 Language strategy (all 5)

All extraction uses `tree_sitter_language_pack`. Language-specific adapters live in `scripts/extract_lang/<lang>.py`, sharing a common interface:

```python
class LangAdapter:
    def symbols(self, tree: Tree) -> list[SymbolRecord]: ...
    def call_edges(self, tree: Tree, symbols: SymbolIndex) -> list[CallEdge]: ...
    def field_io(self, tree: Tree, symbols: SymbolIndex) -> list[FieldIO]: ...

    # Helpers
    def visibility(self, node: Node) -> Visibility: ...
    def is_nested(self, node: Node) -> bool: ...
    def detect_shape(self, node: Node) -> Shape | None: ...
```

Per-language notes:

| Language | Visibility rule | Nested detection | Special cases |
|----------|----------------|------------------|---------------|
| Python | `_` prefix = private | function/method body scope | Decorator-generated symbols captured by name; metaclasses skipped |
| JavaScript | `#` prefix private; non-exported = module-private | closure scopes | Arrow functions assigned to names = symbols; anonymous arrow in args = not tracked |
| TypeScript | `private`/`protected` keyword + JS rules | same as JS | Interfaces and type aliases as symbols; `declare` symbols tagged `shape: declaration` |
| Go | lowercase first letter = unexported | no nested functions in typical code | Interface methods tracked; `pub`-equivalent is capitalization |
| Rust | non-`pub` = private | `fn` inside `fn` | Trait impls: method resolution goes via trait name first, then impl type; generics erased in `qualified_name` |

Call resolution shares the same algorithm across languages; adapter only differs in how it extracts `receiver_hint` from the AST.

## 5. Pre-flight Checklist additions

Added to the existing Phase 3 pre-flight in `SKILL.md`:

- [ ] `inventory.json` uses `schema_version: 2`; `call_edges` and `field_io` arrays present
- [ ] `clean-room/wires.json` generated; `DESIGN_DOC.md` §4.5 populated with prose per wire
- [ ] `call-graph-delta` report has zero `missing-callee` entries with `triage: pending` or `gap-to-close`
- [ ] `dead-parameters` report has zero `pending` / `gap-to-close` entries (suppressible via `--mode=project-initialization`)
- [ ] `dead-reads` report has zero `pending` / `gap-to-close` entries (suppressible via init mode)
- [ ] `orphan-methods` report has zero `pending` / `gap-to-close` entries (suppressible via init mode)
- [ ] `content-diff` report has zero `critical` entries with `pending` or `gap-to-close`; `warning` entries triaged
- [ ] `COVERAGE.md` Wires section generated and reviewed; total item count includes wires

## 6. Work Breakdown (for autonomous-advisor)

Each step is an independently implementable unit with a clear exit test.

### Step A — Extractor: symbol pass v2

- Add `visibility`, `parent_id`, `enclosing_scope` fields.
- Walk into function bodies for nested symbols.
- Extend `shape` vocab with prompt-template / regex / threshold / config-const.
- Emit `content_snapshot` and write sidecar `content/<sha256>.txt`.
- Update `inventory-vocab.json`.
- Set `schema_version: 2`.
- **Exit test:** Python fixture with 1 public fn, 1 private helper, 1 nested closure, 1 prompt constant emits 4 symbol records with correct tags and a sidecar.

### Step B — Extractor: call-edge pass

- New AST pass over `Call` nodes, per language.
- Extract `arg_bindings` including `literal_value` for empty literals.
- Name-resolution algorithm with `receiver_hint`.
- Populate `resolved | ambiguous | unresolved`.
- **Exit test:** fixture where `runner.run(session, "")` passes `""` to `client_sop_text` emits a `call_edge` with `arg_bindings[1].literal_value == ""`.

### Step C — Extractor: field-I/O pass

- Track reads, writes, and `op_detail` for class/struct/module state.
- Per-language mutation method lists.
- **Exit test:** fixture where `CallSopState.apply_alerts` contains `self.matched_types.append(t)` emits a `field_io` record with `op: write, op_detail: append`. Separate fixture where the same method contains `self.matched_types = [t for t in …]` emits `op: write, op_detail: assign`. The two should be distinguishable in a diff.

### Step D — Language adapters

- Implement `LangAdapter` for Python, JS, TS, Go, Rust.
- Shared tests in `tests/adapters/` parameterized over a common set of fixture shapes per language.
- **Exit test:** the shared fixture suite (one E-pattern, one B-pattern, one C-pattern test) passes on all 5 languages.

### Step E — Differ: five new reports

- Implement `call-graph-delta`, `dead-parameters`, `dead-reads`, `orphan-methods`, `content-diff`.
- Entry-point detection heuristics.
- Triage sidecar load/save.
- Exit-code logic with `--mode=project-initialization`.
- **Exit test:** the known-bug fixture set from §3 success criteria causes non-zero exit and names the exact failing entry.

### Step F — Wire ledger generator + Pass 4.5

- `scripts/generate-wire-ledger.py`: walk `call_edges` from entry points, emit `wires.json` + seeded `DESIGN_DOC.md` §4.5.
- Subagent prompt template for prose enrichment.
- **Exit test:** run against a toy pipeline repo; `wires.json` contains one wire per distinct producer→consumer edge in the closure of the entry point.

### Step G — Coverage update

- `generate-coverage.py` reads `wires.json` and emits the new Wires section.
- Summary counters include wires.
- **Exit test:** run on a sample `DESIGN_DOC.md` + `wires.json`; `COVERAGE.md` Wires section appears with correct counts.

### Step H — `SKILL.md` update

- Document new passes, new reports, new gates, new artifacts.
- Update the `Artifacts & Coverage Tracking` table with `triage.yaml`, `wires.json`, `content/`.
- Update Pre-flight Checklist.
- Document the `--mode=project-initialization` escape hatch.

### Step I — Regression fixtures

- Build fixture repo pairs (original + broken-rewrite) that reproduce each of the E/B/C bugs from §0.
- One set per supported language, at minimum covering the patterns from the recent parity run.
- CI harness invokes the full pipeline (extract → enrich → diff) and asserts the expected non-zero exit + matching entries.

## 7. Rollout

- v2 inventories interoperate with v1 diffs (graceful degradation with a note).
- In-flight Parity-Mode projects: regenerate `inventory.json` + `inventory.rewrite.json` with v2 extractor; re-run differ; triage the new reports once.
- Full clean-room projects in progress: at next Phase 1 re-run, switch to v2. Existing `DESIGN_DOC.md` kept; §4.5 generated and appended.
- Single breaking change: `inventory-vocab.json` gains entries (new `shape` values). v1 validators will reject v2 inventories. Not a concern because v1 only ran locally, never in CI.

## 8. Open Risks

- **Call-resolution precision on dynamic languages.** Python/JS method call resolution degrades when receiver type is unknown (`self.x.run()`). Heuristic falls back to `ambiguous`; gate treats ambiguous as non-dead but flags high counts for attention.
- **Nested-symbol explosion.** Repos with many small closures could bloat `inventory.json`. Mitigation: closures smaller than 3 AST nodes (e.g., `lambda x: x + 1`) are not emitted as standalone symbols; they stay inline.
- **Content-snapshot churn.** Cosmetic whitespace changes in prompts would produce different `sha256` and might trip `content-diff` with near-zero delta. Solution: `line_count` and `token_count_estimate` are the gate signals, not sha256. Sha256 is identity only.
- **Framework magic.** Decorator-registered handlers, plugin systems, reflection — all look like orphans/unused. The suppression rules in §4.2.4 handle common cases; additions are easy (new decorator names → config file). Unknown frameworks will produce false positives on first run; triage as `false-positive` with reason.

## 9. Success gates (for autonomous-advisor)

Hard criteria — advisor may not mark this complete until all pass:

1. `scripts/extract-inventory.py` emits schema v2 for all 5 languages; regression fixture suite passes.
2. `scripts/diff-inventory.py` produces all 10 report sections (5 legacy + 5 new); regression fixtures for E/B/C each cause the expected non-zero exit and report entry.
3. `scripts/generate-wire-ledger.py` exists and produces `wires.json` + seeded `DESIGN_DOC.md` §4.5.
4. `scripts/generate-coverage.py` emits a Wires section with accurate counts.
5. `SKILL.md` reflects all of the above; Pre-flight Checklist updated; `--mode=project-initialization` documented.
6. Runtime on the 50k-LOC reference repo ≤ 2× the v1 baseline. Record numbers in the final commit message.
7. One end-to-end smoke run on a real Parity Mode project (the caller's current workspace, if available) produces a report where at least one of the listed E/B/C bugs from §0 is independently rediscovered.
