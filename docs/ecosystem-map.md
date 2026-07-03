# Skill Jar — Ecosystem Map

> Hand-authored routing + composition map for the jar's skills. It carries the
> one thing the generated indexes cannot: the **edges between skills** —
> routing, composition, verification, autonomy, and shared state.
>
> Companion surfaces (do not duplicate them here): [`skills.json`](../skills.json)
> is the generated per-skill index (name / description / path / tags / maturity);
> [core-skills.md](core-skills.md) is the generated list of the self-improvement
> substrate; [evidence-model.md](evidence-model.md) defines the metadata fields.
> This map is **not generated** — update §5 when a skill is added or renamed.

## How to read this

The jar is an agent operating system. Skills are executable capabilities;
[`skills.json`](../skills.json) is the routing index; category folders are
installable plugins; the agent packs ([development](../development/agents/manifest.json),
[systems-design](../systems-design/agents/manifest.json)) are reusable worker
roles; `agent-state/` is durable loop memory; [`scripts/audit-jar.py`](../scripts/audit-jar.py)
is the quality gate; [AGENTS.md](../AGENTS.md) is the safety constitution.

A fresh agent should: (1) pick the skill from §1, (2) check the pipeline it
belongs to in §2, (3) confirm the autonomy/human-gate posture in §3, (4) treat
every dependency in §4 as optional unless marked bundled, and (5) use the
canonical roles and state files in §5–§6 instead of inventing new ones.

## 1. Routing — which skill for which intent

Pick by the **shape of the request**, not by keyword. Each row also names what
NOT to use, so overlapping skills stay disambiguated.

