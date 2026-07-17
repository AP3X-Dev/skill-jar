---
name: clean-room
description: "Use when reimplementing, porting, or cloning an existing codebase/repo — produces an exhaustive design doc via multi-pass analysis, proposes improvements over the original, then hands off to autonomous implementation (the autonomous-advisor skill). Supports three modes: full clean-room (firewalled, IP-safe), Parity Mode (close gaps against an original), and Transparent Mode (no firewall, for code you own). Triggers include 'clean room rewrite', 'port this repo', 'reimplement X in Y', 'clone without copying code', 'rewrite from scratch based on the original', 'transparent rewrite', 'rewrite without firewall'."
---

# Clean Room Rewrite

## Overview

A **clean room rewrite** produces a new implementation of an existing system without the implementer ever reading the original source. The only bridge between original and rewrite is a **design document**. Legal reason: avoid copyright/licensing contamination. Engineering reason: force a real understanding of behavior, not a line-by-line transliteration.

**Core principle:** The design doc is the product of this skill's first phase. Its accuracy determines whether the rewrite works. Skimp on the doc → the rewrite is wrong in ways no one will notice until production.

## Modes

This skill has three modes. Pick one at the start — mixing them mid-project is what causes contamination incidents. Lock the mode before source analysis; "internal", "time-boxed", or "both repos are already on disk" are not modes.

| Mode | Firewall? | Use when |
|------|-----------|----------|
| **Full clean-room** (default) | Yes — implementer never sees original | IP/legal separation required; license-safe reimplementation; untrusted upstream |
| **Parity Mode** | Yes (for the original) | A rewrite already exists and needs gap-closing against its source |
| **Transparent Mode** | **No** — implementer reads the original freely | You own both codebases; no IP concerns; want the multi-pass rigor without the subagent overhead |

**Default assumption:** if the user hasn't specified, ask. Don't silently pick Transparent just because it's easier — a clean-room run that should have been firewalled can't be retroactively cleaned. Until the human explicitly clears Transparent Mode, default to full clean-room.

See the **Transparent Mode** and **Parity Mode** sections below for the deltas from the default flow.

## Three Phases

| Phase | Role | Sees | Produces |
|-------|------|------|----------|
| **1. Analyze** | Analyzer | Original source | `DESIGN_DOC.md` |
| **2. Improve** | Architect + Human | Design doc | `IMPROVEMENTS.md` + `PRP.md` |
| **3. Implement** | autonomous-advisor or host-neutral implementation stack | PRP only (no original source) | New codebase |

**Hard rule:** The Phase 3 implementer MUST NOT read the original source. Start a fresh session between Phase 2 and Phase 3. Do not paste original code into the implementation session. If any detail is missing from the doc, either (a) return to Phase 1 or 2 to fix it, or (b) use the **Research Subagent Escape Hatch** below — the implementer itself never peeks. "Just one function", "just one test", or "just the exact error string" is still a direct read.

### Research Subagent Escape Hatch

If Phase 3 hits a gap, the implementer may dispatch a **fresh research subagent** that CAN read the original source. The subagent's job is to *answer a specific question*, not to transcribe code.

**What the research subagent MAY return:**
- Architectural explanations and design rationale
- Behavior descriptions in prose
- Invariants, preconditions, edge cases it observed
- Algorithm descriptions and complexity analysis
- **Pseudocode** when a concrete algorithm shape is needed
- Recommendations / "watch out for X"

**What the research subagent MUST NOT return:**
- Verbatim source or test code, comments, or string literals from the original, even short snippets
- File-by-file code snippets
- Direct translation that reads like a line-by-line port
- Exact internal function names or error strings unless they're part of the public contract already in the PRP
- Identifiers invented by the original author unless they're part of the public contract already in the PRP

**Protocol:**
1. Implementer formulates a precise question (e.g., "How does module X handle concurrent writes to Y?" — not "show me module X").
2. Implementer dispatches a research subagent with: the question, a copy-ban reminder, and instruction to return findings only.
3. Subagent returns findings. If the response contains banned source/test code, exact internal names, or exact non-public error text, discard it instead of salvaging useful pieces; record the failed dispatch and re-run with stricter instructions.
4. Implementer uses clean findings directly AND appends them as a new entry in `DESIGN_DOC.md` so the knowledge is durable for future questions.
5. If the same question recurs, consult the updated doc first — don't re-dispatch.

This preserves the clean-room firewall: the *implementer's context* is never contaminated with original source. Only the *research subagent's* throwaway context sees it, and only abstracted findings cross the boundary.

### Known pressure rationalizations

| Rationalization | Required response |
|-----------------|-------------------|
| "This is internal and time-boxed, so the legal/IP posture can be documented later." | Stop and lock the mode first; default to full clean-room until Transparent is explicitly cleared. |
| "Function names and exact error strings are parity markers, not meaningful copied implementation." | Treat non-public names/error text as contamination-sensitive; capture behavior in prose or fingerprints, not implementation text. |
| "Letting the implementer peek at the original for small gaps is lower risk than guessing behavior." | Never let the implementer peek; use doc repair, a clean research subagent, or a targeted Phase 1 pass. |
| "The gap list is already known from eyeballing the app, so AST inventory is redundant." | Eyeballing can add notes only after the mechanical inventory/diff has grounded the gap list. |
| "A mode-lock file is process overhead when both repos are already on disk." | `RUN_STATE.md` is the firewall state; write/read it before opening both repos side by side. |
| "If the research helper returns a little source or test code, using it saves time and improves fidelity." | Reject the response wholesale; re-dispatch for prose, invariants, or pseudocode only. |
| "A contamination scan can wait until before merge, once there is code worth scanning." | Build the fingerprint before Phase 3 and scan after the first code-producing milestone, each major milestone, and final merge. |
| "The practical plan is to compare, port, test, and tighten afterward." | That is direct porting, not clean-room; complete Phase 1/2 gates before implementation. |

## Repository Roles — the firewall applies to ONE repo

The clean-room restriction applies **only to the repo being rewritten** (the "target"). Most real projects involve additional repos that are NOT under clean-room rules. Classify every repo up front, before Phase 1.

| Role | Clean-room rules apply? | Access pattern |
|------|------------------------|----------------|
| **Target** (the one being rewritten) | **YES** | Phase 1 analyzer only; implementer uses doc + research subagents |
| **Host / runtime** (e.g., we're reimplementing Repo A on top of Repo B's runtime) | No | Implementer reads directly; code, APIs, and idioms are reference material |
| **Library / SDK** we depend on | No | Read freely; use as-is |
| **Reference / inspiration** (unrelated project with a pattern we like) | No | Read freely |
| **Integration target** (system we must interop with) | No | Read its wire format, schemas, clients freely |
| **Previous rewrite attempt** by the user | No | Read freely |
| **Licensed corpus / IP-contaminated** | **YES** | Treat as a second target — apply full firewall |

Declare roles in `DESIGN_DOC.md` §0 under a **"Repository Roles"** subsection:

```markdown
## Repository Roles
- **Target (clean-room):** <repo-url-or-path> — <short description>
- **Host runtime:** <repo> — we build on top of this; direct use OK
- **Reference:** <repo> — studied for <pattern>; direct use OK
- **Integration target:** <system> — must interop with <protocol/schema>
```

