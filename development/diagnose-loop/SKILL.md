---
name: diagnose-loop
description: "Bounded diagnosis loop for ONE hard bug or performance regression: reproduce → seed suspects → fan out parallel hypotheses (each made to refute itself) → converge on the root cause → lock a regression test → fix → independently verify. Uses systematic-debugging discipline with parallel hypothesis testing, optional FUGAZI suspect seeding, optional MemBerry root-cause memory, and maker≠checker (the fixer never certifies its own root cause); Superpowers skills are optional accelerators, not prerequisites. Use when diagnosing a single stubborn bug, a flaky failure, or a perf regression whose cause is unknown and where earlier fixes bounced. NOT for a known one-line fix (just fix it), a continuous find→fix→verify backlog (use bug-pipeline), or a metric-driven hardening pass (use optimization-loop)."
tags:
  - meta
  - diagnosis
  - bounded-loop
core: true
maturity: linted
---

# Diagnose Loop

A **bounded convergence loop** for one hard defect. It does not run forever — it runs until the root cause is pinned and a regression test locks it, or until the evidence says *escalate to a human*. It takes the discipline of systematic-debugging (no fix without a root cause first) and adds three things that discipline alone can't give you: **parallel hypotheses** instead of one guess at a time, **seeded suspects** from static analysis and past bugs instead of a cold start, and a **separate verifier** so a plausible-but-wrong fix dies at the gate instead of shipping.

**Output:** a confirmed root cause with boundary evidence, a regression test that fails without the fix and passes with it, the minimal fix, and (optionally) a stored root-cause signature so the next similar bug starts ahead.

## Operating Contract

Produce a diagnosis package, not a hunch: deterministic repro command, minimized failing case, suspect list, hypothesis table with confirmed/refuted evidence, named root cause, regression-test proof, minimal fix, repo gate result, and verifier verdict. Each stage fails closed when it lacks observed boundary values or a runnable command. A green symptom without root-cause evidence is not done.

## When to Use

- One stubborn bug whose cause is genuinely unknown — you can see the symptom but not why.
- A fix bounced: you tried something, it didn't hold, and you're about to guess again.
- A performance regression — a number got worse and you need the cause, not a band-aid.
- A flaky failure that needs a deterministic repro before anyone can fix it.

## When NOT to Use

- The cause is obvious and the fix is one line — just fix it (and add the test).
- A backlog of many defects to grind through continuously — use **bug-pipeline**.
- A measured quality/hardening pass with a metric ratchet — use **optimization-loop**.
- No way to trigger the failure at all — get a repro first; you cannot diagnose what you cannot reproduce.

## The loop

One root cause per run. Each stage has a falsifiable exit — no vibes.

| # | Stage | Exit condition (gate) |
|---|---|---|
| 1 | **Reproduce** | A deterministic command/script that triggers the failure on demand. No repro → STOP and report; do not proceed on a hunch. |
| 2 | **Minimize** | The smallest input/path that still fails. Strip away everything that doesn't change the symptom. |
| 3 | **Seed suspects** | A ranked suspect list — from *(optional)* FUGAZI signals on the failing module and *(optional)* MemBerry signatures of similar past bugs, plus a manual backward trace from the failure point. |
| 4 | **Hypothesize in parallel** | N independent investigators, **one variable each**, each told to *refute its own hypothesis*. Each returns confirmed / refuted **with evidence at a component boundary**. |
| 5 | **Converge** | A separate analyst weighs the returns and names the single surviving root cause. None survive → new hypotheses (back to 3). ≥3 fix rounds failed → **escalate** (question the architecture, hand to a human). |
| 6 | **Lock & fix** | Write the failing **regression test first**, then the smallest fix. Both green. A separate **verifier** confirms the symptom is gone, the test fails without the fix, and the repo gate passes. |

**Iron law (inherited):** no fix is written before stage 6, and no fix is written without a named root cause from stage 5. A fix applied during investigation is a contaminated experiment — revert it before continuing.

## Roles (maker ≠ checker)

