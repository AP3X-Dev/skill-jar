---
name: test-backfill-loop
description: "A loop-engineer loop that raises test coverage on an existing codebase one module per cycle: discovery finds the highest-value uncovered code (optional FUGAZI cold-code plus coverage gaps), a maker writes characterization tests that pin current behaviour (TDD discipline), and a separate verifier confirms the tests actually bite — they fail when behaviour changes — and that coverage ratchets up, never down. Builds and dry-runs the loop, then offers launch. Use when an existing codebase is under-tested and you want coverage raised safely and continuously, especially before a refactor. NOT for greenfield TDD on new features (just write tests first), a single missing test (just add it), or general multi-dimension hardening (use optimization-loop)."
tags:
  - meta
  - test-generation
  - validation
core: true
maturity: linted
---

# Test Backfill Loop

A specialized [loop-engineer](../loop-engineer/SKILL.md) loop that builds a **safety net under untested code** — one module per cycle, each test proven to actually catch a regression before it counts. The hard part of backfilling isn't writing tests; it's writing tests that *bite*. A test that passes no matter what the code does adds a green check and zero safety. This loop's verifier exists to kill those.

**Output:** a running coverage loop in the target repo — a target ledger, three role agents, a per-cycle driver — plus one verified cycle, then a launch **offer**. Coverage rises on a ratchet; it never silently falls.

## When to Use

- An existing codebase is under-tested and you want a safety net before refactoring it.
- You want coverage raised *continuously and safely*, with each test proven meaningful.
- Legacy code whose behaviour you must lock down before changing it.

## When NOT to Use

- New feature work — write the tests first with red-green discipline; don't backfill.
- One obvious missing test — just add it.
- A broad quality pass across many dimensions (perf, wiring, dead code) — use **optimization-loop**; coverage is one of its metrics, not the whole job.

## Characterization tests — read this first

These tests pin **current** behaviour so a later refactor can't change it unnoticed. That means they can also pin a **bug** in place. The rule: when a test would have to assert obviously-wrong behaviour, that's not a test to write — it's a **defect to file**: the writer's `blocked-suspected-bug` entries go to the canonical sink `agent-state/BUG_TRACKER.md` (or hand it to [diagnose-loop](../diagnose-loop/SKILL.md)). Never encode a known bug as "expected" just to get the line green. The loop builds a net under *intended* behaviour; suspected wrong behaviour is escalated, not cemented.

## The three roles (maker ≠ checker)

| Role | Job | Never |
|---|---|---|
| **Scout** (producer) | Find the highest-value uncovered code (most-used, riskiest, about-to-be-refactored); file one target per cycle with the coverage gap and why it matters | Write tests; chase 100% for its own sake |
| **Test-writer** (maker) | Write characterization tests for ONE target that pin current behaviour; run them green; raise coverage on that module | Assert behaviour it believes is wrong (file it instead); test implementation details that lock in nothing |
| **Verifier** (checker, different model) | Confirm each new test **bites** (it fails when the behaviour it covers is perturbed), re-run the suite, confirm the coverage ratchet advanced; promote or reopen | Accept a test that passes against a broken stub; approve on the coverage number alone |

The verifier's distinctive check is the **bite test** (see below) — coverage % is necessary but not sufficient.

## The ledger & ratchet

State lives in `agent-state/COVERAGE_TARGETS.md` (the backlog of modules to cover) plus the loop-engineer spine. The ratchet metric is **coverage %** (line or branch, per the repo's tool) — up-only — guarded by the bite test so the number means something.

```md
# COVERAGE_TARGETS.md
## Meta
| Coverage baseline | <n>% | Current | <n>% | Tool | <command> |
## Targets
### CT-1 — <module/file>
- **Coverage now:** <n>%   **Why high-value:** <most-called | risky | pre-refactor>
- **Status:** pending → covered → verified  (or: reopened | blocked-suspected-bug)
- **Writer notes:** <tests added + coverage delta>
- **Verifier notes:** <bite-test evidence + ratchet check>
```

## The "tests must bite" gate

The non-negotiable quality bar. A new test only counts if it can **fail**:

- The verifier perturbs the covered behaviour (mutate a return, flip a branch, or run the test against a deliberately broken stub of the function) and confirms the new test goes **red**.
- A test that stays green under perturbation asserts nothing real — it's reopened, not merged, no matter what it did to the coverage number.

Coverage that rises without biting tests is the exact false comfort this loop is built to prevent.

## The cycle (driver outline)

One module per cycle, on the loop-engineer spine:

1. **Preflight** — clean tree; read the ledger; record the coverage baseline if unset.
2. **Discovery** — skip if `pending` targets remain; else the Scout picks the next high-value uncovered module.
3. **Planning** — pick one `pending` target; check failed-attempts.
4. **Execution** — the Test-writer adds characterization tests in a worktree; suspected bugs → `blocked-suspected-bug`, not encoded.
5. **Verification** — the Verifier runs the bite test on each new test, re-runs the suite, checks the coverage ratchet advanced; promotes or reopens.
6. **State update** — commit tests + ledger together (`backfill(CT-N): <module>`).

## Optional: FUGAZI-guided discovery

If [FUGAZI](https://github.com/AP3X-Dev/FUGAZI) is available, it sharpens *what to cover first*: `fugazi runtime_report` / `cold-code` distinguishes code that ran-but-was-untested (high value — real paths, no net) from never-run code (maybe dead — route to [dead-code-reaper](../dead-code-reaper/SKILL.md), don't test it), and `hot-path` points at the code that matters most. Pair with the coverage tool's gap report. Skip if FUGAZI isn't installed — the coverage tool alone drives discovery.

## Optional: MemBerry

If a MemBerry-style memory MCP is available, `berry_store` the gotchas backfilling surfaces (hard-to-test seams, hidden global state, a module that needed a refactor to be testable) and `berry_load` them before touching the same area again. The ledger stays authoritative for *what's covered*; memory holds *why a module fought back*.

## Build, then offer launch

Scaffold via [loop-engineer](../loop-engineer/SKILL.md), drop the three agents, pin the suite + coverage commands as the gate, and dry-run one cycle. Then **offer** the human a scheduled `/loop` or cron — backfilling spends compute, and the human owns the spend. Start at autonomy Level 2: commits locally, human reviews and pushes.

## Generated agents

Copy-ready generated agents live in [../agents/README.md](../agents/README.md) and are sourced from [../agents/manifest.json](../agents/manifest.json). Install only the roles needed for the active backfill loop: `test-backfill-scout`, `test-backfill-writer`, `test-backfill-verifier`.

## Common Mistakes

- **Tests that don't bite.** The #1 failure — coverage rises, safety doesn't. The bite test is the whole point.
- **Encoding bugs as expected.** A characterization test of wrong behaviour cements the bug. File it; don't assert it.
- **Chasing 100%.** Cover the high-value, high-risk code first; trivial getters can wait forever.
- **Testing implementation details.** Tests bound to internals break on every refactor and protect nothing — they're anti-safety-net.
- **Letting the writer self-verify.** Same brain that wrote a too-loose test will accept it. The verifier perturbs and re-checks independently.

---

*Uses red-green discipline applied to existing code as characterization tests and runs on [loop-engineer](../loop-engineer/SKILL.md) conventions, in the same shape as [bug-pipeline](../bug-pipeline/SKILL.md). No external TDD skill is required. Pairs naturally before [improve-architecture](../improve-architecture/SKILL.md): backfill the net, then deepen the module under it.*
