---
name: review-panel
description: "Adversarial multi-lens code review for a diff, branch, or PR: an optional FUGAZI pre-pass grounds the review in deterministic findings, then a panel of independent reviewers each works a distinct lens (correctness, security, simplicity/reuse) in parallel, findings are deduped and severity-ranked, and every finding is verified against the codebase before it is acted on — no performative agreement. Applies requesting/receiving-code-review discipline with bundled prompts, FUGAZI grounding, and optional MemBerry false-positive memory; Superpowers skills are optional accelerators, not prerequisites. Use when reviewing a branch/PR/diff and you want broad, adversarial, evidence-checked coverage rather than a single-reviewer pass — before a merge, or as a tougher gate on a risky change. NOT for a quick single-file glance (just review it) or a continuous defect pipeline (use bug-pipeline)."
tags:
  - meta
  - review
  - evaluator
core: true
maturity: linted
---

# Review Panel

A code review that does not trust one reviewer or one finding. It runs a **panel** of independent reviewers, each on a distinct lens, grounds them in deterministic static-analysis findings, then makes every finding **earn its place** by verifying it against the codebase before anyone acts on it. The two failure modes of AI code review — a single reviewer's blind spots, and confident-but-wrong findings implemented via performative agreement — are designed out.

**Output:** a deduped, severity-ranked findings list where each entry is marked *verified* (reproduced against the code) or *refuted*, plus the actions taken (Critical/Important fixed, Minor noted).

## Superpowers is optional

If `requesting-code-review`, `receiving-code-review`, or `dispatching-parallel-agents` are installed, they can provide familiar reviewer dispatch and review-receipt mechanics. If they are absent, use this skill directly: the bundled lens prompts in [references/reviewer-kit.md](references/reviewer-kit.md) define the reviewers, synthesizer, severity model, and verify-before-act protocol.

## Operating Contract

The review output is a verified review package, not a list of opinions. Pin `BASE_SHA` and `HEAD_SHA` before dispatch. Every finding must include `file:line`, trigger or abuse path, impact, severity, and origin lens. The synthesizer may dedupe and rank only findings the reviewers raised. The author must verify or refute each finding against the code before acting; fixes for Critical/Important findings name the command that proved the issue gone.

## When to Use

- A branch/PR/diff is about to merge and you want adversarial, broad coverage.
- A change is risky (security surface, public API, concurrency) and one reviewer isn't enough.
- You want findings that survived an evidence check, not a wall of plausible suggestions.

## When NOT to Use

- A quick single-file change — just review it directly.
- A continuous find→fix→verify backlog across the whole repo — use **bug-pipeline**.
- You only want the project's standard reviewer — use that reviewer or command directly.

## The panel (maker ≠ checker)

The author of the diff is never a reviewer of it. Each reviewer is a fresh, independent agent with one lens — redundant reviewers on the same lens just agree with each other.

| Role | Lens / job | Never |
|---|---|---|
| **Correctness reviewer** | Logic errors, edge cases, error handling, data flow, concurrency | Comment on style |
| **Security reviewer** | Auth, injection, secrets, unsafe deserialization, input validation at boundaries | Pass over a risk as "probably fine" |
| **Simplicity reviewer** | Reuse (is this already in the codebase?), dead abstraction, over-engineering, YAGNI | Demand gold-plating |
| **Synthesizer** | Dedupe across lenses, rank by severity, drop overlaps | Add findings no reviewer raised |
| **Author** (receives) | Verify each finding against reality, then act — fix or push back **with reasoning** | Reply "great catch!" and implement before verifying |

Run reviewers **in parallel** — independent lenses, no shared state. Lens templates and the per-finding verification protocol: [references/reviewer-kit.md](references/reviewer-kit.md).

## The process

1. **Pin the diff** — `BASE_SHA` and `HEAD_SHA` (or the PR number). Every reviewer reviews exactly this range.
2. **(Optional) FUGAZI pre-pass** — ground the panel before opinions form (see below).
3. **Dispatch the panel** — one reviewer per lens, in parallel, each handed the diff, the base SHAs, and its lens prompt. Each returns findings with `file:line`, severity, and a concrete rationale.
4. **Synthesize** — dedupe across lenses, rank by severity (Critical / Important / Minor), collapse the three lists into one.
5. **Verify before acting** — for each finding, the author *reproduces the claim against the codebase* (does the edge case actually reach this line? is the "duplicate" really equivalent?). A finding that can't be reproduced is refuted, with a one-line reason — not silently implemented. No performative agreement.
6. **Act** — fix Critical and Important; note Minor. Each fix is its own small change.
7. **(Optional) Record** — store confirmed false-positive patterns to MemBerry so repeat noise is auto-deprioritized next time.

## Severity model

Apply after verification:

- **Critical** — correctness/security defect that will bite in production. Fix before merge.
- **Important** — real problem, not a blocker. Fix now or file it.
- **Minor** — style/preference. Note it; don't gate the merge on it.

A finding's severity is only meaningful *after* it survives step 5. An unverified "Critical" is a hypothesis.

## Optional: FUGAZI pre-pass

If [FUGAZI](https://github.com/AP3X-Dev/FUGAZI) (CLI `fugazi` or the `fugazi-mcp` MCP server) is available, run it read-only on the changed files before the panel, so reviewers start from deterministic facts instead of re-deriving them: `fugazi dead-code --format json` (did the diff orphan something?), `fugazi dupes --format json` (did it reintroduce a clone?), `fugazi boundaries --format json` (did it cross a seam?), `fugazi circular-deps --format json` (did it add a cycle?), `fugazi health --format json` (which changed functions are now complexity hotspots). Hand the findings to the relevant lens as *starting points* — every one still goes through step 5. Skip if FUGAZI isn't installed.

## Optional: MemBerry false-positive memory

If a MemBerry-style memory MCP is available, `berry_load` at step 2 to recall findings this project has confirmed as false positives before (a "dead" registry that's actually reflection-loaded, a "duplicate" that's deliberately separate), and `berry_store` at step 7 when a finding is refuted with a durable reason. Memory de-noises future panels; it never silences a fresh finding — step 5 still runs. On conflict, the codebase wins.

## Generated agents

Copy-ready generated agents live in [../agents/README.md](../agents/README.md) and are sourced from [../agents/manifest.json](../agents/manifest.json). Install only the roles needed for the active review panel: `review-correctness`, `review-security`, `review-simplicity`, `review-synthesizer`.

## Common Mistakes

- **Performative agreement.** "You're absolutely right!" then implementing an unverified finding is how a confident-but-wrong review breaks working code. Verify against the codebase first; push back with reasoning when the finding is wrong.
- **Redundant reviewers.** Three agents on the same lens just nod at each other. Diversity of lens is the whole point.
- **Acting on the raw finding list.** Severity is a claim until reproduced. An unverified Critical can be a misread.
- **Letting the author review their own diff.** Same brain, same blind spot — the panel is separate by construction.
- **Treating FUGAZI/MemBerry as verdicts.** They seed and de-noise; the evidence check is non-negotiable.

---

*Borrows the Superpowers review disciplines when available, but stands alone through the bundled reviewer-kit prompts. For one bug found here that needs deep root-causing, hand it to [diagnose-loop](../diagnose-loop/SKILL.md); for an ongoing repo-wide defect sweep, [bug-pipeline](../bug-pipeline/SKILL.md).*
