---
name: arch-drift-watch
description: "Use when an established repository needs continuing read-only architecture drift detection between reviews. In guardrail-pack mode it consumes guardrail-forge's approved policy, exact baseline/exceptions, and canonical machine-readable verifier; in standalone mode it runs configured FUGAZI boundaries/cycles/complexity/dupes against agent-state/ARCH_BASELINE.json. Each cycle files only new violations and never redesigns policy, advances a baseline, or fixes code. Choose one source mode explicitly and fail closed; never silently fall back. NOT for bootstrapping policy (use guardrail-forge), deciding refactors (use improve-architecture), dead-code removal, or general hardening."
---

# Architecture Drift Watch

Architecture entropy compounds quietly — each AI-assisted change can add a little coupling, a cycle, a cross-seam reach, until the codebase is hard to change. Periodic reviews ([improve-architecture](../improve-architecture/SKILL.md)) catch it, but only when you run them. This loop is the **smoke detector between reviews**: it watches the structural metrics on a schedule and raises a flag the moment *new* drift appears — without ever deciding what to do about it. Deciding stays human.

**Output:** a committed structural **baseline**, a scheduled watch loop, and a triage inbox that accumulates *new* drift (not the whole backlog) for the next architecture review. Detection-only by default; it writes findings, not code.

## When to Use

- You want continuous early warning on architecture drift between manual reviews.
- A codebase under heavy AI-assisted change where coupling/cycles creep in unnoticed.
- You want new boundary or cycle violations to surface the day they land, not at the next quarterly review.

## When NOT to Use

- Deciding *which* refactor to do, or designing the deepening — that's **improve-architecture** (human judgment; this loop only detects).
- Removing dead code — **dead-code-reaper**.
- A broad quality pass with a fix backlog — **optimization-loop**.
- A one-shot first-principles reshape plan for a subsystem — **rebuild-panel** (a deep read on demand; this loop watches for *new* drift on a schedule).

## Choose one evidence source mode

Record the mode in `agent-state/loop-state.md`; never autodetect or switch modes
during a cycle.

### Guardrail-pack mode

Use this after [guardrail-forge](../guardrail-forge/SKILL.md) has closed Level 2.
It requires `.architecture/policy.yaml`, `baseline.json`, `exceptions.yaml`,
`decisions.json`, `verification.json`, the canonical verifier, and the generated
adapter. An architecture owner initializes the first clean handoff explicitly:

```text
python scripts/architecture/watch_guardrail.py --initialize --decision-id <handoff-decision> --approved-by <owner-id>
```

Before initialization, run the adapter once to obtain its blocked authority
digest, then record an approved `watch-handoff` decision for that exact digest in
`.architecture/decisions.json` and commit it with the reviewed pack. The adapter
reads the decision from `HEAD`, requires the working copy to match, and rejects
invented/uncommitted IDs or a preloaded cursor without committed authority. It
also requires every pack, tool, generated hook/workflow, validator, fixture, and
required evidence file needed to reproduce the handoff to be tracked and
Git-blob-equivalent to `HEAD`,
even when an index flag such as `assume-unchanged` hides the working-tree edit.
All Git authority reads discard inherited `GIT_*` overrides, and sanitized Git
must identify the requested directory as the exact worktree root. Working
authority files are compared directly to raw `HEAD` blobs without invoking
`.gitattributes` clean filters. Hook/workflow wrappers require exact raw bytes;
other authority files permit only CRLF-to-LF platform normalization.

Normal cycles run `python scripts/architecture/watch_guardrail.py`. The adapter
invokes the canonical `--repo-only --format json` verifier and emits
`guardrail-watch-v1`. It requires a stable repository snapshot, `complete: true`,
at least one rule, matching authority, stable rule IDs, exact fingerprints,
routing kinds, owners, paths, and messages. Any malformed output, exit `2`,
missing approval/verification/artifact binding, expired exception, empty rule
set, or unapproved authority change blocks without advancing the cursor. After
the cursor write it reruns verification, recomputes effective authority, and
repeats committed-file checks; any difference rolls the cursor back and blocks.
The newly written cursor is bound to its filesystem identity and exact bytes
before, during, and after final validation. A concurrent replacement is never
overwritten during rollback and forces a blocked result.
Do not
fall back to FUGAZI or text scanning because the pack is temporarily broken.

The approved `.architecture/baseline.json` is authoritative in this mode. The
canonical verifier applies its exact legacy fingerprints and exceptions; every
finding returned by the adapter is active drift and always keeps exit `1`.
The adapter compares fingerprints to
`agent-state/architecture-guardrail/watch-cursor.json` from the last complete
scan to classify new, persisting, and resolved findings, then atomically advances
it. That exact path is the only writable cursor location; custom paths,
symlinks, and Windows junction ancestors are invalid. The adapter re-runs verification after the
write and restores the prior cursor bytes exactly if the result changes. The cursor is
operational state, not a second policy baseline or suppression
list. Editing it can alter labels but can never suppress a current finding or
turn drift green. An authority change needs a clean scan plus an explicit
`--accept-authority-change` handoff decision and owner.

### Standalone FUGAZI mode