**Rules for non-target repos:**
- Analyze them however is useful — no multi-pass discipline required.
- Their code, APIs, identifiers, and idioms can be used directly in Phase 3.
- Capture what's relevant about them in `DESIGN_DOC.md` as *external contracts we're targeting*, not as clean-room behavior.
- If the target and a host repo share names or structures by coincidence, document it so Phase 3 doesn't conflate them.

**Multi-target case:** If more than one repo is under clean-room (e.g., merging two systems into one rewrite), each gets its own firewall, its own design-doc section, and its own research-subagent contract. Findings from one target's research subagent must not leak into another target's section.

**Red flag:** Treating a host/runtime repo as clean-room wastes effort and prevents legitimate code reuse. Treating a target repo as "just reference" defeats the whole skill. Classify deliberately at the start.

## When to Use

- User asks to rewrite/port/reimplement an existing repo
- Cloning functionality from a reference implementation in a different language
- Replacing a legacy system while preserving behavior
- Creating a license-safe reimplementation
- **Closing parity gaps** between an existing rewrite/port and its original (see Parity Mode below)

**Do NOT use for:**
- Refactoring your own code (just refactor)
- A first-principles *reshape plan* for a subsystem you own, without a full rewrite — that's [rebuild-panel](../rebuild-panel/SKILL.md) (it routes back here only when its verdict is a genuine rewrite)
- Small utilities where reading the source is fine
- When the user wants a literal translation (use a transpiler or direct port instead)

## Parity Mode — closing gaps against an original

Use this mode when a rewrite/port already exists but is missing features, edge cases, or behaviors the original has. The goal is to bring the rewrite to full parity without contaminating it with original source.

