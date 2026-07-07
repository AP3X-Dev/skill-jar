---
name: spec-driven-change
description: "Spec-driven development as native, tracker-free markdown: agree on WHAT before code and keep the spec current by construction. Each change ships as a folder (proposal + tasks + a typed spec DELTA) whose requirements use a machine-checkable `### Requirement:` / `#### Scenario:` GIVEN/WHEN/THEN grammar; a bundled validator gates it; on archive the delta merges into a living `openspec/specs/` layer so requirements never drift. Hands a validated change folder to autonomous-advisor / sprint-ticket-runner instead of a hand-written PRP. Use when you want a persistent requirements contract, spec-driven change proposals, an anti-stale living spec, or to align intent before implementation — git-native, no issue tracker, no openspec CLI. NOT for deciding a design's shape (use design-panel / clean-room, which feed this), executing the work (use autonomous-advisor / sprint-ticket-runner, which consume it), or reconciling stale prose plans (use plan-prune; this prevents drift by construction)."
---

# Spec-Driven Change

A lightweight spec layer so you agree on **what** to build before any code is
written — and, unlike every other plan artifact, the spec stays current *by
construction*. Each change is a reviewable folder carrying a typed **delta**
against a living requirements set; when the change ships, the delta merges into
that set, so the requirements never drift out of sync with the code.

This is the OpenSpec discipline rebuilt as **self-contained jar-native markdown**:
no `openspec` CLI, no npm, no issue tracker. Two small stdlib scripts stand in for
the tool's validate/merge; everything else is a markdown convention any agent on
any host can follow. Absence of a Python runtime is a clean skip — the same rules
apply by hand.

**Output:** a validated change folder under `openspec/changes/<name>/` (proposal,
tasks, a typed spec delta) ready for an executor to implement; and, on ship, an
updated living `openspec/specs/` plus the change archived with its `why` intact.

## What this owns — and what it must not touch

This skill is the **only** writer of typed requirement specs. Its boundary is
sharp on purpose, so it composes with the design→build backbone instead of
colliding with it:

| It OWNS | It does NOT do (route elsewhere) |
|---|---|
| The `openspec/` tree (living `specs/` + `changes/` + `changes/archive/`) | **Decide the design's shape** → [design-panel](../design-panel/SKILL.md) (one feature) / [clean-room](../clean-room/SKILL.md) (a port) own the WHICH-SHAPE call; they hand their chosen design in as the change's `design.md`. |
| The requirement/scenario grammar + the four delta headers | **Execute / manage tickets** → [autonomous-advisor](../autonomous-advisor/SKILL.md) (PRP pipeline) and [sprint-ticket-runner](../sprint-ticket-runner/SKILL.md) (board) consume the change folder downstream. This skill stops at a *validated* folder; it runs no makers, checkers, or loops. |
| The validate + archive-merge scripts | **Reconcile stale prose plans** → [plan-prune](../plan-prune/SKILL.md) cleans up after-the-fact drift; this prevents requirement drift up front, and its onboard path *consumes* plan-prune's reconciled plan rather than re-deriving it. |

The word "spec" is overloaded — a design-panel or clean-room "spec" is a
point-in-time *design snapshot*, discarded after handoff. **This skill's "spec" is
a persistent, validated requirement contract** that every future change updates.

## When to Use

- You want intent pinned as a durable, machine-checkable **requirements contract**
  before implementation — not left in chat history where AI agents drift.
- You want the requirements to **stay current**: every shipped change updates them,
  so `openspec/specs/` is always the truth about what the system must do.
- You want to hand an executor (autonomous-advisor / sprint-ticket-runner) a
  *validated* change folder instead of a hand-written, unchecked PRP.
- You're adopting spec-driven development in a brownfield repo (see Onboarding).

## When NOT to Use

- **Deciding which design is right** — that's a design exploration → design-panel
  (one feature) or clean-room (a rewrite). They feed this skill the chosen shape.
- **Actually implementing** — this skill produces intent; autonomous-advisor and
  sprint-ticket-runner run the makers/checkers. Never run a loop from here.
- **Cleaning up fragmented old plans** — that's plan-prune. This skill's onboard
  path can *consume* plan-prune's output, but it does not do reconciliation.
- **A trivial one-file change** — just make it. The change folder is for work worth
  agreeing on first.

## The lifecycle

Four stages. Grammar and templates: [references/spec-format.md](references/spec-format.md),
[references/change-templates.md](references/change-templates.md).

