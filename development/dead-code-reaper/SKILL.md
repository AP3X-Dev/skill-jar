---
name: dead-code-reaper
description: "FUGAZI-native loop that safely removes confirmed-dead code — one trace-verified cluster per cycle, suite- and build-gated, with an independent verifier and a finding-count/LOC ratchet. A Scout runs FUGAZI's dead-code family and proves zero reachability with trace before filing a candidate; a Reaper removes exactly one cluster with the smallest diff; a Validator re-runs FUGAZI plus the repo gate and promotes or reopens. Builds and dry-runs the loop, then OFFERS launch — never auto-removes. Use when a codebase has accumulated dead code, unused exports/files/deps, or duplication to prune continuously and safely. NOT for a single obvious unused symbol (just delete it), live-but-ugly code (use improve-architecture), or defect repair (use bug-pipeline). Requires FUGAZI (CLI fugazi or fugazi-mcp) or an equivalent reachability analyzer."
---

# Dead Code Reaper

A specialized [loop-engineer](../loop-engineer/SKILL.md) loop whose discovery engine is **FUGAZI** and whose entire job is to make dead-code removal *safe to run unattended*. FUGAZI finds the dead code and proves it's unreachable; the loop is the harness that removes exactly one thing at a time, re-proves nothing broke, and keeps an independent agent between "removed" and "verified". Maker≠checker by construction: the Reaper that deletes never certifies its own deletion.

**Output:** a running prune loop in the target repo — a ledger, three role agents, a per-cycle driver — plus one verified cycle. Then it **offers** launch; it never auto-prunes. Deleting code is expensive to reverse, so the human owns the go.

## When to Use

- A codebase has accumulated dead weight — orphan files, unused exports, dead deps, leaked private types, duplicate definitions — and you want it pruned *continuously and safely*, not in one risky sweep.
- You want every removal backed by a reachability proof and a green suite, in a reviewable ledger.

[arch-drift-watch](../arch-drift-watch/SKILL.md) is the upstream detector that routes duplication / dead-code drift into this removal loop; this loop is the safe-removal sink for those findings.

## When NOT to Use

