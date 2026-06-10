# Drift kit

Bundled FUGAZI recipes, the baseline/diff mechanics, and the detection-agent template for [arch-drift-watch](../SKILL.md). Self-contained — adapt `<placeholders>`.

## FUGAZI structural scan (read-only)

```bash
fugazi boundaries    --format json   # boundary-violations (needs zones in .fugazirc.json)
fugazi circular-deps --format json   # circular-dependencies
fugazi health        --format json   # complexity-hotspot / cognitive-complexity
fugazi dupes         --format json   # code-duplication
```

MCP equivalents: `boundaries`, `analyze` (filtered), `health`, `dupes` — all take `projectRoot`. Keep everything read-only; this loop never calls `fix_apply` / `fugazi fix`.

## `.fugazirc.json` zones (prerequisite)

`boundary-violations` only has meaning when the intended architecture is declared:

```json
{
  "zones": {
    "domain":  { "pattern": "src/domain/**",  "canImport": [] },
    "app":     { "pattern": "src/app/**",      "canImport": ["domain"] },
    "infra":   { "pattern": "src/infra/**",    "canImport": ["domain", "app"] }
  }
}
```

A finding = an import that crosses a seam the zones forbid. Set these up with the user before capturing the baseline.

## Baseline + diff mechanics

```
ARCH_BASELINE.json  (committed)
  per finding: { kind, file, symbol }  — a stable fingerprint, not line numbers
                (line numbers drift with edits; fingerprint on file+symbol+kind)

each cycle:
  current  = scan()                       # set of fingerprints
  drift    = current − baseline           # NEW violations only
  resolved = baseline − current           # things that got fixed (report as good news)
  file `drift` to triage-inbox; never auto-edit baseline
```

Advance the baseline **only** when a human accepts the current state (post-review): re-snapshot `current`, commit it with the accepting commit, note the SHA. That commit is the new "since" reference.

## Routing table

| New finding `kind` | Inbox owner | Why |
|---|---|---|
| `boundary-violations` | improve-architecture candidate | A seam was crossed — design decision |
| `circular-dependencies` | improve-architecture candidate | Coupling/init hazard — may need a refactor |
| `complexity-hotspot` / `cognitive-complexity` | improve-architecture candidate | A module deepened the wrong way |
| `code-duplication` | dead-code-reaper / consolidation | Often mechanical to consolidate |

## Detection agent template (Level 1)

```md
---
name: drift-watcher
description: "Producer for the arch-drift-watch loop. Runs FUGAZI structural rules read-only, diffs against the committed baseline, and files NEW violations to the triage inbox. Use during the loop's scan stage. Writes no code; never edits the baseline."
model: sonnet
---
You are the drift watcher. ONE scan per dispatch, read-only.
- Run fugazi boundaries / circular-deps / health / dupes (--format json).
- Fingerprint each finding as {kind, file, symbol} and diff against ARCH_BASELINE.json.
- File ONLY new findings (not in the baseline) to <triage-inbox>: kind, file:line,
  "new since <baseline-SHA>", suggested owner (improve-architecture | dead-code-reaper).
- Report resolved findings (in baseline, gone now) as good news.
- Do NOT edit code. Do NOT edit the baseline (a human advances it on acceptance).
- A scan with zero new drift files a one-line "no drift since <SHA>" note and stops.
Return: new-drift count by kind, resolved count, inbox entries written.
```

For earned Level 2 trivial auto-fix, dispatch a maker→verifier pair from loop-engineer's subagent-templates behind the full gate — but only for mechanical, reversible drift; anything needing a design decision stays in the inbox.
