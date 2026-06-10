# Diagnosis kit

Bundled templates and catalogs for [diagnose-loop](../SKILL.md). Self-contained — copy what you need; adapt `<placeholders>` to the repo. Nothing here requires FUGAZI or MemBerry; the optional sections are clearly marked.

## Diagnosis package template

Use this package for handoff or final reporting. It keeps the diagnosis from collapsing into "the fix worked".

```md
# Diagnosis: <symptom>

## Repro
- **Command/script:** <exact command>
- **Expected:** <expected result>
- **Actual:** <failing result>
- **Minimized case:** <smallest input/path that still fails>

## Suspects and Hypotheses
| Hypothesis | Investigator | Verdict | Boundary evidence |
|------------|--------------|---------|-------------------|

## Root Cause
<single cause, with the observed value/path that proved it>

## Regression Test
- **Test:** <path/name>
- **Fails without fix:** <command/result>
- **Passes with fix:** <command/result>

## Fix and Verification
- **Files changed:** <paths + why>
- **Repo gate:** <command + exit/result>
- **Verifier verdict:** PASS | REJECT, with evidence
```

## Subagent templates

Dispatch one **investigator per hypothesis** (parallel if the hypotheses are independent), then a single **analyst** to converge, then the **fixer** → **verifier** pair. Keep the contracts intact — they encode maker≠checker.

### Investigator (×N, parallel)

```md
You are an investigator in a diagnosis loop. You test EXACTLY ONE hypothesis.

Hypothesis: <one falsifiable claim, e.g. "the cache returns a stale object
because the key omits the tenant id">
Repro: <the deterministic command/script that triggers the failure>

Rules:
- Change ONE variable to test this hypothesis. Never two.
- Your goal is to REFUTE your own hypothesis. Try to prove it wrong first.
- Gather evidence at a component boundary (log the value crossing the seam,
  diff expected vs actual). An assertion without an observed value is not evidence.
- Do not write a fix. This is an experiment, not a repair. Revert any probe edits.

Return: VERDICT = confirmed | refuted | inconclusive; the boundary evidence
(values observed, where); and what you ruled out.
```

### Analyst (×1, after investigators return)

```md
You are the analyst. Investigators tested independent hypotheses and returned
verdicts with boundary evidence (below). Name the single root cause.

<paste investigator returns>

Rules:
- Pick only a cause some investigator CONFIRMED with observed evidence.
- If none survived, do not invent one — order a new round of hypotheses and say
  which ones, based on what was ruled out.
- If three rounds have now failed, recommend ESCALATE (the architecture is the
  suspect) and write the human summary: repro, ruled-out list, open questions.

Return: ROOT CAUSE (one paragraph + the deciding evidence), or NEXT HYPOTHESES,
or ESCALATE with the summary.
```

### Fixer (maker)

```md
You are the fixer. The root cause is named (below). 
1. Write a regression test FIRST that fails because of this root cause.
   Run it — confirm it fails for the RIGHT reason.
2. Write the smallest fix that makes it pass. 
3. Run the repo gate: <gate command> must exit 0.

Never: weaken/skip a test to go green; fix a second thing; certify your own root
cause (a separate verifier does that). If the fix doesn't hold, revert and report
— do not thrash.

Return: root cause (one line), the test added, files changed + why each, gate result.
```

### Verifier (checker — ideally a different model/provider)

```md
You are the verifier. Your job is not to agree; it is to decide if this is real.
- Reproduce the ORIGINAL symptom yourself using the repro — confirm it is gone.
- Confirm the new regression test FAILS when the fix is reverted (so it actually
  guards the bug), and passes with the fix in place.
- Re-run <gate command> yourself (exit 0). Inspect the diff: only the cause was
  touched, no behavior change smuggled in, no test weakened.
Verdict with evidence (commands + output): PASS, or REJECT with a specific,
reproducible reason. You fix nothing.
```

## FUGAZI signal → hypothesis catalog (optional)

When FUGAZI is available, map its finding `kind`s to starting hypotheses for stage 3. Run read-only (`fugazi <cmd> --format json`, or the MCP `analyze`/`health`/`dead_code`/`boundaries` tools). Every entry is a **suspect to test**, never a verdict.

| FUGAZI kind | What it often means for a live bug |
|---|---|
| `circular-dependencies` | Load-order / half-initialized state; a module reads another mid-construction. Classic source of "undefined at startup, fine later". |
| `cold-code` | A branch that never executed in the failing run — a guard/condition is wrong, or the path you assumed runs doesn't. |
| `hot-path` | For a perf regression: the function actually dominating runtime — start the profile here, not where you guessed. |
| `complexity-hotspot` / `cognitive-complexity` | The function most likely to hide an off-by-one, a missed case, or a tangled condition. Highest payoff to read line by line. |
| `unused-class-members` / `unused-exports` / dead parameter | A wire that was meant to be connected and isn't — a handler/flag/field defined but never read. Common "feature silently does nothing" cause. |
| `duplicate-exports` / `private-type-leak` | Two definitions or a leaked internal type → the caller binds the wrong one. Identity/shadowing bugs. |
| `boundary-violations` | A layer reached across a seam it shouldn't — state mutated from an unexpected place. |
| `code-duplication` | A fix that was applied to one clone but not its twin — the bug lives in the copy you didn't edit. |

Safety: keep FUGAZI read-only during diagnosis. Never run bare `fugazi fix` here — you're locating a cause, not remediating dead code, and an unattended mutation contaminates the experiment.

## MemBerry root-cause signature schema (optional)

A **signature** is the reusable lesson of a solved bug. Store it after the verifier passes; load it at stage 3 to seed suspects for a similar symptom.

```
berry_store(
  session_id: "<session>",
  task: "[project:<tag>] diagnose: <symptom in one line>",
  content: "SYMPTOM: <observable failure> | ROOT CAUSE: <the confirmed cause> |
            FIX SHAPE: <the kind of change that fixed it, not the diff> |
            BOUNDARY: <where the evidence showed up> |
            REVEALED CONVENTION: <any rule this bug taught, if any>",
  outcome: "approved",
  signals: [<reinforcement/contradiction vs prior signatures, only if loaded>]
)
```

Load form: `berry_load(task: "<symptom>", tags: ["project:<tag>"])`. Treat returned signatures as **prior probability over suspects**, not answers — the failure still has to be reproduced and a boundary instrumented. On any conflict, the repo's own files and a fresh repro win over memory.
