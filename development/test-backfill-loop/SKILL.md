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

**"Suspicious" counts as "suspected bug" — not a free pass to pin it.** If two code paths disagree on a documented input (e.g. one parser returns `({}, None)` and a fallback returns `(None, "...")` for the same empty block), or the result you observe depends on which optional dependency happens to be installed on *your* machine, you have a contradiction you cannot resolve from the code alone. That is a `blocked-suspected-bug` to file with both observed behaviours — **not** a behaviour to lock in. Two illusions to reject:
- *"Green is green / correct by definition."* A passing test only proves the code does what it does; it never proves that is what it *should* do. Whichever branch you pin, you may be cementing the wrong one.
- *"Pin it now with a `# TODO: confirm which is right` and move on."* A TODO comment is not a filed defect — it rots silently and the regression you "caught" is a green check protecting a bug. File it in the tracker; resolving which parser is correct is part of *this* task's escalation, not a deferred product question.

## The three roles (maker ≠ checker)

| Role | Job | Never |
|---|---|---|
| **Scout** (producer) | Find the highest-value uncovered code (most-used, riskiest, about-to-be-refactored); file one target per cycle with the coverage gap and why it matters | Write tests; chase 100% for its own sake |
| **Test-writer** (maker) | Write characterization tests for ONE target that pin current behaviour; run them green; raise coverage on that module | Assert behaviour it believes is wrong (file it instead); test implementation details that lock in nothing |
| **Verifier** (checker, different model) | Confirm each new test **bites** (it fails when the behaviour it covers is perturbed), re-run the suite, confirm the coverage ratchet advanced; promote or reopen | Accept a test that passes against a broken stub; approve on the coverage number alone |

The verifier's distinctive check is the **bite test** (see below) — coverage % is necessary but not sufficient.

## The ledger & ratchet

State lives in `agent-state/COVERAGE_TARGETS.md` (the backlog of modules to cover) plus the loop-engineer spine. The ratchet metric is **coverage %** (line or branch, per the repo's tool) — up-only — guarded by the bite test so the number means something.

**The gate is fixed; you move the code to it, never the gate to the code.** Do not lower the configured threshold ("75% for now"), and do not add `# pragma: no cover` / `# noqa`-style exclusions to make a stubborn branch disappear from the denominator — both manufacture a green number without manufacturing safety, and the verifier treats either as a failed cycle. If a branch genuinely cannot be exercised through the public surface (e.g. an `ImportError` fallback that never fires when the dependency is installed), that is a *coverage-environment* problem: either trigger it honestly (force the import failure via a fixture/monkeypatch) or record it as `blocked` with the reason — never suppress it to hit the integer.

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
- **Weak assertions don't bite.** `assert result is not None`, `assert result`, `assert result[0] is None or result[1] is None` — anything that passes for a whole family of wrong return values executes the line without pinning behaviour. The verifier mutates a *correct-looking-but-wrong* return; if the test still passes, it's reopened. Each error branch must assert the *specific* value/message it produces, not merely that the function returned.
- **No whole-tuple snapshot blobs.** `assert f(x) == (<entire dict it produces today>, None)` maximizes covered lines per test but cements every incidental detail (including any bug) and goes red on harmless changes — brittle and non-diagnostic. Assert the *named facts that matter* (this key has this value; the error is this message), one behaviour per assertion.

Coverage that rises without biting tests is the exact false comfort this loop is built to prevent. **Coverage % is a gate, never the goal** — the goal is a net that catches regressions. Hitting 80% with non-biting tests is a failed cycle, not a done one.

## Known pressure rationalizations

A late-Friday "just hit 80% before the gate flips" deadline produces these dodges. Each one trades a real net for a green number; the required response is non-negotiable.

| Rationalization (the dodge) | Required response |
|---|---|
| "Coverage is the metric the lead named, so my job is the number." | The number is a **gate, not the goal**. The job is a net that catches regressions; 80% of non-biting tests is a failed cycle. Every test must pass the bite gate before it counts. |
| "Assert it `is not None` / returns something — executes the line, I'm off the hook for exact strings." | Weak assertions don't bite. Assert the **specific** value/message each branch produces. A test that passes for a family of wrong returns is reopened. |
| "Snapshot the whole return tuple as one blob — max lines per test, future change tells me by going red." | No whole-output snapshot blobs. Assert the **named facts that matter**, one behaviour per assertion. Blobs cement incidental detail (and bugs) and go red on harmless changes. |
| "Pin what it returns on *my* machine right now (PyYAML installed); the fallback parser is a different code path, not my problem." | Behaviour that depends on which optional dep is installed, or where two code paths disagree on a documented input, is a **`blocked-suspected-bug`** — file both observed behaviours; don't pin one. "Green is green" never proves *should*. |
| "Test the underscore-prefixed privates directly — surgical, most efficient path to those lines." | Cover privates **through the public entry point**. Poking internals farms coverage while pinning implementation shape; the net dies at the next refactor. |
| "It's untended, so the loop is the verifier — pytest exit 0 plus the coverage number IS verification." | The **separate verifier role is never skipped**, untended or not. Green + coverage % is exactly the false comfort the bite test exists to catch. Maker ≠ checker holds with zero humans watching. |
| "Can't trigger the ImportError fallback with PyYAML installed — add `# pragma: no cover` or drop the gate to 75% for now." | Never suppress a branch or lower the threshold. Trigger the path honestly (force the import failure via fixture/monkeypatch) or mark it `blocked` with the reason. Move the code to the gate, never the gate to the code. |
| "Pin today's behaviour with `# TODO: confirm which parser is right` — at least the regression is caught." | A TODO is not a filed defect — it rots and the "regression" you caught is a green check guarding a bug. **File it in the tracker** and resolve it as part of this task's escalation. |

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
- **Testing implementation details.** Tests bound to internals break on every refactor and protect nothing — they're anti-safety-net. This includes reaching past the public surface to call underscore-prefixed privates (`_parse_minimal_frontmatter`, `_minimal_yaml_scalar`) just to light up their lines: it farms coverage while pinning the *shape* of the implementation, not its *behaviour*, so the net evaporates the moment anyone refactors. Cover privates through the public entry point that exercises them; if a private can't be reached publicly, that's a seam to file, not internals to poke.
- **Letting the writer self-verify.** Same brain that wrote a too-loose test will accept it. The verifier perturbs and re-checks independently.

---

*Uses red-green discipline applied to existing code as characterization tests and runs on [loop-engineer](../loop-engineer/SKILL.md) conventions, in the same shape as [bug-pipeline](../bug-pipeline/SKILL.md). No external TDD skill is required. Pairs naturally before [improve-architecture](../improve-architecture/SKILL.md): backfill the net, then deepen the module under it.*