- One obvious unused symbol — just delete it and run the tests.
- The code is *live but ugly* (shallow modules, tangled seams) — that's **improve-architecture**, not removal. Provably single-use over-engineering in live code (a one-caller wrapper, a factory-for-one) that must stay behavior-identical is **simplify-loop**.
- The "dead" code is a defect (a wire that should be connected but isn't) — that's **diagnose-loop** / **bug-pipeline**; reaping it hides the bug.
- No reachability analyzer available and no test suite. Without FUGAZI (or equivalent) the discovery is guesswork; without a gate, "removed safely" is a rumor.

## Requires FUGAZI

This loop is built around [FUGAZI](https://github.com/AP3X-Dev/FUGAZI) (CLI `fugazi`, or the `fugazi-mcp` MCP server). It supplies the dead-code rule family and — critically — `trace_file` / `trace_export` reverse-reachability, which is how a candidate is *proven* dead before anything is deleted. An equivalent analyzer with reachability works too; the contracts below assume FUGAZI's finding `kind`s.

## The three roles

| Role | Job | Writes | Never |
|---|---|---|---|
| **Scout** (producer) | Run FUGAZI's dead-code family read-only; for each candidate, prove zero reachability with `trace`; file high-confidence clusters with `kind` + `file:line` + trace evidence | The ledger only | Deletes code; files a candidate it couldn't prove unreachable |
| **Reaper** (maker) | Remove exactly ONE `pending` cluster, smallest diff, in a worktree; re-run FUGAZI on the touched area (no new findings); run the repo gate | Code + the ledger | Removes two clusters; runs bare `fugazi fix`; deletes through a public contract |
| **Validator** (checker, different model) | Re-run FUGAZI (the cluster's findings gone, no new ones), re-run the full gate (suite + build + typecheck green), inspect the diff for behavior change; promote `verified` or reopen | The ledger + failed-attempts | Removes anything itself; approves without re-running the analyzer and the gate |

Run the Validator on a **different model/provider** than the Reaper where the host allows — a deletion that "looks safe" to one brain is exactly what the other should catch.

## The ledger — `DEAD_CODE_LEDGER.md`

Shared state, default `agent-state/DEAD_CODE_LEDGER.md`. Statuses change; rows are never deleted (a reopened removal is a lesson, not garbage).

```md
# DEAD_CODE_LEDGER.md

## Meta
| Field | Value |
|---|---|
| Last Scout Scan | <timestamp> |
| FUGAZI baseline (total findings) | <n> |
| Findings now / LOC removed / clusters verified | <n> / <n> / <n> |

## Candidates

### DC-1 — <one-line: what's dead>
- **Kind:** unused-exports | unused-files | unused-deps | unused-class-members | duplicate-exports | private-type-leak | code-duplication
- **Location:** <file:line(s)>
- **Reachability proof:** `fugazi trace --export <name>` → 0 importers  (or `trace --file` → 0 reachable)
- **Status:** pending → removed → verified  (or: reopened | blocked)
- **Reaper notes:** <what was removed + re-scan result>      <!-- set by Reaper -->
- **Validator notes:** <commands run + verdict basis>        <!-- set by Validator -->

## Scan Notes
<one entry per Scout sweep: command run, candidate count, what was filtered as
a false positive and why — a sweep that files nothing is still a valid cycle>
```

**Status flow:** `pending` (Scout) → `removed` (Reaper) → `verified` (Validator), or `reopened` (Validator, logged to failed-attempts), or `blocked` (a human must decide — see Safety).

## Discovery recipe

The Scout's read-only sweep. Exact commands and the full `kind` table live in [references/reaper-kit.md](references/reaper-kit.md); the shape:

1. **Scan:** `fugazi dead-code --format json` (and `fugazi dupes --format json` for clones). Parse findings by `kind`.
2. **Prove each candidate dead:** for an export, `fugazi trace --export <name>` must return **0 importers**; for a file, `fugazi trace --file <path>` must show 0 reachable importers. No proof → do not file it.
3. **Filter false positives** (FUGAZI's framework plugins help, but the Scout still checks): entry points, framework-registered handlers, DI/reflection/string-dispatch targets, serialization shapes, public package API. Anything reachable only dynamically is **not** provably dead — mark `blocked`, not `pending`.
4. **File** at most a few high-confidence clusters with the proof attached.

## The cycle (driver outline)

One cluster per cycle. Built on loop-engineer's spine; the reaper's shape:

1. **Preflight** — `git status` clean; read the ledger and loop state; record the FUGAZI baseline finding count if not set.
2. **Discovery** — skip if `pending` candidates remain; else run the Scout for one sweep.
3. **Planning** — pick one `pending` cluster (prefer the lowest-risk kind: `unused-files`/`unused-deps` before `unused-exports`); check failed-attempts first.
4. **Execution** — the Reaper removes it in a worktree and re-scans the touched area.
5. **Verification** — the Validator re-runs FUGAZI + the full gate and promotes or reopens.
6. **State update** — ledger reflects the status; commit code and ledger **together** (`reap(DC-N): <what>`).

**The ratchet:** total FUGAZI finding count must be **≤** baseline and LOC **lower**, with the **full** suite, build, and typecheck green. "Full" means the same gate the repo runs in CI — including a slow or flaky integration suite. You may not substitute `tsc --noEmit` + unit tests for the integration suite to dodge a 25-minute run; flakiness gets fixed or explicitly quarantined, never silently skipped. If a removal *creates* a finding (e.g. `unresolved-imports` because something did use it) the ratchet broke — **reject and reopen**. Floors only advance.

## Safety

- **Never run bare `fugazi fix` unattended.** It mutates source with no confirmation gate and is file-by-file non-atomic. The Reaper does its own surgical removal and runs the gate; if you ever use FUGAZI's fixer, it's `fix_dry_run` → human/Validator-gated apply, never in the loop body.
- **A static-analysis flag is a candidate, not a proof.** `ts-prune`, `depcheck`, `knip`, `unimported`, IDE "unused" hints, and even FUGAZI's `unused-*` rules find *suspects* by static reference counting. They cannot see dynamic reachability, so they do **not** clear a deletion. The proof is a `trace` (or hand-traced equivalent) returning **0 reachable importers** *after* you account for dynamic and out-of-repo use. No trace → no removal, regardless of how many tools flagged it.
- **The deletion test applies to internal services too.** "Unused internally" is not "safe to delete" for any surface a consumer FUGAZI can't see — a published package's API, *and* an internal service's HTTP routes, webhook DTOs, queue/job names, ORM-mapped columns, and anything another repo or runtime binds by name. "It's not an npm package" does **not** retire this test. Public-contract-shaped exports flagged unused → `blocked` + human decision, unless config marks the real entry points. This mirrors the rule: never silently drop a supported feature.
- **Dynamic reachability → blocked, and it is yours to defend.** Reflection, DI, string-keyed dispatch (`adapters[providerName]`, `registerJob('name', …)`), glob/registry wiring (`glob('**/*.handler.ts')`), framework decorators (`@Entity()`), barrel/index re-exports, `React.lazy(() => import(...))`, `__all__`/serialization. If usage *could* be dynamic, it is not provably dead — and "they shouldn't have used a string key" is not an exception. Block it; the cost of a wrong delete is yours, not the author's.
- **One cluster per cycle — deadlines do not relax this.** Batched deletions make the Validator's job ambiguous and rollbacks expensive. A freeze on Monday is a reason to be *more* careful, not to merge 22 files in one commit. Dependency removals are their own clusters (a `depcheck` "unused" dep can be a dynamic `require`, peer/optional dep, build-tool or runtime-config dependency) — never fold them into a code-removal cluster.

### Known pressure rationalizations

A fresh agent under deadline pressure reaches for these. Each is wrong here; the required response is the gate.

| Rationalization (the dodge) | Required response |
|---|---|
| "ts-prune/depcheck flagged it as unused — that's my reachability proof, I don't need to hand-trace 60 symbols." | The tool produced a *candidate*. Reachability proof = `trace`/hand-trace to 0 reachable importers including dynamic + out-of-repo use. Unproven → don't remove. |
| "The user said they already eyeballed these and to just blast through it — defer to the owner." | The user owns *launch and direction*, not the per-cluster proof. "Blast through" never waives the trace, the gate, or one-cluster-per-cycle. Confirm scope, then still prove each one. |
| "Zero static references = dead by definition; if something used it via a string key, that's a code smell on their end." | Dynamic/string-key/reflection use means **not provably dead** → `blocked`. It is not the author's problem to defend; it is your delete to justify. |
| "tsc --noEmit + unit tests pass = safe; the 25-min flaky integration suite isn't worth blocking a Friday merge, and flaky tests can't be trusted." | The gate is the **full** suite + build + typecheck. A slow/flaky integration suite is not optional; fix or quarantine flakiness explicitly, never silently downgrade the gate to skip it. |
| "Barrel/index re-exports nothing imports, plus `LegacyRefundHandler` and the V1 webhook DTO — textbook dead code, obviously safe to cut." | Barrel re-exports hide dynamic consumers; `*Handler` and `WebhookV*Payload`/DTO names scream registry/serialization/external-contract. These are the `blocked` cases, not the easy ones. |
| "Batch all 22 files into one cleanup commit — one PR, one CI run; 60 tiny commits would take all night." | One cluster per cycle, one commit per cluster. Reviewability and cheap rollback beat a tidy single PR, especially before a freeze. |
| "depcheck says these deps are unused — rip them from package.json in the same pass; fewer deps is the goal." | depcheck misses dynamic `require`, peer/optional deps, and build/runtime-config use. Each dep is its own proven cluster (reinstall + full gate), never folded into a code removal. |
| "These look like public API but it's an internal `payments-api`, not a published library — no external consumer to worry about." | Internal services have consumers the analyzer can't see: HTTP/webhook callers, queue/job names, ORM columns, other repos. The deletion test applies → `blocked`. |

## Build, then offer launch

Scaffold via [loop-engineer](../loop-engineer/SKILL.md) (state spine, `AGENTS.md`, driver), drop the three agents (templates in [references/reaper-kit.md](references/reaper-kit.md)), pin the gate, and **dry-run exactly one cycle**. Then stop and **offer** the human launch — a scheduled `/loop` or a cron cold-start. Do not auto-launch a loop that deletes code; the spend and the risk are the human's call. Start at autonomy Level 2: the loop commits locally; a human reviews diffs and pushes.

## Generated agents

Copy-ready generated agents live in [../agents/README.md](../agents/README.md) and are sourced from [../agents/manifest.json](../agents/manifest.json). Install only the roles needed for the active dead-code run: `dead-code-reaper-scout`, `dead-code-reaper-reaper`, `dead-code-reaper-validator`.

## Common Mistakes

- **Deleting without a reachability proof.** A static "unused" flag (FUGAZI's `unused-*`, `ts-prune`, `depcheck`, `knip`) is the *candidate*; `trace` returning zero *reachable* importers — after accounting for dynamic and out-of-repo use — is the proof. File only proven clusters.
- **Reaping a bug.** Code that's dead because a wire was never connected is a *defect*. Removing it makes the missing feature permanent. Route ambiguous cases to diagnose-loop.
- **Treating public API as dead.** The most expensive mistake — deleting the package's surface because nothing inside calls it. Block it; ask.
- **Running `fugazi fix` in the loop.** Unattended source mutation with no gate. The loop removes deliberately and verifies; the fixer is a manual, dry-run-first tool.
- **Batching removals.** One cluster per cycle keeps each diff attributable and each rollback cheap.

---

*A loop built on [loop-engineer](../loop-engineer/SKILL.md) conventions, in the same shape as [bug-pipeline](../bug-pipeline/SKILL.md) — three roles, a shared ledger, a runnable gate, maker≠checker — but specialized for safe removal with FUGAZI as the reachability oracle.*
