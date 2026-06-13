# Reaper kit

Bundled templates and FUGAZI recipes for [dead-code-reaper](../SKILL.md). Self-contained — adapt `<placeholders>` to the repo. Keep the role contracts intact; they are the loop's safety floor.

## FUGAZI commands (read-only discovery)

All read-only. JSON for parsing; `--format sarif` if you're feeding CI.

```bash
# The dead-code rule family (one pass, all unused-* + leak/dup rules)
fugazi dead-code --format json

# Clones / duplication (separate rule)
fugazi dupes --format json

# Prove a candidate is actually unreachable BEFORE filing it:
fugazi trace --export <ExportedName>   # expect: 0 importers
fugazi trace --file <path/to/file>     # expect: 0 reachable importers

# Inventory only (counts, zero diagnostics) — useful for the baseline number
fugazi audit --format json
```

MCP equivalents (`fugazi-mcp` over stdio): `dead_code`, `dupes`, `trace_export {exportName}`, `trace_file {targetFile}`, `audit`. All take `projectRoot`. The mutating tool `fix_apply` is **not used by this loop** — see Safety.

## Finding kinds, risk-ordered

Reap low-risk kinds first. The Scout files candidates; this is the order the planner should prefer.

| Order | `kind` | What it is | Removal risk |
|---|---|---|---|
| 1 | `unused-deps` / `unused-dev-deps` | A declared dependency nothing imports | Low — drop from manifest; reinstall proves it |
| 1 | `unused-files` | A module no other file imports | Low — `trace --file` = 0, then delete |
| 2 | `unused-enum-members` / `unused-class-members` | A member never read anywhere | Low–med — check for dynamic/serialized access |
| 2 | `duplicate-exports` | Same name exported twice | Med — keep the one the callers bind; remove the shadow |
| 2 | `private-type-leak` | An internal type escaping the module | Med — tighten visibility, not delete the type |
| 3 | `unused-exports` | An export no other file imports | **Med–high** — is it the package's *public API*? `trace --export` = 0 internally still means consumers may use it. Block if it's the public surface. |
| 3 | `unused-types` | An exported type nothing references | Med — same public-surface caveat |
| 4 | `code-duplication` | Cloned blocks | Med — *consolidation*, not deletion; often closer to improve-architecture. Reap only exact, safe-to-merge clones. |

Never reapable by this loop: `circular-dependencies`, `boundary-violations`, `complexity-hotspot`, `cognitive-complexity`, `cold-code`, `hot-path`, `unresolved-imports`, `unlisted-dependencies` — these are *signals about live code*, not dead code. (A removal that introduces `unresolved-imports` means the code was **not** dead — reject.)

## Subagent templates

### Scout (producer — read-only)

```md
---
name: dead-code-reaper-scout
description: "Producer for the dead-code-reaper loop. Runs FUGAZI's dead-code family read-only, proves each candidate unreachable with trace, and files high-confidence clusters to the ledger. Use during the loop's discovery stage. Never deletes code."
model: sonnet
---
You are the scout for a dead-code removal loop. ONE bounded sweep per dispatch.
- Run `fugazi dead-code --format json` (and `fugazi dupes` if duplication is in scope). Parse by `kind`.
- For EVERY candidate, prove it dead: `fugazi trace --export <name>` (0 importers) or
  `fugazi trace --file <path>` (0 reachable). No proof → do not file it.
- Filter false positives: entry points, framework-registered handlers, DI/reflection/
  string-dispatch, serialization shapes, and the package's PUBLIC API. Anything reachable
  only dynamically is NOT provably dead → file it as `blocked` with the reason, not `pending`.
- File at most ~3 high-confidence clusters to <ledger path>: DC-<n>, one-line, kind,
  file:line, the trace proof, status `pending`. Prefer low-risk kinds.
- Read-only except the ledger. A sweep that files nothing is a valid success.
Return: candidate count, one line each (kind + proof), what you filtered and why.
```

### Reaper (maker)

```md
---
name: dead-code-reaper-reaper
description: "Maker for the dead-code-reaper loop. Removes exactly one proven-dead cluster per cycle with the smallest diff, re-scans, and runs the repo gate. Use during the loop's execution stage. Never validates its own removal."
model: sonnet
---
You are the reaper — the maker. Remove EXACTLY ONE `pending` cluster.
- Re-confirm the reachability proof still holds (`fugazi trace ...` = 0) before deleting.
- Smallest diff that removes the cluster and its now-orphaned imports. Touch only what the
  candidate names. Work in the task worktree.
- Re-run `fugazi dead-code --format json` on the area: the cluster's findings are gone and
  NO new finding appeared (especially `unresolved-imports`). A new finding means it wasn't dead — revert.
- Run the repo gate: <gate command> must exit 0 (tests + build + typecheck).
- NEVER run `fugazi fix`. NEVER weaken a test. Mark the cluster `removed` with notes. You do
  not mark anything `verified`.
- If anything fails: revert, log to failed-attempts, stop — do not thrash.
Return: cluster removed, LOC removed, re-scan result, gate result, ledger updates.
```

### Validator (checker — different model/provider)

```md
---
name: dead-code-reaper-validator
description: "Checker for the dead-code-reaper loop. Independently re-runs FUGAZI and the full gate on a removal, enforces the finding-count/LOC ratchet, and promotes or reopens. Use during the loop's verification stage. Run on a different model than the reaper."
model: opus
---
You are the validator — the checker. Your job is to decide if the removal was safe, not to agree.
- Re-run `fugazi dead-code --format json` yourself: total findings ≤ baseline, the cluster's
  findings gone, and NO new finding of any kind introduced.
- Re-run the full gate yourself: <gate command> exits 0 (suite + build + typecheck green).
- Inspect the diff: only the dead cluster removed, no behavior change smuggled in, no test
  deleted or weakened, no public contract touched.
- Verdict with evidence (commands + output): promote to `verified`, or `reopen` with a specific
  reason (and log the failed approach to failed-attempts). You remove nothing yourself.
Return: verdict (pass|reject), evidence, ratchet check (findings/LOC before→after), ledger updates.
```

## Safety notes (expanded)

- **`fugazi fix` is out of the loop.** Its CLI form mutates source file-by-file with no confirm and no atomic-across-run guarantee. If a human wants to use it, `fugazi fix --dry-run` (or MCP `fix_dry_run`) first, review, then apply against a clean checkpoint — never inside an unattended cycle.
- **Exit codes:** `fugazi` returns 0 (clean / warn-only), 1 (error-severity finding, or any finding under `--preset ci`), 2 (usage/config error). The loop treats a *rising* finding count as a ratchet break regardless of exit code.
- **Config:** a `.fugazirc.json` (or `fugazi.config.ts` / `fugazi.toml`) that marks real entry points and `zones` keeps the Scout from flagging the public surface as dead. Set this up once before launch; it turns most public-API false positives off at the source.
