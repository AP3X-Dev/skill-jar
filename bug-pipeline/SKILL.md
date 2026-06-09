---
name: bug-pipeline
description: "Autonomous three-agent bug repair pipeline for any codebase: a Hunter sweeps and files evidence-backed defects to a shared BUG_TRACKER.md, a Fixer repairs one bug per cycle, and an independent Validator (ideally a different model) verifies or reopens. Use when the user wants an automated bug-fixing loop, continuous find→fix→verify cycles, or mentions 'bug pipeline', 'hunter fixer validator', or 'auto-repair loop'. NOT for a single known bug (just fix it) or a metrics-driven hardening pass (use building-optimization-loops). Composes with loop-engineer, which scaffolds the loop infrastructure this pipeline runs on."
---

# Bug Pipeline (Hunter → Fixer → Validator)

A three-agent repair loop over a shared markdown tracker. The **Hunter** (producer) discovers defects and files them with evidence; the **Fixer** (consumer) repairs exactly one per cycle; the **Validator** (quality gate) independently verifies or reopens. Maker≠checker is enforced by construction: the fixer never validates its own fix, and the validator runs on a different model/provider where possible — same model, same brain, same blind spots.

**Output:** a running pipeline in the target repo — the tracker, three role agents, and a per-cycle driver — plus a verified first cycle. This is a *specialized loop*: use [loop-engineer](../loop-engineer/SKILL.md) to scaffold the state spine, safety rules, and triggers it runs on; this skill defines the pipeline's contract.

## When to Use

- A codebase needs continuous, unattended find→fix→verify cycles, not a one-off fix.
- A defect backlog should accumulate in one reviewable place with statuses and evidence.
- Multiple agents (possibly on different schedules) need to hand work to each other without sharing a session.

## When NOT to Use

- One specific known bug — just fix it (use **bugfix** / your debugger).
- A quality/hardening pass with measured dimensions and a ratchet — use **building-optimization-loops**.
- The repo has no runnable verification (tests, lint, a gate script). Build the gate first — a pipeline that can't verify fixes just churns the tracker.

## The three roles

| Role | Job | Writes | Never |
|---|---|---|---|
| **Hunter** (producer) | One bounded sweep per cycle over a rotating focus area; files at most ~3 high-confidence defects with `file:line` evidence and a symptom/repro | The tracker only | Modifies code; files style nits or hypotheses |
| **Fixer** (consumer) | Repairs exactly ONE `pending` bug with the smallest diff; runs the repo gate; marks it `fixed` with root-cause notes | Code + the tracker | Marks its own work `verified`; weakens the gate or tests |
| **Validator** (quality gate) | Independently reproduces the symptom is gone, re-runs the gate, inspects the diff for scope creep; promotes to `verified` or `reopens` with notes | The tracker + failed-attempts log | Fixes anything itself; approves without evidence |

Run the validator on a **different model or provider** than the fixer where the host allows it — cross-brain checking catches what self-review can't.

## The tracker — `BUG_TRACKER.md`

The pipeline's shared state. Default location: `agent-state/BUG_TRACKER.md` (repo root works too — pin one path in the driver). Append-only in spirit: statuses change, entries are never deleted.

```md
# BUG_TRACKER.md

## Meta
| Field | Value |
|---|---|
| Last Hunter Scan | <timestamp> |
| Last Fixer Pass | <timestamp> |
| Last Validator Pass | <timestamp> |
| Total Found / Pending / Fixed / Verified / Reopened | 0 / 0 / 0 / 0 / 0 |

## Bugs

### BUG-1 — <one-line title>
- **Severity:** high | medium | low
- **Evidence:** <file:line>
- **Symptom / repro:** <observable failure or one-line repro>
- **Status:** pending → fixed → verified  (or: reopened | blocked)
- **Fixer notes:** <root cause + what changed>          <!-- set by Fixer -->
- **Validator notes:** <commands run + verdict basis>   <!-- set by Validator -->

## Sweep Notes
<one entry per hunter sweep: focus area, probes run, findings count — a sweep
that files nothing is a valid success and still gets a note>
```

**Status flow:** `pending` (Hunter) → `fixed` (Fixer) → `verified` (Validator) — or `reopened` (Validator, with rejection notes; logged to failed-attempts so no cycle retries it blind) — or `blocked` (needs a human decision).

## Setting it up in a repo

1. **Scaffold the loop infra** with [loop-engineer](../loop-engineer/SKILL.md) (`scaffold-loop.py` lays down `agent-state/`, `AGENTS.md`, a driver stub) — or go minimal: just the tracker and the three agents.
2. **Pin the gate**: the exact command(s) that exit 0/1 in THIS repo (tests, lint, an audit script). The Fixer and Validator both run it every cycle.
3. **Drop the three agents** (templates below) into the host's agent dir (`.claude/agents/` for Claude Code; adapt to `.codex/agents/*.toml` via loop-engineer's subagent-templates for Codex).
4. **Dry-run one cycle** end-to-end before scheduling anything. Do not hand off a pipeline that has never closed a cycle.