| Role | Job | Never |
|---|---|---|
| **Investigator** (×N, parallel) | Test ONE hypothesis by changing ONE variable; gather evidence at a boundary; actively try to *refute* it | Test two things at once; declare a cause it didn't instrument |
| **Analyst** | Weigh investigator returns, name the surviving root cause, or order another round | Pick a cause no investigator confirmed with evidence |
| **Fixer** (maker) | Write the regression test, then the smallest fix; run the gate | Certify its own root cause; weaken a test to go green |
| **Verifier** (checker, ideally a different model) | Reproduce-gone, confirm test-fails-without-fix, re-run the gate, inspect diff scope | Fix anything itself; approve on assertion instead of a command's output |

Run the **Investigators in parallel** when the hypotheses are independent (different files/subsystems, no shared state) — one agent per hypothesis. If they're entangled (each depends on the last's result), run them sequentially. Full subagent prompt templates: [references/diagnosis-kit.md](references/diagnosis-kit.md).

## Optional: FUGAZI suspect seeding

If [FUGAZI](https://github.com/AP3X-Dev/FUGAZI) (codebase-intelligence static analyzer — CLI `fugazi` or the `fugazi-mcp` MCP server) is available, stage 3 starts from deterministic signals instead of a blank page. Skip entirely if it isn't; the manual backward trace still works.

- Run read-only on the failing area: `fugazi health --format json` and `fugazi circular-deps --format json` (or MCP `health` / `analyze`).
- Translate signals into hypotheses — e.g. `circular-dependencies` → load-order / half-initialized-state bug; `cold-code` → a branch that *should* run but doesn't (guard wrong); `complexity-hotspot` / `cognitive-complexity` → the function most likely hiding the logic error; a dead parameter or unread field near the failure → a wire that was never connected.
- These are **suspects, not verdicts** — every one still has to survive an investigator. FUGAZI narrows where to look; it does not name the cause.
- The full signal→hypothesis catalog is in [references/diagnosis-kit.md](references/diagnosis-kit.md).

## Optional: MemBerry root-cause memory

If a MemBerry-style memory MCP is available, the loop remembers what past bugs taught it. Skip if absent — nothing else depends on it.

- **At stage 3:** `berry_load(task: "<symptom in one line>", tags: ["project:<tag>"])` — pull root-cause signatures of bugs with a similar symptom, so the suspect list starts from history.
- **After stage 6 verifies:** `berry_store(...)` the **signature** — symptom → confirmed root cause → fix shape — and any convention the bug revealed. Store the *lesson*, not the diff.
- A bounced earlier fix is data: if MemBerry (or the repo's failed-attempts log) already holds a rejected approach for this symptom, do not retry it blind — pick a different angle or escalate.

## Termination & escalation

- **Solved:** root cause named with boundary evidence, regression test green, verifier passed. Done — record the signature and stop.
- **Escalate** when: 3 fix rounds have failed (the architecture is the suspect now, not the line), the fix would change a public contract, or the cause crosses a boundary the loop isn't allowed to touch. Hand the human a tight summary: repro, what was ruled out (with evidence), and the surviving open questions.

## Generated agents

Copy-ready generated agents live in [../agents/README.md](../agents/README.md) and are sourced from [../agents/manifest.json](../agents/manifest.json). Install only the roles needed for the active diagnosis loop: `diagnose-investigator`, `diagnose-analyst`, `diagnose-fixer`, `diagnose-verifier`.

## Common Mistakes

- **Guessing in series.** One hypothesis at a time, fix-and-pray, is exactly what this loop replaces. Fan out; make each investigator try to *kill* its own idea.
- **Fixing before the root cause is named.** A fix that makes the symptom disappear without an explained cause is a coincidence waiting to regress.
- **No regression test.** If nothing fails *without* the fix, you haven't proven you fixed anything — and the bug will quietly return.
- **Letting the fixer grade itself.** Same brain, same blind spot. The verifier reproduces independently; "looks fixed" is not evidence.
- **Trusting FUGAZI/MemBerry as verdicts.** They seed suspects and recall history; they never replace reproducing the failure and instrumenting a boundary.

---

*Uses the same root-cause, regression-test-first, and parallel-hypothesis disciplines as the Superpowers debugging skills where they're installed, but stands alone through [references/diagnosis-kit.md](references/diagnosis-kit.md). Sibling jar skills are optional accelerators: [bug-pipeline](../bug-pipeline/SKILL.md) for the many-bugs case, [loop-engineer](../loop-engineer/SKILL.md) if you want to turn a recurring class of failure into a scheduled loop.*
