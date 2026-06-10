---
name: arch-drift-watch
description: "A scheduled detection loop that guards architecture against drift: each run executes FUGAZI boundaries / circular-deps / complexity (and dupes) read-only, diffs the findings against a committed baseline, and files only the NEW violations to a triage inbox — routing structural-judgment items to improve-architecture (human-owned) and offering small, safe auto-fixes only at higher autonomy. Detection-only by default (Level 1, no code writes). Builds the baseline and dry-runs one cycle, then offers the schedule. Use when you want continuous early warning on architecture entropy / AI-driven drift between periodic reviews. Requires FUGAZI. NOT for the judgment call of what to refactor (use improve-architecture), dead-code removal (use dead-code-reaper), or general hardening (use optimization-loop)."
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

## Requires FUGAZI

This loop is the scheduled, baseline-diffed front-end to [FUGAZI](https://github.com/AP3X-Dev/FUGAZI)'s structural rules. It needs `fugazi boundaries`, `circular-deps`, `health` (complexity), and `dupes` — with a `.fugazirc.json` declaring the architecture `zones` so `boundary-violations` means something. Without FUGAZI (or an equivalent structural analyzer + zone config) there's nothing to baseline.

## The baseline — why drift, not findings

The core idea: **report the delta, not the backlog.** A first run on a real codebase finds dozens of pre-existing violations; re-reporting them every cycle is noise that trains everyone to ignore the loop. Instead, snapshot the current findings once as the **baseline**, commit it, and each cycle file only what's *new since the baseline*.

`agent-state/ARCH_BASELINE.json` — per-kind finding fingerprints (file + symbol + kind), committed. `drift = current_findings − baseline`. The baseline advances **only when a human accepts** the new state (after a review fixes or knowingly accepts a violation) — never silently, or the watch goes blind.

## The cycle (detection, Level 1 default)

Runs on a schedule; reads, never writes code.

1. **Preflight** — clean tree; read the baseline and loop state.
2. **Scan** — `fugazi boundaries`, `circular-deps`, `health`, `dupes` (`--format json`), read-only.
3. **Diff** — subtract the baseline. Only genuinely new findings remain.
4. **Route + file** — write each new violation to `agent-state/triage-inbox.md` with `kind`, `file:line`, "new since `<baseline-SHA>`", and a suggested owner:
   - `boundary-violations` / `circular-dependencies` / `complexity-hotspot` → **improve-architecture candidate** (human-judged refactor).
   - `code-duplication` → **dead-code-reaper** / consolidation candidate.
5. **Report** — a clean cycle (no new drift) files a one-line "no drift since `<SHA>`" note and stops. Drift found → the inbox carries it to the next review.

No code changes, no baseline changes — detection only. The human runs improve-architecture on what the inbox surfaced, and *then* accepts a new baseline.

## Autonomy — detection earns auto-fix

- **Level 1 (default): detection-only.** Watch, diff, file to the inbox. Zero code writes. This is the safe, correct default — structural fixes are judgment calls.
- **Level 2+ (earned): trivial auto-fix.** Only the narrow, mechanical, reversible drift — a newly-introduced import cycle a single move breaks, an obvious duplicate — may be handed to a maker→verifier pair (loop-engineer's split) behind the full gate. Anything requiring a *design decision* stays in the inbox for a human. Raise the level only after cycles show the inbox routing is trustworthy.

## Optional: MemBerry

If a MemBerry-style memory MCP is available, `berry_store` the **accepted waivers** — a violation a review knowingly accepted with a reason (the same thing an ADR records) — so the loop can mute it instead of re-flagging, and `berry_load` them when filing. The committed baseline + ADRs stay authoritative; memory is a convenience index. Skip if absent.

## Build, then offer the schedule

Scaffold via [loop-engineer](../loop-engineer/SKILL.md) at Level 1, write `.fugazirc.json` zones with the user, capture the **baseline** on the current commit, and dry-run one cycle (it should find zero drift against its own fresh baseline). Then **offer** a schedule — a cron cold-start or `/loop` — since even a read-only loop consumes runs. The deliverable is a watch that's armed, not auto-armed.

## Common Mistakes

- **Re-reporting the whole backlog.** Without a baseline, every cycle screams about pre-existing violations and gets muted. Drift is the delta.
- **Auto-fixing structural judgment.** Breaking a cycle can mean a real design decision. Detection routes to a human; it doesn't refactor on its own.
- **Letting the baseline drift silently.** If the baseline advances without a human accepting the new state, accumulating drift becomes the new "normal" and the watch is blind. Advance it only on acceptance.
- **No zones configured.** `boundary-violations` is meaningless without `.fugazirc.json` zones declaring the intended architecture. Configure them first.

---

*The detection half of [improve-architecture](../improve-architecture/SKILL.md) — that skill owns the judgment (what to deepen, how), this loop owns the watch (what changed, when). Runs on [loop-engineer](../loop-engineer/SKILL.md) conventions; routes duplication to [dead-code-reaper](../dead-code-reaper/SKILL.md).*
