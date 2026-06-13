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
- The code is *live but ugly* (shallow modules, tangled seams) — that's **improve-architecture**, not removal.
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

**The ratchet:** total FUGAZI finding count must be **≤** baseline and LOC **lower**, with the suite, build, and typecheck green. If a removal *creates* a finding (e.g. `unresolved-imports` because something did use it) the ratchet broke — **reject and reopen**. Floors only advance.

## Safety

- **Never run bare `fugazi fix` unattended.** It mutates source with no confirmation gate and is file-by-file non-atomic. The Reaper does its own surgical removal and runs the gate; if you ever use FUGAZI's fixer, it's `fix_dry_run` → human/Validator-gated apply, never in the loop body.
- **The deletion test.** "Unused internally" is not "safe to delete" for a library's public surface — that's the API, used by consumers FUGAZI can't see. Public exports flagged unused → `blocked` + human decision, unless config marks the real entry points. This mirrors the rule: never silently drop a supported feature.
- **Dynamic reachability → blocked.** Reflection, DI, string-keyed dispatch, plugin registration, `__all__`/serialization. If usage could be dynamic, it isn't provably dead.
- **One cluster per cycle.** Batched deletions make the Validator's job ambiguous and rollbacks expensive.

## Build, then offer launch

Scaffold via [loop-engineer](../loop-engineer/SKILL.md) (state spine, `AGENTS.md`, driver), drop the three agents (templates in [references/reaper-kit.md](references/reaper-kit.md)), pin the gate, and **dry-run exactly one cycle**. Then stop and **offer** the human launch — a scheduled `/loop` or a cron cold-start. Do not auto-launch a loop that deletes code; the spend and the risk are the human's call. Start at autonomy Level 2: the loop commits locally; a human reviews diffs and pushes.

## Generated agents

Copy-ready generated agents live in [../agents/README.md](../agents/README.md) and are sourced from [../agents/manifest.json](../agents/manifest.json). Install only the roles needed for the active dead-code run: `dead-code-reaper-scout`, `dead-code-reaper-reaper`, `dead-code-reaper-validator`.

## Common Mistakes

- **Deleting without a reachability proof.** FUGAZI's `unused-*` is the candidate; `trace` returning zero importers is the proof. File only proven clusters.
- **Reaping a bug.** Code that's dead because a wire was never connected is a *defect*. Removing it makes the missing feature permanent. Route ambiguous cases to diagnose-loop.
- **Treating public API as dead.** The most expensive mistake — deleting the package's surface because nothing inside calls it. Block it; ask.
- **Running `fugazi fix` in the loop.** Unattended source mutation with no gate. The loop removes deliberately and verifies; the fixer is a manual, dry-run-first tool.
- **Batching removals.** One cluster per cycle keeps each diff attributable and each rollback cheap.

---

*A loop built on [loop-engineer](../loop-engineer/SKILL.md) conventions, in the same shape as [bug-pipeline](../bug-pipeline/SKILL.md) — three roles, a shared ledger, a runnable gate, maker≠checker — but specialized for safe removal with FUGAZI as the reachability oracle.*