Use when no guardrail pack has been installed. This is the scheduled,
baseline-diffed front-end to [FUGAZI](https://github.com/AP3X-Dev/FUGAZI)'s
structural rules. It needs `fugazi boundaries`, `circular-deps`, `health`, and
`dupes`, with `.fugazirc.json` architecture zones.

If FUGAZI/equivalent is missing or zones are not configured with the user, stop
and record the blocker. Do not replace it with `rg`, guessed directory
boundaries, or suspicious text matches.

## The baseline — why drift, not findings

The core idea: **report the delta, not the backlog.** A first run on a real codebase finds dozens of pre-existing violations; re-reporting them every cycle is noise that trains everyone to ignore the loop. Instead, snapshot the current findings once as the **baseline**, commit it, and each cycle file only what's *new since the baseline*.

In standalone mode, `agent-state/ARCH_BASELINE.json` holds per-kind finding
fingerprints and `drift = current_findings - baseline`. In guardrail-pack mode,
`.architecture/baseline.json` holds exact per-rule legacy fingerprints and the
canonical verifier returns only active drift. Do not create or compare against a
second architecture baseline in pack mode.

Either baseline advances **only when a human accepts** the new state after review
— never silently, or the watch goes blind.

"Baseline today's state" is not permission to overwrite an existing baseline or launder unknown drift. If a baseline already exists, advance it only after explicit human acceptance tied to a review/ADR.

## The cycle (detection, Level 1 default)

Runs on a schedule; reads, never writes code.

1. **Preflight** — clean tree; read the baseline and loop state.
2. **Scan** — run the configured mode only: generated guardrail watcher adapter, or
   FUGAZI commands with `--format json`; read-only.
3. **Diff** — in pack mode, consume the adapter's complete classification; in standalone mode, subtract
   `ARCH_BASELINE.json`.
4. **Route + file** — write each new violation to `agent-state/triage-inbox.md` with `kind`, `file:line`, "new since `<baseline-SHA>`", and a suggested owner:
   - `boundary-violations` / `circular-dependencies` / `complexity-hotspot` → **improve-architecture candidate** (human-judged refactor).
   - `code-duplication` → **dead-code-reaper** / consolidation candidate.
   - If the analyzer output cannot produce a concrete kind, location, baseline SHA, and owner, record a blocker instead of filing a vague triage row.
5. **Report/state** — file new drift, report persisting/resolved counts, and only
   trust the adapter to advance the operational cursor only after a complete scan. A clean cycle
   files a one-line no-drift note and stops.

No code, policy, validator, exception, decision, verification, or baseline
changes—detection only. The human runs improve-architecture on what the inbox
surfaced and then separately approves any pack/baseline update.

The repo audit gate is still required for this jar, but green audit output does
not make a drift run safe. Safety requires a complete configured source mode,
its authoritative baseline, exact routing, and maker-checker separation for any
later fix.

## Autonomy — detection earns auto-fix

- **Level 1 (default): detection-only.** Watch, diff, file to the inbox. Zero code writes. This is the safe, correct default — structural fixes are judgment calls.
- **Level 2+ (earned): separate trivial auto-fix.** The watcher still does not fix during the detection cycle. Only the narrow, mechanical, reversible drift — a newly-introduced import cycle a single move breaks, an obvious duplicate — may be handed to a separate maker→verifier pair (loop-engineer's split) behind the full gate. Anything requiring a *design decision* stays in the inbox for a human. Raise the level only after cycles show the inbox routing is trustworthy.

## Optional: MemBerry

If a MemBerry-style memory MCP is available, index accepted waivers and their
committed exception/baseline decision for explanation and provenance. Memory
never mutes a finding by itself; only the deterministic committed pack can do
that. Skip MemBerry if absent.

## Build, then offer the schedule

Scaffold via [loop-engineer](../loop-engineer/SKILL.md) at Level 1. For pack mode,
initialize the generated adapter from the approved clean handoff and dry-run one
normal adapter cycle.
For standalone mode, configure FUGAZI zones with the user, capture the baseline on
the current commit, and dry-run one cycle. Then **offer** a schedule—never
auto-arm it—because even read-only cycles consume runs.

## Generated agents

Copy-ready generated agents live in [../agents/README.md](../agents/README.md) and are sourced from [../agents/manifest.json](../agents/manifest.json). Install only the roles needed for the active watch: `arch-drift-watcher`.

## Common Mistakes

- **Re-reporting the whole backlog.** Without a baseline, every cycle screams about pre-existing violations and gets muted. Drift is the delta.
- **Auto-fixing structural judgment.** Breaking a cycle can mean a real design decision. Detection routes to a human; it doesn't refactor on its own.
- **Letting the baseline drift silently.** If the baseline advances without a human accepting the new state, accumulating drift becomes the new "normal" and the watch is blind. Advance it only on acceptance.
- **No zones configured.** `boundary-violations` is meaningless without `.fugazirc.json` zones declaring the intended architecture. Configure them first.
- **Silently falling back between modes.** A broken guardrail pack is a blocker,
  not permission to run FUGAZI or text scans against different semantics.
- **Creating a second baseline in pack mode.** The generated exact baseline is
  already authoritative; a second snapshot can hide or duplicate drift.
- **Treating audit green as enough.** The jar gate proves the skill pack is structurally valid; it does not replace FUGAZI, zones, baseline diffing, or exact routing.

---

*The detection half of [improve-architecture](../improve-architecture/SKILL.md) — that skill owns the judgment (what to deepen, how), this loop owns the watch (what changed, when). Runs on [loop-engineer](../loop-engineer/SKILL.md) conventions; routes duplication to [dead-code-reaper](../dead-code-reaper/SKILL.md).*
