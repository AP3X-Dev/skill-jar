# Drift kit

Bundled guardrail-pack/FUGAZI recipes, mode-specific baseline/diff mechanics,
and the detection-agent template for [arch-drift-watch](../SKILL.md).
Self-contained—adapt `<placeholders>`.

## Guardrail-forge pack scan (preferred after forge handoff)

```text
python scripts/architecture/watch_guardrail.py
```

Initialize once from an approved clean Level 2 handoff with `--initialize`, a
decision ID, and owner. The ID must resolve to a committed approved
`watch-handoff` decision whose subject hash is the adapter's independently
computed authority and whose bytes match `HEAD`. All authority-bearing pack
files, canonical tools, generated hook and CI workflow, validator implementation
roots, fixtures, and required evidence/target files must be tracked and
clean-filtered blob-equivalent to
`HEAD`, bypassing index hints such as `assume-unchanged`; committing only
the decision is invalid. Require
`schema: guardrail-watch-v1`, `complete: true`, a
nonzero `rules_run`, and findings shaped as
`{rule_id, fingerprint, path, message, kind, owner, state}`.
Exit `0` is a complete clean scan, exit `1` is complete drift, and exit `2` is a
configuration/tool/incomplete-scan blocker. The watcher files exit-1 findings by
fingerprint and never changes `.architecture/policy.yaml`, `baseline.json`,
`exceptions.yaml`, `decisions.json`, or `verification.json`.

The pack's baseline is authoritative. The adapter compares complete-scan findings
to the only permitted cursor path,
`agent-state/architecture-guardrail/watch-cursor.json`, to classify new,
persisting, and resolved findings. It emits every active finding and exit `1`
regardless of cursor label. The cursor stores authority digest, scan time, and
observed fingerprints; it never suppresses a finding. Custom paths, symlinks,
and Windows junction ancestors are invalid. It advances atomically only after a complete scan, then
re-runs verification and restores the exact prior cursor bytes if the result changed. Do not
create `ARCH_BASELINE.json` or run the FUGAZI
recipe below in the same watcher. If the configured pack command is broken or
its authority digest changed without an approved handoff, stop rather than
changing source modes.

## Standalone FUGAZI structural scan (read-only)

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

## Standalone baseline + diff mechanics

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
name: arch-drift-watcher
description: "Producer for arch-drift-watch. Runs the configured guardrail-pack verifier or standalone FUGAZI scan read-only, compares against that mode's authoritative baseline/cursor, and files NEW violations. Use during the loop scan stage. Never edits policy or baseline."
model: sonnet
---
You are the drift watcher. ONE scan per dispatch, read-only.
- Read loop-state.md and run only its configured source mode.
- Guardrail-pack mode: run `python scripts/architecture/watch_guardrail.py`,
  require complete output, and treat every returned finding as active drift.
- Standalone mode: run fugazi boundaries / circular-deps / health / dupes
  (--format json), fingerprint each finding, and diff against ARCH_BASELINE.json.
- File ONLY new findings (not in the baseline) to <triage-inbox>: kind, file:line,
  "new since <baseline-SHA>", suggested owner (improve-architecture | dead-code-reaper).
- Report resolved findings (in baseline, gone now) as good news.
- Do NOT edit code. Do NOT edit the baseline (a human advances it on acceptance).
- A scan with zero new drift files a one-line "no drift since <SHA>" note and stops.
Return: new-drift count by kind, resolved count, inbox entries written.
```

For earned Level 2 trivial auto-fix, dispatch a maker→verifier pair from loop-engineer's subagent-templates behind the full gate — but only for mechanical, reversible drift; anything needing a design decision stays in the inbox.