| The user wants to… | Use | Not |
|---|---|---|
| Fix one known bug | the host's `bugfix` / your debugger (external) | a loop skill |
| Root-cause ONE hard bug of unknown cause | [diagnose-loop](../development/diagnose-loop/SKILL.md) | bug-pipeline (that's a backlog) |
| Continuously find→fix→verify many defects | [bug-pipeline](../development/bug-pipeline/SKILL.md) | diagnose-loop (single bug) |
| Harden an existing codebase on measured metrics | [optimization-loop](../development/optimization-loop/SKILL.md) | auto-research, improve-architecture |
| Optimize ONE scalar metric on a frozen harness | [auto-research](../development/auto-research/SKILL.md) | optimization-loop (multi-metric) |
| Deepen shallow modules (human picks direction) | [improve-architecture](../development/improve-architecture/SKILL.md) | optimization-loop (automated) |
| Get continuous early warning on architecture drift | [arch-drift-watch](../development/arch-drift-watch/SKILL.md) | improve-architecture (it decides) |
| Safely remove confirmed-dead code | [dead-code-reaper](../development/dead-code-reaper/SKILL.md) | improve-architecture (live code) |
| Raise test coverage one module per cycle | [test-backfill-loop](../development/test-backfill-loop/SKILL.md) | unit-test-quality (judging tests) |
| Judge / repair / reject existing or slop tests | [unit-test-quality](../development/unit-test-quality/SKILL.md) | test-backfill-loop (a loop) |
| Build a NEW custom loop (job ≠ the named loops) | [loop-engineer](../development/loop-engineer/SKILL.md) | the specialized loops |
| Explore a feature/component design (design-it-twice) | [design-panel](../development/design-panel/SKILL.md) | design-system (whole system) |
| Adversarial multi-lens review of a diff/branch/PR | [review-panel](../development/review-panel/SKILL.md) | bug-pipeline (continuous) |
| Add observability/telemetry to an app | [instrument-observability](../development/instrument-observability/SKILL.md) | diagnose-loop (it debugs) |
| Reconcile fragmented/stale planning docs | [plan-prune](../development/plan-prune/SKILL.md) | sprint-ticket-runner (it executes) |
| Run a long multi-ticket sprint from a board | [sprint-ticket-runner](../development/sprint-ticket-runner/SKILL.md) | autonomous-advisor (single PRP pass) |
| Hands-off execute a complete PRP | [autonomous-advisor](../development/autonomous-advisor/SKILL.md) | sprint-ticket-runner, clean-room |
| Reimplement / port / clone an existing codebase | [clean-room](../development/clean-room/SKILL.md) | autonomous-advisor (no analysis pass) |
| Harden a skill against agent rationalizations | [skill-forge](../development/skill-forge/SKILL.md) | loop-engineer (code loop) |
| Add/import one skill into this jar | [add-to-jar](../development/add-to-jar/SKILL.md) | skill-forge (authoring) |
| Design a whole system / size a topology | [design-system](../systems-design/design-system/SKILL.md) | design-panel (one feature) |
| Pin an API contract (retries/versioning/errors) | [api-design](../systems-design/api-design/SKILL.md) | design-system, data-store-selection |
| Choose the data layer from access patterns | [data-store-selection](../systems-design/data-store-selection/SKILL.md) | design-system, api-design |
| Gate a service for launch (SLOs/runbooks/drills) | [production-readiness](../systems-design/production-readiness/SKILL.md) | design-system (it designs) |

The four well-modelled overlap clusters (copy this discipline when adding
skills): **defect triad** diagnose-loop ↔ bug-pipeline ↔ optimization-loop;
**improvement triad** optimization-loop ↔ auto-research ↔ improve-architecture;
**test pair** test-backfill-loop ↔ unit-test-quality; **detector→actor**
arch-drift-watch → improve-architecture / dead-code-reaper. Each names the
others in its "NOT for" boundary.

## 2. Composition — the two backbones

**Loop backbone.** [loop-engineer](../development/loop-engineer/SKILL.md) is the
scaffolding spine (state files, maker≠checker subagents, drivers, gates,
worktree isolation). Five specialized loops run ON it and should be invoked
directly when their job matches — loop-engineer is the builder of last resort,
not a competitor:

```
loop-engineer (scaffold)
  ├─ bug-pipeline        (Hunter → Fixer → Validator over BUG_TRACKER.md)
  ├─ optimization-loop   (audit → fix → measure, metric ratchet)
  ├─ auto-research       (hypothesize → mutate → run → keep/discard, one scalar)
  ├─ dead-code-reaper    (Scout proves dead → Reaper removes → Validator gates)
  └─ test-backfill-loop  (Scout → Writer characterization tests → Verifier "bite")
```

**Design → build → launch backbone (systems-design + autonomous execution).**

```
design-system  ──▶ api-design / data-store-selection  (detail the contract & data layer)
      │
      ▼
design-panel (feature spec)  or  clean-room (port/clone → DESIGN_DOC + PRP)
      │
      ▼
autonomous-advisor  (execute the PRP hands-off; advisor ≠ verifier)
      │
      ├─▶ review-panel        (adversarial pre-merge review of the branch)
      ├─▶ optimization-loop   (Phase 5 hardening, delegated not reimplemented)
      └─▶ production-readiness (launch gate: SLOs, runbooks, drill)
```

**Detection → decision.** [arch-drift-watch](../development/arch-drift-watch/SKILL.md)
(continuous, detection-only) files NEW drift and routes it: structural-judgment →
improve-architecture; duplication/dead code → dead-code-reaper. It never decides
or applies a refactor itself.

**Cross-cutting.** [instrument-observability](../development/instrument-observability/SKILL.md)
produces the telemetry/alerts that [production-readiness](../systems-design/production-readiness/SKILL.md)'s
launch gate consumes (instrument first, then gate). [plan-prune](../development/plan-prune/SKILL.md)
keeps the planning surface canonical *before* [sprint-ticket-runner](../development/sprint-ticket-runner/SKILL.md)
executes it.

## 3. Autonomy ladder and the human gate

Skills declare one of four autonomy postures. The rule: **compute-spending
execution loops are OFFERED, never auto-launched** — they start only on an
explicit human "go". The human always owns architecture, merge, push, cost, and
any irreversible external action (deploys, publishes, emails). See
[AGENTS.md](../AGENTS.md) for the safety floor.

| Posture | Meaning | Example skills |
|---|---|---|
| detection-only | reads + reports, writes no code | arch-drift-watch (L1), improve-architecture (explore), production-readiness, data-store-selection |
| offers-launch | builds + dry-runs one cycle, then asks before running | bug-pipeline, dead-code-reaper, optimization-loop, auto-research, test-backfill-loop, loop-engineer, sprint-ticket-runner |
| fully-autonomous (gated) | runs the whole pipeline, but behind hard phase gates, a 50-cycle cap, maker≠checker, and no irreversible actions | autonomous-advisor |

`offers-launch` skills MUST present the plan/baseline and wait for a human yes;
they MUST define a stop condition (converged / stalled / budget exhausted / no
work left). A loop skill missing either is a defect.

## 4. Dependencies and adapters — bundled vs external

The jar is **self-contained**: every skill runs from its own `SKILL.md` +
bundled `references/`. The items below are *optional accelerators* — absence is
a clean skip, never a blocker. A fresh jar-only checkout has none of them and
must still work.

| Dependency | Status | Used by (referenced) | Posture |
|---|---|---|---|
| FUGAZI (`fugazi` / `fugazi-mcp`) | external static-analysis CLI/MCP | dead-code-reaper, arch-drift-watch (required for the loop), diagnose-loop, review-panel, auto-research, test-backfill-loop (optional) | if present, use; never run `fugazi fix` unattended |
| MemBerry + `memberry-setup` | external user-global MCP + skill, NOT bundled | optimization-loop, autonomous-advisor, clean-room (all optional) | optional persistence adapter; absent = files-only |
| Superpowers suite | external skills | design-panel, diagnose-loop, review-panel, autonomous-advisor (all bundle a standalone fallback) | optional lineage/accelerators |
| `bugfix`, `tdd`, `to-issues`, `triage`, `writing-plans` | external/global skills, NOT in the jar | named as redirects by loop-engineer, optimization-loop, unit-test-quality, design-system | marked external + carrying a plain fallback (F-5) |

## 5. Skill relationship table

One row per installable skill. Prerequisite = what usually runs first; Hands
off to = what runs after / where output goes; Roles = canonical installable
agent names (from the category `manifest.json`; `—` = scaffolds/bundles its
own or needs none).

| Skill | Cat | Prerequisite | Hands off to | Do-not-duplicate / boundary | Installable roles |
|---|---|---|---|---|---|
| add-to-jar | dev | — | skill-forge (queues RED) | NOT authoring from scratch / bulk import | — |
| arch-drift-watch | dev | loop-engineer | improve-architecture, dead-code-reaper | NOT deciding/removing/hardening | `arch-drift-watcher` |
| auto-research | dev | loop-engineer | — | NOT multi-metric (optimization-loop) | — (harness is the checker) |
| autonomous-advisor | dev | a PRP (from design-panel/clean-room) | optimization-loop, review-panel | NOT without a PRP; NOT a port (clean-room); NOT a ticket sprint (sprint-ticket-runner) | `autonomous-advisor`, `autonomous-verifier` |
| bug-pipeline | dev | loop-engineer | diagnose-loop (deep bug) | NOT one bug; NOT metric hardening | `bug-pipeline-hunter`, `-fixer`, `-validator` |
| clean-room | dev | (an original codebase) | autonomous-advisor (via PRP) | NOT your own code; NOT a literal transpile | `clean-room-analyzer`, `-researcher`, `-gap-checker`, `-improvement-sweeper`, `-contamination-reviewer` |
| dead-code-reaper | dev | loop-engineer | improve-architecture, diagnose-loop/bug-pipeline | NOT one symbol; NOT live-but-ugly code | `dead-code-reaper-scout`, `-reaper`, `-validator` |
| design-panel | dev | — | autonomous-advisor (once a PRP exists) | NOT trivial; NOT whole-system (design-system) | `design-explorer`, `-designer`, `-judge`, `-skeptic` |
| diagnose-loop | dev | a repro | bug-pipeline (backlog) | NOT a known fix; NOT a backlog | `diagnose-investigator`, `-analyst`, `-fixer`, `-verifier` |
| improve-architecture | dev | — | dead-code-reaper, arch-drift-watch | NOT autonomous hardening; NOT a rewrite (clean-room) | `architecture-explorer`, `-interface-designer`, `-depth-checker` |
| instrument-observability | dev | — | production-readiness (telemetry → launch gate) | NOT live-incident debugging (diagnose-loop) | — |
| loop-engineer | dev | — | the 5 specialized loops | NOT a one-off task; NOT a hardening pass (optimization-loop) | explorer/implementer/verifier templates (in `references/`) |
| optimization-loop | dev | loop-engineer | improve-architecture (judgment) | NOT one bug; NOT single-scalar (auto-research) | — (scaffolds via loop-engineer) |
| plan-prune | dev | — | sprint-ticket-runner (execute), improve-architecture (direction) | NOT new plans; NOT architecture redesign | — |
| review-panel | dev | a diff/branch/PR | diagnose-loop (deep bug), bug-pipeline (sweep) | NOT a single-file glance; NOT a continuous loop | `review-correctness`, `-security`, `-simplicity`, `-synthesizer` |
| skill-forge | dev | a target skill | loop-engineer (code loop) | NOT a one-line edit; NOT non-skill docs | `skill-forge-pressure-tester`, `-forger`, `-judge`, `-linter` |
| sprint-ticket-runner | dev | plan-prune (clean plan); a worktree mechanism | plan-prune (drift) | NOT a single bug; NOT plan cleanup (plan-prune); NOT a single gated PRP run (autonomous-advisor) | — |
| test-backfill-loop | dev | loop-engineer | diagnose-loop / bug-pipeline (suspected bug → `BUG_TRACKER.md`) | NOT greenfield TDD; NOT judging tests (unit-test-quality) | `test-backfill-scout`, `-writer`, `-verifier` |
| unit-test-quality | dev | TDD (external, optional) | test-backfill-loop, diagnose-loop | NOT continuous backfill; NOT broad hardening | — |
| api-design | sd | design-system | data-store-selection, production-readiness | NOT topology; NOT store internals | `api-contract-designer`, `api-compatibility-reviewer`, `api-abuse-reviewer` |
| data-store-selection | sd | design-system | api-design, production-readiness | NOT topology; NOT API contract | `data-access-analyst`, `data-store-designer`, `data-gate-reviewer` |
| design-system | sd | — | api-design, data-store-selection, production-readiness, design-panel, clean-room | NOT one feature; NOT launch gating | `system-intake-analyst`, `system-topology-designer`, `system-topology-skeptic` |
| production-readiness | sd | design-system | diagnose-loop, optimization-loop | NOT designing the system; NOT live-incident root cause | `readiness-slo-operator`, `readiness-runbook-writer`, `readiness-launch-reviewer` |

**Verification note.** No skill is another skill's verifier — verification is
*intra-skill* (each skill's own maker≠checker agent roles), never inter-skill.
The one apparent exception (design-system → production-readiness) is a sequential
launch handoff, not a check of design-system's own output. review-panel and
autonomous-advisor's `autonomous-verifier` are the closest the jar comes to a
reusable cross-skill checker.

## 6. Shared state files (`agent-state/`)

Conventions are load-bearing: skills assume these canonical sinks. Do not
cross-file (jar-audit findings ≠ bug-pipeline defects ≠ forge results).

| File | Owner / writer | Readers | Purpose |
|---|---|---|---|
| `loop-state.md` | every loop | restarted loop-agent | the restart spine: done / verify / next |
| `triage-inbox.md` | jar-audit, arch-drift-watch | planning | open structural/skill findings (one block each, runnable verify cmd) |
| `BUG_TRACKER.md` | bug-pipeline hunter; test-backfill suspected-bug sink | fixer, validator | defects: pending → fixed → verified |
| `SKILL_FORGE_TRACKER.md` | skill-forge | forge cycles | per-skill RED→GREEN→REFACTOR queue |
| `decisions.md` | any loop | humans, restarts | choices + human-decision items + rationale |
| `failed-attempts.md` | any maker/checker | future cycles | append-only; never deleted |
| `completed.md` | any loop | restarts | durable record of finished work |
| `skill-usage.md` | generated agent hooks | skill-forge | usage/error evidence → improvement candidates |
| `ARCH_BASELINE.json` | arch-drift-watch | the watcher | committed structural baseline to diff against (runtime) |
| `DEAD_CODE_LEDGER.md` | dead-code-reaper | reaper, validator | proven-dead clusters (runtime) |
| `COVERAGE_TARGETS.md` | test-backfill-loop | writer, verifier | chosen coverage targets (runtime) |
| `sprint/` | sprint-ticket-runner | restarts | board, tickets, parallelism map, handoff (runtime) |

## 7. Core / self-improvement substrate

The 7 `core: true` skills form the jar's maintenance system: **loop-engineer**
is the loop spine the loop family builds on; **skill-forge** hardens any skill
against rationalizations; and **bug-pipeline**, **diagnose-loop**, **review-panel**,
**test-backfill-loop**, and **auto-research** are the dogfooded/linted exemplars.
(**add-to-jar** is the *non-core* intake path — drop a skill → `sync-jar.py` →
`audit-jar.py`.) [core-skills.md](core-skills.md) is the authoritative list, with
maturity and evidence. Keep the core set on a fork to retain the jar's ability to
audit, test, review, and improve itself.

## 8. Gates — how the jar verifies itself

The single gate is [`scripts/audit-jar.py`](../scripts/audit-jar.py) (exits 0/1,
also run by CI). It validates: frontmatter parses with name/description; every
description carries a "use when" trigger; skill name == directory; every relative
Markdown link resolves; every `.py` compiles and the scaffolder stays idempotent;
and the three generated artifacts are in sync — [`skills.json`](../skills.json)
(`gen-index.py --check`), plugin manifests (`gen-plugins.py --check`), and the
agent packs (`gen-agent-packs.py --check`). Both `add-to-jar` and `skill-forge`'s
LINT stage terminate in this gate. It does **not** see inside fenced code blocks,
so bundled-template names and embedded examples are out of its current scope —
see [`agent-state/decisions.md`](../agent-state/decisions.md) for proposed
narrow extensions.

Never weaken, skip, or loosen a check to make it pass; a genuinely-wrong check is
a logged human-decision item, not a silent edit.