**Repo roles in Parity Mode:**
- **Target (clean-room):** the original — still firewalled from the implementer
- **Rewrite-in-progress:** the existing partial rewrite — implementer reads and edits this directly (it's "our code")
- Any host/runtime/reference repos are classified normally

**Workflow:**

1. **Phase 1 (parity variant) — gap inventory.** Instead of a full design doc from scratch, run multi-pass analysis focused on *differences*. Passes A, B, and C are mechanical — run the AST extractor and differ first, then let Passes D/E work against the grounded diff. A gap list from eyeballing, screenshots, or manual app use can supplement `PARITY_GAPS.md`; it cannot replace the AST-backed inventory/diff.

   ```bash
   python "<skill-dir>/scripts/extract-inventory.py" <original-repo>  -o clean-room/inventory.json
   python "<skill-dir>/scripts/extract-inventory.py" <rewrite-repo>   -o clean-room/inventory.rewrite.json
   python "<skill-dir>/scripts/diff-inventory.py" \
     clean-room/inventory.json clean-room/inventory.rewrite.json \
     -o clean-room/PARITY_GAPS.md
   ```

   - Pass A: original's public contract — inventory filtered to `exported` + `location: source` (generated, not hand-enumerated)
   - Pass B: rewrite's current public contract — same filter applied to `inventory.rewrite.json`
   - Pass C: **diff the two** — `diff-inventory.py` classifies every delta into `missing`, `extra`, `kind-drift`, `signature-drift`, `tag-drift`. Output is `PARITY_GAPS.md`. Exit code 1 if any gaps remain.
   - Pass D: for each non-trivial behavior in the original §4/§6/§7 (module responsibility, control flow, error handling), check whether the rewrite implements it. Scope this by cross-referencing the inventory: every `shape: error-type` and `modifiers: throws` symbol in the original is a candidate for Pass D check.
   - Pass E: test-behavior diff — which original-test scenarios pass against the rewrite? Which fail? Which can't even be expressed? Seed from `location: test` symbols in both inventories; missing test symbols are a lower-priority signal than missing production symbols.
   - Output: `PARITY_GAPS.md` (AST-backed) + prose addenda from Passes D/E appended to the same file.

2. **Phase 2 — triage gaps and plan improvements.** Same as full mode: score each gap by impact/effort/risk, decide accept/defer/reject, roll into a PRP. Improvements can coexist with parity fixes — label each entry as `parity-gap` or `improvement`.

3. **Phase 3 — autonomous parity closure.** Hand off to [autonomous-advisor](../autonomous-advisor/SKILL.md) when available, or the host-neutral fallback stack below. The implementer works on the rewrite-in-progress directly; the firewall only blocks reads of the original. Research-subagent escape hatch still applies for any ambiguity about what the original actually does.

**Rules specific to Parity Mode:**
- Gaps are closed one at a time, each with its own acceptance test (often ported from the original's test suite via the research subagent — pseudocode of the assertion, not the verbatim test code).
- Function names, internal identifiers, and exact error strings are not copied as "parity markers" unless they are public contract terms already recorded in the PRP.
- If the rewrite has diverged *intentionally* from the original, classify that divergence: `preserved-divergence` (keep it) vs `regression` (parity-close it). Log in `PARITY_GAPS.md`.
- Don't let Parity Mode silently turn into "make the rewrite match the original byte-for-byte" — the PRP still decides what "parity" means for this project.

**Output artifacts:**
- `PARITY_GAPS.md` — the diff + decisions
- `PRP.md` — gaps selected for closure, framed as requirements with acceptance criteria
- Optionally update an existing `DESIGN_DOC.md` if one exists from a prior clean-room pass

## Transparent Mode — no firewall

Use when there is no IP/legal reason to keep the implementer blind to the original. You keep the multi-pass analytical rigor (the real engineering value of this skill) and drop the contamination controls (the legal/IP overhead).

**When to use Transparent Mode:**
- You own both the original and the rewrite
- Internal rewrite, refactor-as-rewrite, language port within the same org
- Open-source → open-source with a license compatible with direct copying (you're still rewriting for engineering reasons, not legal ones)
- Prototyping a rewrite approach before committing to a full firewalled run
- Teaching/learning exercise where the goal is understanding, not IP separation

**When NOT to use Transparent Mode:**
- Any licensed/proprietary original you don't own
- GPL/copyleft original being reimplemented for a permissively-licensed or commercial product
- Any situation where "did this code come from that code?" might be asked by a lawyer
- When in doubt — use full clean-room; you can't retroactively firewall contaminated context

**Repo roles (Transparent Mode):**
- **Original:** read freely at any phase, by any role. Still classified in `DESIGN_DOC.md` §0 so Phase 3 knows what it's targeting.
- All other role types behave the same as default mode.

**What changes vs. default flow:**

| Area | Default (firewalled) | Transparent Mode |
|------|---------------------|------------------|
| Phase 1 analyzer reads original | Yes | Yes |
| Phase 3 implementer reads original | **No** | **Yes — freely** |
| Research-subagent escape hatch | Required for every ambiguity | Not needed; implementer reads directly |
| Reverse-contamination scan (fingerprint) | Required merge gate | Skipped |
| "Fresh session between Phase 2 and 3" rule | Hard rule | Soft — helpful for focus, not required |
| `DESIGN_DOC.md` / `PRP.md` / `COVERAGE.md` | Required | Required — the rigor is the point |
| Multi-pass analysis (Passes 1–10) | Required | Required |
| Inventory extraction (Pass 1b) | Required | Required |
| Improvements sweep (Phase 2) | Required | Required |
| `clean-room/` gitignored | Yes | Yes — still planning artifacts, not product |

**Why keep the doc + passes?** The multi-pass analysis exists because humans (and LLMs) miss edge cases on a single read — that's true whether or not you're firewalled. The doc is what makes Phase 3 tractable for an autonomous advisor. Skipping it because "I can just read the code" is how rewrites silently lose behavior.

**Pragmatic shortcuts Transparent Mode allows:**
- When Phase 3 hits a small ambiguity, the implementer can read the exact original function directly instead of formulating a research-subagent question. Still update `DESIGN_DOC.md` with the finding so the knowledge is durable and future tasks don't re-derive it.
- When a bug is found in the rewrite, a direct side-by-side diff with the original is fair game for root-causing.
- Pseudocode in `DESIGN_DOC.md` can be tighter — the implementer can always verify against the source.
- No need to sanitize identifiers: if a name is good, keep it. Naming is not where real IP lives.

**Guardrails that still apply:**
- Don't wholesale copy-paste modules. The engineering goal is still a fresh implementation informed by a design — not a line-by-line transliteration. If you're copy-pasting more than a few lines, either (a) vendor the original as a library instead of rewriting, or (b) you're not really rewriting.
- Don't skip Pass 9 (test behavior extraction). Tests encode invariants that reading the code won't surface.
- Don't skip Pass 10 gap-hunt. "I can always check the source" is exactly how the doc ends up incomplete and Phase 3 drifts.
- Phase Gates 1→2 and 2→3 still apply. Completeness is the bar, firewall or not.

**Phase 3 dispatch in Transparent Mode:**
- `autonomous-advisor` (or fallback stack) runs the same way, but its ambiguity protocol is simpler: read the original, update the doc, continue. No research subagents needed.
- The advisor still treats `PRP.md` as the source of truth for *what* to build. The original is a reference for *how* specific behaviors work, not a substitute for the plan.

**Switching modes:**
- Transparent → full clean-room: not possible mid-project. The implementer's context is already contaminated. Start over with a fresh team/session if legal posture changes.
- Full clean-room → Transparent: allowed, but rare. Document the reason in the PR description (e.g., "IP review cleared direct reference to original").

## Artifacts & Coverage Tracking

Every run of this skill produces a set of planning artifacts. They live in a `clean-room/` directory at the root of the rewrite workspace.

| File | Purpose | Written during |
|------|---------|----------------|
| `clean-room/RUN_STATE.md` | **Mode lock + restart memory** — the first artifact of every run (see below) | Phase 1, before anything else |
| `clean-room/failed-attempts.md` | What was tried and failed (rejected research dispatches, failed fixes) so no later session retries it blind | Phase 3 onward |
| `clean-room/DESIGN_DOC.md` | Multi-pass design of the original | Phase 1 |
| `clean-room/inventory.json` | AST-extracted inventory (schema v2: symbols + call_edges + field_io) — structural skeleton feeding Passes 3/4/4.5/5/7/9 and Parity Mode diff | Phase 1, Pass 1b |
| `clean-room/inventory.rewrite.json` | (Parity Mode only) same schema, extracted from the rewrite-in-progress | Phase 1 (parity variant) |
| `clean-room/content/<sha>.txt` | Raw content of prompt-template / regex symbols (sidecar so inventory.json stays diffable) | Phase 1, Pass 1b |
| `clean-room/enrichment-prompts/` | Per-batch prompts for the Tier-2 LLM enrichment pass | Phase 1, Pass 1b |
| `clean-room/wires.json` | Mechanically-derived producer→consumer wire ledger for Pass 4.5 | Phase 1, Pass 4.5 |
| `clean-room/IMPROVEMENTS.md` | Triaged improvements list | Phase 2 |
| `clean-room/PRP.md` | Consolidated requirements handed to Phase 3 | Phase 2 |
| `clean-room/COVERAGE.md` | Checklist mapping original → rewrite; includes Wires section | Phase 1 onward |
| `clean-room/PARITY_GAPS.md` | (Parity Mode only) diff of original vs existing rewrite (10 report sections) | Phase 1 (parity variant) |
| `clean-room/SELF_CHECK.md` | (Rewrite-only) dead-parameter / dead-read / orphan-method / content-diff on the rewrite alone | Phase 3 or during parity closure |
| `clean-room/triage.yaml` | Persisted triage decisions for diff reports (preserved across re-runs) | Phase 1 onward |
| `clean-room/research/*.md` | Findings from research-subagent dispatches | Phase 3 |

### Gitignore by default

**These artifacts MUST NOT be committed to the rewrite repo.** They may contain detailed descriptions of the original's behavior that, while not verbatim code, are strategic planning material and can muddy provenance if shipped alongside the clean-room product.

At the start of Phase 1, before writing any doc, the analyzer:

1. Creates `clean-room/` in the rewrite workspace, and writes `RUN_STATE.md` as the **first artifact** — mode locked, phase table initialized (see the RUN_STATE.md section below). **If the directory already exists, treat the run as a resume:** read `RUN_STATE.md` FIRST (mode + next action) before touching any other file, then any existing `DESIGN_DOC.md` / `PRP.md` / `COVERAGE.md`; do not overwrite. **If `clean-room/` exists but `RUN_STATE.md` does not** (a legacy run), reconstruct it from the artifacts before doing new work — and assume **full clean-room (firewalled)** until the human confirms otherwise. A wrong guess toward Transparent on a firewalled run contaminates it irreversibly; the reverse merely costs ceremony.
2. Adds to `.gitignore` (create the file if missing):
   ```
   # clean-room planning artifacts — do not commit
   clean-room/
   ```
3. Verifies the directory is ignored (`git check-ignore -v clean-room/DESIGN_DOC.md` should match the rule).
4. **(MemBerry, optional) Set up MemBerry Memory for the rewrite workspace if available.** Like the optional FUGAZI integration used elsewhere in this skill, MemBerry is an optional persistence adapter — its absence is a clean skip, not a blocker. Check the workspace's `CLAUDE.md` for an `## MemBerry Memory` section.
   - If **missing** and the `memberry-setup` skill is available, invoke it to bootstrap MemBerry (project tag, entities, domain tags, seed priors, default memory blocks) before proceeding to Pass 1. A clean-room rewrite generates high-value persistent knowledge — Phase 2 triage decisions, research-subagent findings, rejected improvements, parity-close rationale, per-module gotchas — that lives in MemBerry so future sessions and Phase 3 agents build on it instead of re-deriving it.
   - If **missing** and `memberry-setup` is **not** available (it is a user-global skill, not bundled in this jar), skip MemBerry and proceed to Pass 1. Note the skip in `DESIGN_DOC.md` §0 ("MemBerry unavailable for this workspace") so later sessions don't re-offer setup.
   - If **present**, confirm the project tag and entity list still reflect the current workspace; update via `berry_bootstrap` if stale.
   - Verify MemBerry is reachable with `berry_tools(action: "list")`. If the call fails, proceed without persistence — do not block the rewrite on it.
   - If the user explicitly opts out for this repo, record that decision in `DESIGN_DOC.md` §0 ("MemBerry disabled for this workspace — reason: …") so later sessions don't re-offer setup.
5. Loads prior context: call `berry_load(task: "clean-room rewrite of <target>", tags: ["project:<tag>"])` so any pre-existing knowledge about the target or workspace informs Phase 1 from the first pass.

If the user explicitly asks to commit some artifact (e.g., a sanitized PRP for the team to review), do it as a one-off with an explicit un-ignore for that specific file — don't relax the directory-level rule.

### `RUN_STATE.md` — mode lock + restart memory

A clean-room run is multi-pass, multi-session, and crash-expensive. `RUN_STATE.md` is what makes it **restartable** — and, more importantly, what makes the firewall survive a restart. Write it before opening the original and rewrite side by side. The mode is the one fact a resumed session cannot afford to guess: a session that assumes Transparent on a run that was firewalled reads the original source into the implementer's context, and the contamination cannot be undone. The mode lives in this file, written once, never edited mid-run.

```markdown
# Clean-Room Run State — <target>

## Mode (LOCKED at run start — never change mid-run; see Switching modes)
- **Mode:** full-clean-room | parity | transparent
- **Firewalled targets:** <repo(s) under clean-room rules>

## Phase & Pass Status
| Item | Status | Artifact / Evidence |
|------|--------|---------------------|
| Pass 1 (Survey) | not-started / in-progress / done | DESIGN_DOC §1 |
| Pass 1b (Inventory) | | inventory.json |
| Passes 2–9 (one row each) | | §2–§9 / wires.json |
| Pass 10 (Gap hunt) | | fresh-agent verdict |
| Phase 2 sweeps + triage | | IMPROVEMENTS.md |
| PRP written | | PRP.md |
| Phase 3 handoff | | run-state of the autonomous run |
| Contamination scan | | scan SHA + exit code |

## Gate Results
| Gate | Check | Result | Date / SHA |
|------|-------|--------|------------|

## In-flight
<what is mid-work right now — for parallel waves, the wave plan that was
dispatched, so a crash mid-wave knows what to collect or redo>

## Next action
<the single most important line for a cold restart>
```

**Update protocol:** after every pass, wave, and sweep completes — and BEFORE dispatching a parallel wave, record the wave plan in In-flight so a crash mid-wave is recoverable. Gate results (below) are appended with their evidence as they run. Like every `clean-room/` artifact, it is gitignored.

### `COVERAGE.md` — the single source of truth for progress

This is the checklist the user asked for. It's generated at the end of Phase 1 and kept live through Phase 3. Every Pass-3 public-contract item, every Pass-4 module responsibility, every Pass-7 error/edge case, and every Pass-9 test-behavior spec becomes a checkbox.

**Structure:**

```markdown
# Coverage Checklist — <original> → <rewrite>

_Generated: <date>. Keep in lockstep with DESIGN_DOC.md._

## Legend
- [ ] not started
- [~] in progress
- [x] implemented + tests passing
- [!] diverged intentionally (see IMPROVEMENTS.md entry)
- [-] out of scope (see PRP non-goals)

## Public Contract (from §3)
- [ ] `POST /api/users` — creates user, returns 201 with body shape X
- [ ] CLI flag `--dry-run` — skips writes, still logs
- [ ] Exported function `parseConfig(path: string): Config`
- ...

## Modules (from §4)
### auth-module
- [ ] Token issuance flow
- [ ] Refresh flow
- [ ] Revocation + blacklist check

### billing-module
- ...

## Error & Edge Cases (from §7)
- [ ] Empty input returns validation error, never 500
- [ ] Unicode surrogate pairs in usernames preserved round-trip
- [ ] Retry after 429 with exponential backoff, max 5 attempts
- ...

## Behavioral Specs from Tests (from §9)
- [ ] Property: serialize then deserialize is identity for all valid configs
- [ ] Golden: sample request X produces canonical response Y
- ...

## Cross-Cutting (from §8)
- [ ] Structured logs with request ID on every request
- [ ] Config precedence: flag > env > file > default
- ...

## Improvements Accepted (from IMPROVEMENTS.md)
- [ ] Replace polling with long-lived subscription (architecture/perf)
- [ ] Add OpenTelemetry traces on hot paths (observability)
- ...

## Summary
- Total items: 147
- Complete: 0
- In progress: 0
- Remaining: 147
```

**Update protocol:**
- Phase 3 implementer (or autonomous-advisor) updates `COVERAGE.md` after each task completes — same commit as the implementation work, but `COVERAGE.md` is gitignored so it's a local-only update.
- Before any task is marked `[x]`, the associated acceptance test must pass.
- The summary counts are the primary progress signal. When all non-`[-]` items are `[x]` and the PRP's success criteria are met, the rewrite is done.
- Parity Mode: the checklist is seeded from `PARITY_GAPS.md` instead of a fresh §3/§4/§7/§9 walk; everything else works the same.

**Generation helper:** run `scripts/generate-coverage.py` (shipped with this skill) to emit a first-cut `COVERAGE.md`:

```bash
python "<skill-dir>/scripts/generate-coverage.py" clean-room/DESIGN_DOC.md clean-room/COVERAGE.md
```

It walks H2/H3 sections, turns every bullet in §3 / §4 / §7 / §8 / §9 into a `[ ]` checkbox, and tallies a summary. After generation:
- Review granularity — split bullets that cover multiple behaviors, merge ones that are genuinely one thing.
- Paste accepted entries from `IMPROVEMENTS.md` into the "Improvements Accepted" section.
- Add `[-]` entries for anything deliberately out of scope per the PRP.

## Phase 1: Multi-Pass Design Document

**The doc is built in passes. Each pass has one job. Do not try to capture everything in one read.** For large codebases (>20k LOC), expect 8+ passes. For small ones, passes can be combined but never skipped entirely.

### Parallelization (recommended for medium+ repos)

Most passes are independent once Pass 1 establishes the map. Dispatch them concurrently when the host supports parallel subagents; otherwise run the waves sequentially. Dependency waves:

| Wave | Passes | Must wait for |
|------|--------|---------------|
| 1 | Pass 1 (Survey), Pass 1b (Inventory extraction) | — |
| 2 | Passes 2, 3, 4, 5, 8, 9 in parallel (each seeded from `inventory.json`) | Wave 1 |
| 3 | Passes 6 (Control flow), 7 (Edges) | Pass 4 output from Wave 2 |
| 4 | Pass 10 (Verification) + any deep-dive passes | All prior waves |

Each dispatched subagent gets: the pass's goal, the repo path, the relevant existing doc sections (e.g., Wave-3 subagents read Pass-4 output), and strict instructions to return **doc content only** — no verbatim code, pseudocode OK. Coordinator merges results into `DESIGN_DOC.md` after each wave.

Expected speedup on a 50k-LOC repo: ~3–4× vs. serial. Trade: the coordinator must merge carefully to keep the doc coherent; one reconciliation pass after Wave 2 is usually needed.

For small repos (<5k LOC), serial is fine — parallelism overhead isn't worth it.

Create `DESIGN_DOC.md` at the start of Pass 1. Append/refine across passes. Commit after each pass so you can diff progress.

### Pass 1 — Survey / Cartography

Goal: know the shape before you know the content.

- Repo layout: top-level dirs, their purpose (infer from names + READMEs)
- Languages, build system, package manager, runtime versions
- LOC per module (`tokei`, `cloc`, or `scc`)
- Entry points: `main`, CLI commands, server bootstrap, library exports
- Test layout and test framework
- License, README, CONTRIBUTING, ARCHITECTURE.md if present

Output section: **"Repository Map"** with a tree and one-line purpose per directory.

### Pass 1b — Inventory Extraction (AST, schema v2)

Goal: build a deterministic, exhaustive inventory — the structural skeleton that every later pass is anchored to. LLM passes miss things; AST extraction doesn't. Do not mark Pass 1b done from manual review or a known gap list; if extraction is unsupported or fails, record the limitation as a gate issue instead of pretending the inventory exists.

**Schema v2** runs three structured passes over each file:

- **E1 — Symbol pass.** Every top-level, class-level, **and nested** symbol. Includes private helpers (C-pattern coverage). Adds `visibility` (public / private / nested), `parent_id` (enclosing class symbol id), and `enclosing_scope` (enclosing function symbol id, for closures). Detects content-sensitive symbols via `shape: prompt-template | regex | threshold | config-const` and emits a `content_snapshot` (sha256, length, line_count, token estimate) with raw text in a gitignored sidecar (`clean-room/content/<sha>.txt`).
- **E2 — Call-edge pass.** Every call site becomes a `call_edge` with `caller_id`, `callee_name`, `receiver_hint`, `arg_bindings`, and `resolution: resolved | ambiguous | unresolved`. `arg_bindings` captures `literal_value` for empty/default literals (`""`, `None`, `0`, `[]`, `{}`). This is the mechanical substrate for the dead-parameter and call-graph-delta reports.
- **E3 — Field-I/O pass.** Every read/write of a class/struct/module field becomes a `field_io` record with `op: read | write` and `op_detail: assign | append | extend | inplace-op | setitem | method-mutation | …`. Catches the accumulate-vs-rebuild and first-write-vs-latest-wins drifts that the old pass missed.

**Run the extractor:**

```bash
python "<skill-dir>/scripts/extract-inventory.py" <target-repo> -o clean-room/inventory.json
```

Supports Python, JavaScript, TypeScript (+tsx), Go, Rust via `tree_sitter_language_pack` (install once with `pip install tree-sitter-language-pack`). **Python has full v2 support** (E1 + E2 + E3). JS/TS/Go/Rust run Pass E1 only in this revision; their `call_edges` / `field_io` are empty arrays and remain targets for follow-up extension. The reports degrade gracefully on partial coverage.

Output (`clean-room/inventory.json`, schema v2):
- `symbols[]` — every symbol with id, qualified_name, file, line, normalized signature, kind, Tier-1 tags, visibility, parent_id, enclosing_scope, optional content_snapshot, empty tier2 block.
- `call_edges[]` — resolved call graph with arg_bindings.
- `field_io[]` — read/write ledger with op_detail.
- Sorted deterministically — re-running on unchanged source produces byte-identical JSON.

**Tier-1 tags (deterministic, assigned here):**
- `kind` — one of: function, method, class, interface, type-alias, enum, struct, constant, variable, module
- `modifiers` — any of: exported, async, generator, abstract, static, readonly, deprecated, throws
- `shape` — any of: error-type, entrypoint, data-class, decorator, **prompt-template, regex, threshold, config-const**
- `location` — one of: source, test, fixture, migration, benchmark, example
- `visibility` — one of: public, private, nested

The closed vocabulary lives in `scripts/inventory-vocab.json` (v2) and the extractor rejects anything off-list. Extend the vocab deliberately; don't coin ad-hoc tags.

**Tier-2 tags (semantic, LLM-assigned):**

After extraction, run the enrichment pass to add `role` / `concern` / `risk` tags:

```bash
python "<skill-dir>/scripts/enrich-inventory.py" prompt clean-room/inventory.json -o clean-room/enrichment-prompts
# dispatch each prompt to a research subagent (one at a time, or in parallel)
# collect responses as clean-room/enrichment-responses/*.json
python "<skill-dir>/scripts/enrich-inventory.py" apply clean-room/inventory.json clean-room/enrichment-responses/*.json
```

The prompt is strict: it forbids returning code, identifiers, comments, or pseudocode — only tags from the vocabulary. The apply step re-validates every tag; an unknown value rejects the whole symbol's patch, not the whole response.

**How later passes consume the inventory:**

| Pass | Seeded from | What it adds |
|------|-------------|--------------|
| 3 (Public Contract) | symbols with `exported` modifier + `visibility: public`, filtered by `location: source` | docstrings, HTTP route / CLI surface, schemas, events |
| 4 (Modules) | symbols grouped by directory | responsibility prose, algorithms, collaborators |
| **4.5 (Integration Seams)** | `call_edges` + `field_io` walked from entry points (see below) | per-wire narrative: data meaning, invariants, break symptoms |
| 5 (Data Model) | symbols with `kind: class/struct/type-alias/enum/interface` and `shape: data-class` | invariants, DB schemas, wire formats |
| 7 (Errors) | symbols with `shape: error-type` and `modifiers: throws` | raise conditions, validation rules, failure recovery |
| 9 (Tests) | symbols with `location: test` | scenarios asserted, property invariants, fixtures |

Pass 3/4/5/7/9 subagents should receive the relevant inventory slice (via `jq`-style filter or a scoped view) alongside their read-only repo access — they enrich the skeleton with prose; they don't re-enumerate.

**Why this exists:** before inventory extraction, Pass 3 and Pass 9 depended on the analyzer LLM *noticing* every exported symbol and test — reliable for small repos, lossy above ~5k LOC. The inventory guarantees completeness by construction, and `COVERAGE.md` inherits that completeness. v2 extends the same guarantee to private helpers (C-pattern), call-graph wiring (E-pattern), and content-sensitive symbols like prompts and regexes (B-pattern).

Output section (in `DESIGN_DOC.md`): none directly. The inventory is a separate artifact consumed by other passes; they cite it rather than copying from it.

### Pass 2 — External Dependencies & Boundaries

- Every third-party dependency and what it's used for (grep imports)
- External services: DBs, APIs, queues, filesystems, env vars
- Network protocols, ports, wire formats
- Platform assumptions (OS, arch, GPU, etc.)

Output section: **"External Surface"**. Include version constraints — they often encode hidden behavior requirements.

### Pass 3 — Public API / Contract

- Every exported/public symbol: name, signature, types, docstring
- CLI commands, flags, subcommands, exit codes
- HTTP routes, request/response schemas, status codes
- Config file schemas and defaults
- Events emitted / consumed

Output section: **"Public Contract"**. This is what the rewrite MUST match exactly.

### Pass 4 — Module-by-Module Behavior

For EACH module/package:
- Responsibility in one sentence
- Inputs, outputs, side effects
- Key algorithms (describe in prose + pseudocode, never copy code)
- State it holds
- Collaborators (who calls it, who it calls)

Output section: **"Modules"**, one subsection per module. This is the longest section.

### Pass 4.5 — Integration Seams (wires)

Goal: catch the E-pattern failure mode — each module looks right in isolation but the wires between them don't carry signal. A parameter is always passed empty, or a field is written but never read, or a public method is never called.

**The LLM is not asked to discover wires.** The call graph already has them. The pass runs in two steps:

1. **Mechanical** (`scripts/generate-wire-ledger.py`): walks `call_edges` from every detected entry point in the inventory and emits one entry per producer → consumer edge. Each wire records the carried parameters, any fields the producer writes near the edge, and any fields the consumer reads. Output: `clean-room/wires.json` plus a seeded `## 4.5 Integration Seams` section appended to `DESIGN_DOC.md`.
2. **Prose** (subagent): annotates each wire with `what_data_represents`, `invariant`, and `if_broken_symptom`. Strict: no new wires — the subagent may only fill the prose fields on the mechanically-generated list. Contamination rules still apply in full clean-room mode (no verbatim code in responses).

**Run:**

```bash
python "<skill-dir>/scripts/generate-wire-ledger.py" clean-room/inventory.json \
  -o clean-room/wires.json \
  --design-doc clean-room/DESIGN_DOC.md
```

Every wire becomes a `COVERAGE.md` checkbox. Feed `wires.json` to `generate-coverage.py --wires clean-room/wires.json` to include them.

In Parity Mode the same machinery runs, and the differ (see below) emits a `call-graph-delta` report naming every wire present in the original's closure but absent from the rewrite's.

### Pass 5 — Data Structures & Persistence

- Core types/structs/classes with fields and invariants
- DB schemas, indexes, migrations
- Serialization formats (JSON shapes, protobuf, custom binary)
- File formats the system reads/writes
- Caching layers and eviction policies

Output section: **"Data Model"**. Include invariants — "field X is never null after init", "list Y is always sorted by timestamp desc".

### Pass 6 — Control Flow & Concurrency

- Request lifecycle from entry to response
- Async/concurrency model: threads, async tasks, actors, workers
- Locks, channels, queues, shared state
- Startup/shutdown sequence
- Retry/backoff/timeout policies

Output section: **"Control Flow"**. Include sequence diagrams (mermaid) for non-trivial flows.

### Pass 7 — Edge Cases, Errors, Validation

- Every error type and when it's raised
- Input validation rules
- Known edge cases handled (empty inputs, overflow, unicode, etc.)
- Failure modes and recovery
- Security-relevant checks (auth, authz, sanitization, rate limits)

Output section: **"Error & Edge Case Catalog"**. Missing an entry here is the #1 cause of rewrite divergence.

### Pass 8 — Cross-Cutting Concerns

- Logging: what's logged, at what level, format
- Metrics / observability
- Configuration loading and precedence
- Feature flags
- i18n / l10n
- Authentication & authorization patterns

Output section: **"Cross-Cutting"**.

### Pass 9 — Test Behavior Extraction

Tests encode behavior the code alone doesn't make obvious.

- For each non-trivial test: what scenario it exercises and the asserted behavior
- Property-based tests: the invariants being asserted
- Fixtures / golden files: what they represent

Output section: **"Behavioral Specifications from Tests"**. These become acceptance criteria for the rewrite.

### Pass 10 — Verification & Gap Hunt

Re-read the design doc WITHOUT looking at code. For each section, ask:
- "If I handed this to someone who can't see the source, could they reimplement it correctly?"
- "Where would they have to guess?"

Then open the source again and fill the guesses. Iterate until a gap-hunt pass produces no new gaps.

**For large codebases, also run targeted "deep dive" passes** on any module where Pass 4 felt shallow — production bugs hide in the modules you skimmed.

### Additional passes for large codebases (>50k LOC)

Add these between Pass 6 and Pass 10:
- **Hot-path pass** — profile/trace-hinted critical paths documented in detail
- **Historical pass** — skim `git log` for bug fixes and the behavior they encode (subtle constraints often live in fix commits, not current code)
- **Config/flag pass** — enumerate every feature flag and non-default config branch

## Design Doc Template

```markdown
# <Project> Design Document (Clean Room)

## 0. Scope & Goals
What this rewrite must replicate. What is explicitly out of scope.

## 1. Repository Map
## 2. External Surface
## 3. Public Contract
## 4. Modules
### 4.1 <module-name>
  - Responsibility:
  - Inputs / Outputs / Side effects:
  - Algorithm (pseudocode):
  - State:
  - Collaborators:
## 5. Data Model
## 6. Control Flow
## 7. Error & Edge Case Catalog
## 8. Cross-Cutting
## 9. Behavioral Specifications from Tests
## 10. Open Questions / Assumptions
Anything the source didn't answer — resolve before implementation.
```

## Phase 2: Improvements & Enhancements

Goal: produce a deliberate list of ways the rewrite will be *better* than the original — then consolidate design + improvements into a PRP that Phase 3 can consume autonomously.

The clean-room rewrite is a rare opportunity to fix things the original got wrong. Don't waste it by producing a 1:1 copy. But also don't silently smuggle in changes — every improvement is an explicit, justified decision captured in `IMPROVEMENTS.md`.

### 2a. Agent-driven improvement sweep

Run these sweeps against `DESIGN_DOC.md`. Each sweep produces candidate improvements tagged by category. Dispatch parallel subagents per sweep when the host supports it; otherwise run the sweeps one at a time.

| Sweep | Looking for |
|-------|-------------|
| **Architecture** | Tight coupling, god modules, leaky abstractions, circular deps, missing seams for testing |
| **Performance** | O(n²) where O(n) works, redundant allocations, sync I/O that should be async, missing batching/caching, hot paths identified in §6 |
| **Correctness** | Edge cases silently dropped in §7, missing validation, race conditions in §6, error swallowing |
| **API ergonomics** | Inconsistent naming, awkward signatures, missing type safety, poor defaults, footgun configs |
| **Modernization** | Dated patterns, deprecated deps, newer stdlib/ecosystem features that replace hand-rolled code, idioms native to the target language |
| **Observability** | Missing structured logs, no metrics on key ops, no tracing, opaque failures |
| **Security** | Hardcoded secrets, missing authz checks, unsafe deserialization, injection surfaces, weak crypto |
| **Testing** | Untested code paths from §9 coverage map, missing property tests, slow or flaky test patterns |
| **DX / Tooling** | Slow builds, missing CI, no reproducible dev env, undocumented setup |
| **Docs** | Gaps between §3 contract and actual documented behavior |
| **Technical debt** | TODOs/FIXMEs in the original, commented-out code blocks, dead code, duplicated logic |

**(FUGAZI) — ground the sweeps deterministically.** If [FUGAZI](https://github.com/AP3X-Dev/FUGAZI) (`fugazi` / `fugazi-mcp`) is available, run it to back the Architecture, Performance, Correctness, and Technical-debt sweeps with hard findings instead of impressions: `fugazi circular-deps`, `fugazi boundaries`, `fugazi health` (complexity), `fugazi dupes`, `fugazi dead-code` (`--format json`). In Transparent/Parity mode point it at the original *and* the rewrite-in-progress; in full clean-room, the analyzer may run it on the original as another structural input. It also cross-checks Pass 1b for TS/JS where this skill's own `inventory.json` carries `call_edges`/`field_io` for Python only — FUGAZI's module-graph reachability fills that gap. Read-only; every finding is a candidate to triage in 2c, never an auto-edit (and never `fugazi fix` here).

### 2b. Human-driven improvement input

The human may have goals the agent can't infer. Surface a short questionnaire and capture answers into `IMPROVEMENTS.md` under a **"Stakeholder Directives"** section:

- What does the original do *poorly* that you want fixed?
- Target language/runtime if porting — and why?
- New platforms/clients to support?
- Performance / scale / latency targets?
- Compliance or regulatory constraints?
- Features to add / remove / defer?
- Deprecations: anything in the original you explicitly do NOT want to carry forward?

### 2c. Triage

Every candidate improvement gets scored:

- **Impact** (high / med / low)
- **Effort** (S / M / L / XL)
- **Risk** of behavior divergence (low / med / high)
- **Decision** — `accept` / `defer` / `reject`, with a one-line reason

Anything `accept`-ed becomes a requirement in the PRP. Anything `reject`-ed is still logged (so Phase 3 can't "helpfully" reintroduce it).

### 2d. Produce the PRP

Consolidate `DESIGN_DOC.md` + accepted `IMPROVEMENTS.md` entries into `PRP.md` following the `prp-template.md` bundled with the **autonomous-advisor** skill. The PRP is the **only input** Phase 3 receives.

The PRP must contain:
- **Goals & non-goals** (from §0 + Stakeholder Directives)
- **Functional spec** — the full public contract from §3, unchanged unless an accepted improvement modifies it
- **Data model** — from §5, plus accepted schema improvements
- **Behavioral acceptance criteria** — §9 test-derived specs
- **Improvements to apply** — each accepted item as an explicit requirement, not a suggestion
- **Explicit non-changes** — behavior that looks improvable but MUST be preserved (and why)
- **Rejected-improvements log** — so Phase 3 doesn't reinvent them
- **Success criteria** — measurable: tests pass, perf targets met, etc.

### `IMPROVEMENTS.md` template

```markdown
# Improvements Over Original

## Stakeholder Directives
(Human input from 2b)

## Candidates

### <category> / <short title>
- **Problem in original:** ...
- **Proposed change:** ...
- **Impact:** high | med | low
- **Effort:** S | M | L | XL
- **Risk of divergence:** low | med | high
- **Decision:** accept | defer | reject
- **Reason:** ...

## Accepted (-> flows into PRP)
- ...

## Rejected (DO NOT reintroduce in Phase 3)
- ...

## Deferred (future iterations)
- ...
```

## Phase 3: Autonomous Clean-Room Implementation

Hand off `PRP.md` to the **autonomous-advisor** skill when available. If it is not installed, use the fallback stack below: the important contract is PRP-only implementation, a run-state file, phase gates, and an advisor/verifier split (maker≠checker), not any particular plugin.

### Pre-flight checklist (enforce BEFORE dispatching)

In **Transparent Mode**, the items marked *(firewall)* below are skipped. All other items still apply — the design doc, inventory, improvements triage, and coverage tracking are the engineering value of this skill and remain mandatory.


- [ ] `clean-room/` directory exists at rewrite workspace root and is gitignored
- [ ] `clean-room/RUN_STATE.md` exists, mode locked, Phase & Pass Status current, gate results recorded with evidence
- [ ] (Optional) MemBerry Memory configured for the rewrite workspace if available (`## MemBerry Memory` section in `CLAUDE.md`, `berry_tools(action: "list")` succeeds) — if `memberry-setup` is available and not yet run, run it; otherwise note the skip (or an explicit opt-out) in `DESIGN_DOC.md` §0 and proceed. Not a blocker.
- [ ] `inventory.json` generated (Pass 1b, **schema v2** — `symbols[]`, `call_edges[]`, `field_io[]`) and Tier-2 enrichment applied
- [ ] Every `exported` + `location: source` symbol in `inventory.json` is either covered by the PRP or explicitly marked out-of-scope
- [ ] `clean-room/wires.json` generated (Pass 4.5); `DESIGN_DOC.md` §4.5 populated with prose per wire
- [ ] `DESIGN_DOC.md` passed Pass 10 gap-hunt with no new gaps
- [ ] `IMPROVEMENTS.md` triaged — every candidate has a decision
- [ ] `PRP.md` written from the `autonomous-advisor` template
- [ ] `COVERAGE.md` generated from DESIGN_DOC + accepted improvements + wires (`generate-coverage.py --wires clean-room/wires.json`); reviewed for granularity
- [ ] (Parity Mode) `PARITY_GAPS.md` regenerated from current inventories; all 10 report sections clean:
  - [ ] `missing` / `kind-drift` / `signature-drift` / `tag-drift` — every entry triaged
  - [ ] `call-graph-delta` — zero `missing-callee` entries with `pending` or `gap-to-close`
  - [ ] `dead-parameters` — zero `pending` / `gap-to-close` entries (soft in `--mode=project-initialization`)
  - [ ] `dead-reads` — zero `pending` / `gap-to-close` entries (soft in init mode)
  - [ ] `orphan-methods` — zero `pending` / `gap-to-close` entries (soft in init mode)
  - [ ] `content-diff` — zero `critical` entries with `pending` / `gap-to-close`
- [ ] (Full clean-room, any mode) `SELF_CHECK.md` run against the rewrite at Phase 3 hand-off; dead-parameter / dead-read / orphan-method / content-diff reports clean (or `--mode=project-initialization` documented in `DESIGN_DOC.md §0`)
- [ ] *(firewall)* Fresh worktree / fresh repo for the rewrite (no original source in the working tree)
- [ ] *(firewall)* Original source excluded from the agent's visible filesystem / context
- [ ] Success criteria in the PRP are *measurable* (tests, benchmarks, lint gates)
- [ ] Phase 3 instructions explicitly tell the implementer to update `COVERAGE.md` after each task and re-run `diff-inventory.py --self-check` after each wiring change

### Handoff

1. Start a fresh session. Do not carry conversation state from Phase 1/2.
2. Invoke [autonomous-advisor](../autonomous-advisor/SKILL.md) with the path to `PRP.md`, or run the host-neutral fallback stack below.
3. The implementation pipeline runs end-to-end:
   - Design phase — advisor answers as stakeholder using the PRP
   - Planning phase — implementation plan
   - Implementation phase — code + tests, with maker≠checker verification
   - Branch completion — merge/PR through the repo's normal workflow
   - Optimization loop — iterate until success criteria are met
4. Monitor only; do not intervene unless the advisor asks a question the PRP genuinely can't answer. If that happens, amend the PRP, then resume — do NOT answer ad hoc.

### If autonomous-advisor is unavailable

Fallback order:
1. Host-native subagent implementation, task-by-task with review checkpoints.
2. A separate execution session that follows the plan with explicit phase gates.
3. Manual implementation — still from PRP only, still no peeking at original, still verified by a separate checker.

### Reverse-Contamination Scan (Phase 3 + merge gate)

Before Phase 3 writes implementation code in full clean-room or Parity Mode, build the fingerprint. Run the scanner after the first code-producing milestone, again before each major milestone, and before the rewrite merges to its main branch. Waiting until final merge lets leaked terms spread through the rewrite before detection.

**Process:**

1. **Build a fingerprint.** Dispatch a research subagent with access to the original (see Escape Hatch). Its job: return a list of *distinctive* terms that would be suspicious if they appeared verbatim in the rewrite. Good candidates:
   - Rare internal identifiers (class/function names unlikely to be reinvented by chance)
   - Distinctive error message phrasings
   - Unique comment phrasings, if the original has them
   - Hand-picked magic numbers or string constants

   The subagent MUST exclude terms that are part of the public contract — those are supposed to match. Save output to `clean-room/fingerprint.txt`, one term per line, `#` comments allowed.

2. **Scan the rewrite:**
   ```bash
   python "<skill-dir>/scripts/contamination-scan.py" clean-room/fingerprint.txt <rewrite-root>
   ```

   Exit codes: `0` = clean, `1` = hits, `2` = usage error.

3. **Triage any hits:**
   - Legitimate match (public contract term that slipped into fingerprint): remove from fingerprint, rerun.
   - Accidental contamination (a research subagent leaked it, or implementer pattern-matched): rewrite the offending code in different terms; rerun until clean.
   - Systemic leak (many hits clustered in one module): treat as a firewall breach — quarantine that module, regenerate its portion of `DESIGN_DOC.md` via fresh research subagents with stricter instructions, and rewrite.

4. **Regenerate periodically.** The fingerprint grows stale as the rewrite evolves. Regenerate it before each major milestone and before final merge.

**Gate rule:** Phase 3 may not proceed past its first code-producing milestone until the scanner has run once against the current rewrite, and final merge is blocked until the scanner exits 0 on the current HEAD. Record the clean-scan commit SHA in the PR description for provenance.

### Ambiguity protocol

If Phase 3 surfaces a question:
- **Zeroth:** check `clean-room/failed-attempts.md` — if this exact question/approach was already tried and rejected, do not repeat it; go straight to the next rung.
- **First:** return to `DESIGN_DOC.md` — was the detail there but missed in the PRP? Fix PRP, resume.
- **Second:** dispatch a **research subagent** (see Escape Hatch above) to inspect the original and return findings/pseudocode. Append findings to `DESIGN_DOC.md`, propagate to PRP, resume. A rejected dispatch (returned verbatim code, was re-done with stricter instructions) gets a row in `failed-attempts.md` with what to instruct differently.
- **Third (heavy gaps):** return to Phase 1 — run a targeted deep-dive pass on the relevant module. Update `DESIGN_DOC.md`, propagate to PRP, resume.
- **Never:** load the original source into the implementer's own context.
- **Always:** failed fix attempts during parity closure or implementation get a `failed-attempts.md` row (what was tried, symptom, lesson) so no later session burns a cycle re-walking the dead path.

## Generated agents

Copy-ready generated agents live in [../agents/README.md](../agents/README.md) and are sourced from [../agents/manifest.json](../agents/manifest.json). Install only the roles needed for the active clean-room run: `clean-room-analyzer`, `clean-room-researcher`, `clean-room-gap-checker`, `clean-room-improvement-sweeper`, `clean-room-contamination-reviewer`.

## Quick Reference

| Question | Where it's answered |
|----------|---------------------|
| What does the system do? | DESIGN §0, §1 |
| What must the rewrite match bit-for-bit? | DESIGN §3, §5 |
| How does it behave at runtime? | DESIGN §4, §6 |
| What breaks it? | DESIGN §7 |
| What are the hidden rules? | DESIGN §9 (tests) |
| What's being improved? | IMPROVEMENTS.md → Accepted |
| What must NOT change? | PRP "Explicit non-changes" |
| What does "done" look like? | PRP "Success criteria" |

## Phase Gates

A gate is runnable where possible — a command whose exit code decides, recorded with its evidence in `RUN_STATE.md` → Gate Results. Prose checks are verified by **fresh eyes**: an agent that did not author the artifact (maker≠checker — the doc's author re-reading its own doc finds the gaps it already knew to look for).

| Gate | Runnable checks (exit code decides) | Fresh-eyes checks |
|------|--------------------------------------|-------------------|
| **1 → 2** | `grep -nE "\bTODO\b|\bTBD\b|see source" clean-room/DESIGN_DOC.md` finds **nothing** (grep exits 1); `inventory.json` + `wires.json` exist; `generate-coverage.py` runs clean | Pass 10 gap-hunt run by a **fresh subagent that did not write the doc**, producing no new gaps |
| **2 → 3** | `PRP.md` exists; pre-flight checklist every box checked | Every `IMPROVEMENTS.md` candidate has a Decision line; PRP success criteria are measurable (a named command/benchmark, not "works well") |
| **During 3** | `COVERAGE.md` item flips to `[x]` only with its acceptance test passing | If ambiguity surfaces, fix doc/PRP — never show original source to implementer |
| **Merge** *(full clean-room)* | `contamination-scan.py` exits 0 on current HEAD — record the SHA in `RUN_STATE.md` and the PR | — |

## Red Flags — STOP and Fix

- Resuming a run without reading `RUN_STATE.md` first — or with the mode unknown → assume full clean-room (firewalled), reconstruct the state file from artifacts, and only then touch anything else. Guessing Transparent on a firewalled run is unfixable.
- Treating "internal", "time-boxed", or "both repos are local" as permission to document the legal/IP posture later → lock the mode first.
- Implementer directly reads the original source → contamination; use a research subagent instead and throw away the implementer's current context
- Research subagent returns verbatim source/test code, exact internal identifiers, exact non-public error strings, or comments → reject its output wholesale, re-dispatch with stricter instructions
- Calling function names or exact error strings "parity markers" when they are not public contract terms → contamination-sensitive material, not implementation guidance
- Skipping AST inventory/diff because the gaps are "already known" → the gap list is ungrounded
- Deferring contamination scan until final merge → too late; fingerprint before Phase 3 and scan after the first code-producing milestone
- "Compare, port, test, tighten afterward" → direct porting, not clean-room
- Design doc has "TODO" or "see source" → not done; run more passes
- A module's §4 entry is <3 sentences → shallow; re-read that module
- Skipping Pass 10 because "the doc looks complete" → it isn't; verify
- Combining passes "to save time" on a large repo → you will miss edge cases in §7 and §9
- Phase 2 produced zero rejected improvements → you didn't actually triage; agents accept too eagerly
- PRP success criteria are unmeasurable ("works well", "is fast") → autonomous-advisor can't know when to stop
- Phase 3 asks a question and you answer it in chat → amend the PRP instead, so the decision is durable
- Original source is reachable from the Phase 3 working tree → move it out before dispatching

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| One giant read-through instead of passes | Each pass has a single lens; you cannot see everything at once |
| Paraphrasing code as pseudocode too literally | Describe *intent and invariants*, not statement-by-statement translation |
| Ignoring tests | Tests are where behavior hides; Pass 9 is non-negotiable |
| Leaving assumptions implicit | §10 exists to surface them; resolve before implementing |
| Letting the implementer "just check one thing" in the original | Forbidden. Go back to the analyzer role instead |

## Real-World Signal

If the rewrite's test suite (built from §9) passes but integration against real callers fails, the gap is almost always in §7 (edge cases) or §5 (invariants) — not §3. Invest extra passes there for large systems.