## Agent templates

Adapt `<placeholders>` to the repo. Keep the contracts intact — they are the pipeline's safety floor.

```md
---
name: hunter
description: "Producer for the bug pipeline. Runs one bounded discovery sweep and files high-confidence defects to BUG_TRACKER.md. Use during the pipeline's discovery stage. Read-only on all content except the tracker."
model: sonnet
---
You are the hunter — the producer in this repo's Hunter → Fixer → Validator pipeline.
- ONE bounded sweep per dispatch over the focus area you were given (rotate focus across cycles).
- File at most 3 findings to <tracker path>, each: BUG-<n>, title, severity, file:line evidence, symptom or one-line repro, status `pending`.
- Real defects only — a concrete failure mode you can articulate. No style nits, no hypotheses, no speculative hardening. Verify each candidate (run the code path or trace it) before filing.
- No duplicates: check the tracker (all statuses) and the failed-attempts log first; dedupe by file:line.
- Deliberate choices are not bugs — templates, suppressions, and documented conventions are design.
- Read-only except the tracker. A sweep that files nothing is a valid success.
Return: findings count, one line per finding, recommended next focus area.
```

```md
---
name: fixer
description: "Maker for the bug pipeline. Fixes exactly one pending BUG_TRACKER.md bug with the smallest diff that passes the repo gate. Use during the pipeline's execution stage. Never validates its own fix."
model: sonnet
---
You are the fixer — the maker in this repo's bug pipeline.
- Fix exactly ONE assigned `pending` bug: read every file it names, then the smallest diff that removes the symptom.
- Run the gate after the fix: <gate command> must exit 0. A fix that breaks the gate is not a fix.
- Mark the bug `fixed` with root-cause notes. You never mark anything `verified` (maker≠checker).
- Never weaken the gate or a test to pass. A wrong check is a human-decision item, not a silent edit.
- If your approach fails: revert, log it to the failed-attempts log, stop — do not thrash.
Return: bug fixed, root cause (one line), files changed + why each, gate result, tracker updates.
```

```md
---
name: validator
description: "Checker for the bug pipeline. Independently verifies a fixed bug — reproduces the symptom is gone, re-runs the gate, inspects the diff — and promotes to verified or reopens with evidence. Use during the pipeline's verification stage. Run on a different model than the fixer."
model: opus
---
You are the validator — the checker. Your job is not to be agreeable; it is to decide whether the fix is actually correct.
- Independently verify ONE `fixed` bug: re-run its repro yourself, re-run <gate command> (must exit 0), inspect the diff (only named files changed, no weakened checks, root cause addressed — not the symptom).
- Verdict with evidence (commands + output): promote to `verified`, or `reopen` with specific, reproducible rejection notes.
- You fix nothing — repairing it yourself collapses maker≠checker. On reopen, also log the failed approach to the failed-attempts log.
Return: verdict (pass|reject), evidence, issues, required fixes if rejected, tracker updates.
```

## The cycle (driver outline)

One bug per cycle. Full driver-prompt patterns live in loop-engineer's automation-templates; the pipeline's shape:

1. **Preflight** — `git status` clean-or-recover; read the tracker and loop state.
2. **Discovery** — skip if `pending` bugs remain (work the backlog first); else dispatch the Hunter for one bounded sweep.
3. **Planning** — pick the single highest-severity `pending` bug; check the failed-attempts log before committing to an approach.
4. **Execution** — the Fixer repairs it.
5. **Verification** — the Validator promotes or reopens.
6. **State update** — tracker reflects the final status; commit code and tracker/state **together** in one commit (`bug-pipeline(N): <title>`), so a restart never sees fixed-but-unrecorded work.

**Stop conditions:** one bug per cycle; a sweep that files nothing is a successful cycle; escalate to a `blocked` status + human-decision list when a fix would change a public contract, span multiple cycles, or the "bug" might be deliberate design.

**Autonomy:** start at Level 2 (loop-engineer's ladder) — the pipeline commits locally; a human reviews diffs and pushes. Earn higher levels with cycles where the Validator's verdicts match the human's review.

## Common Mistakes

- **Letting the fixer self-verify.** The whole point of the third agent is that plausible-but-wrong fixes die at the gate instead of shipping.
- **Hunting without an evidence bar.** A tracker full of "could be cleaner" drowns the real defects. Every entry needs `file:line` + an observable symptom.
- **Fixing more than one bug per cycle.** Batched fixes make the validator's job ambiguous and rollbacks expensive.
- **No gate.** If `fixed` only means "the fixer says so," the pipeline is a rumor mill. Pin a command that exits 0/1.
- **Deleting reopened bugs.** A reopen is data — it feeds the failed-attempts log that stops future cycles from repeating the loss.

---

*Worked example: the skill-jar repo runs an instance of this pipeline on itself — agents in `.claude/agents/`, driver in `docs/prompts/bug-pipeline-driver.md`, tracker in `agent-state/BUG_TRACKER.md`.*