1. **Propose** — create `openspec/changes/<name>/` with `proposal.md` (why/what/scope),
   `tasks.md` (the implementation checklist = the executor's intake), an optional
   `design.md` (paste/point to a design-panel or clean-room design if one exists),
   and one `specs/<capability>/spec.md` **delta** per capability touched.
2. **Validate** — the delta must pass the grammar: requirements at `###`, scenarios
   at exactly `####` (GIVEN/WHEN/THEN), ≥1 scenario each, only the four delta headers.
   `python scripts/validate-spec.py openspec/changes/<name>/specs` — or check by hand
   from spec-format.md. **A change does not leave this skill until it validates.**
3. **Implement (handoff)** — hand the validated change folder to the executor. This
   skill does not implement; `tasks.md` maps to autonomous-advisor's plan or
   sprint-ticket-runner's tickets, and the delta is the machine-checked contract.
4. **Archive (close-out)** — when the change ships, merge its delta into the living
   specs in strict order (RENAMED → REMOVED → MODIFIED → ADDED) and move the folder
   to `openspec/changes/archive/YYYY-MM-DD-<name>/`. The merge is deterministic and
   error-prone by hand — run `python scripts/archive-merge.py --change … --specs …
   --apply`, or apply the documented by-hand procedure. **This close-out is the
   anti-stale engine: the living spec is now current with what shipped.**

## Bundled scripts (optional accelerators)

- `scripts/validate-spec.py` — the jar-native `openspec validate`: flags the silent
  failures (a scenario at the wrong hash depth, a requirement with no scenario, an
  unknown delta header). Exits 0/1 so it can gate a handoff.
- `scripts/archive-merge.py` — the deterministic delta merge in the required order,
  aborting on conflict (modify/remove a missing requirement, add an existing one)
  rather than silently producing a wrong spec.

Both are stdlib-only and self-check with `--selftest`. Neither is required: the
skill is the markdown discipline; the scripts just make the deterministic parts
loud and cheap. No global install, no network, no `openspec` binary.

## Brownfield onboarding

To adopt on an existing codebase, seed the living specs from current behavior:
read routes, handlers, migrations, and tests — and, if [plan-prune](../plan-prune/SKILL.md)
has produced a reconciled canonical plan, **consume it** — then write
`openspec/specs/<capability>/spec.md` in the requirement/scenario grammar and
validate. Onboard reads behavior only to bootstrap the specs; from then on, drift
prevention is the delta+archive lifecycle's job, not a repeated re-derivation.

## Composition

Slots into the design→build backbone as the **WHAT gate** between design and
implementation:

- **Upstream:** design-panel / clean-room decide the shape → their design becomes
  the change's `design.md` and informs the requirement deltas.
- **Core:** this skill encodes the change as a *validated* delta.
- **Downstream:** autonomous-advisor and sprint-ticket-runner consume the change
  folder as immutable intent instead of a hand-written PRP/PRD — a stronger,
  machine-checked contract that fills autonomous-advisor's missing "propose" stage.
- **Alongside:** where `openspec/specs/` is adopted it becomes the canonical
  requirements source; plan-prune points at it and shrinks to reconciling the
  plan/roadmap surface, rather than trying to *be* the requirements layer.

## Operating contract

- **Validate before handoff.** An un-validated change folder is not a deliverable.
  The grammar gate is the cheapest check there is; run it (or apply it by hand) and
  record the result before handing off.
- **The change folder is immutable intent once handed off.** The executor implements
  *against* it; it does not rewrite the requirements to match whatever got built.
- **Deltas, never direct edits.** A change never edits `openspec/specs/` directly —
  it ships a delta that merges on archive. That is what keeps the living spec's
  history and its current state both trustworthy.
- **The living spec is updated by shipping, not by remembering.** The archive merge
  is a required close-out step, not optional cleanup — skip it and you've recreated
  the stale-plan problem this skill exists to prevent.

## Known pressure rationalizations

| Rationalization (the dodge) | Required response |
|---|---|
| "The scenario reads fine as a `### Scenario:` — three hashes vs four is pedantic." | Wrong hash depth **fails silently** — it parses as prose, so the scenario doesn't exist to any tool. Exactly 4 hashes, always. The validator catches it; do not wave it through. |
| "I'll edit `openspec/specs/` directly to save making a delta — same result." | No — a direct edit loses the change's `why` and breaks the merge history. Every change is a delta; the living spec is only ever updated by the archive merge. |
| "The change shipped; updating the living spec is bookkeeping I'll batch later." | The archive merge IS the deliverable's close-out. Skipping it is how the spec goes stale — the failure this skill prevents. Merge on ship, in order, or the change isn't done. |
| "This design decision is obvious; I'll just write the requirement and skip design-panel." | Fine when the shape is genuinely settled — but if there's a real which-shape choice, that's design-panel's call, and it feeds this skill the design. Don't smuggle a design decision into a requirement. |
| "Let me also implement the tasks while I'm here — the folder's ready." | Out of scope. This skill stops at a validated change folder; autonomous-advisor / sprint-ticket-runner implement. Running a maker from here collapses the maker≠checker boundary the jar relies on. |

## Common Mistakes

- **Scenarios at the wrong hash depth.** The number-one broken spec: `###`/`#####`
  or a bullet reads as prose. Exactly `####`.
- **A requirement with no scenario.** Unverifiable intent — every requirement needs
  at least one GIVEN/WHEN/THEN scenario.
- **Editing the living spec directly.** Bypasses the delta history and the merge.
- **Forgetting the archive merge.** The spec silently goes stale — the exact rot
  this skill is built to stop.
- **Turning it into an executor.** It produces validated intent; it does not run the
  work. Hand off to autonomous-advisor / sprint-ticket-runner.

---

*OpenSpec's propose→archive discipline as native, self-contained markdown. Feeds
the jar's implement machinery ([autonomous-advisor](../autonomous-advisor/SKILL.md),
[sprint-ticket-runner](../sprint-ticket-runner/SKILL.md)) a validated, always-current
spec; takes its design from [design-panel](../design-panel/SKILL.md) /
[clean-room](../clean-room/SKILL.md); complements [plan-prune](../plan-prune/SKILL.md)
by preventing the drift plan-prune cleans up.*
