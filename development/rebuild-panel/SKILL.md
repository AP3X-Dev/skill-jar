---
name: rebuild-panel
description: "First-principles rebuild analysis for a subsystem you OWN — answers 'if we were rebuilding X from scratch with intent to significantly improve and optimize it, what would we recommend?' WITHOUT rewriting anything. Parallel mappers ground every claim in real code, git/defect history, and docs/memory; isolated first-principles lenses (substrate, keep-verbatim archaeologist, coupling/blast-radius, operability/cost) each propose from-scratch changes; a skeptic attacks them; a synthesizer emits ONE report: keep-verbatim list, ranked load-bearing changes with the pain each retires, a strangler-fig sequence with effort classes, and a per-recommendation owner routing to executor skills. Detection-only — the human picks; it never ships a change. Use when the user asks what a from-first-principles rebuild would change, wants a refactor/improvement roadmap for a living subsystem, or a rebuild-vs-refactor verdict. NOT for a full rewrite (clean-room), one module's deepening (improve-architecture), or executing changes."
---

# Rebuild Panel

The question this skill answers is the one every maturing system eventually earns: *"if we were rebuilding this from first principles, what would we do differently?"* Answered casually, it produces a hot take — ungrounded opinions about code nobody re-read, a rewrite fantasy, or a list of nitpicks with no order. Answered well, it produces the most valuable planning artifact a subsystem can have: what to **protect**, what to **change first because everything else cascades from it**, and the **safe order** to do it in — each item grounded in the actual code and the actual pain history, and routed to the skill that can execute it.

**Output:** ONE rebuild recommendation report (saved to the repo's design-doc location): a keep-verbatim list, ranked load-bearing changes, a strangler-fig sequence with effort classes, and an owner per recommendation. The panel never ships a change — detection-only, the human picks.

## When to Use

- The user asks "if we rebuilt X from first principles / from scratch, what would you recommend?" or wants a significant-improvement roadmap for a subsystem that already works.
- A subsystem has accumulated pain (recurring defect classes, N-places-to-update taxes, scaling walls) and the team wants a grounded rebuild-vs-refactor verdict before committing anywhere.
- Periodically, as a deeper cousin of an architecture review — when the question is "what would we change" rather than "what drifted."

## When NOT to Use

- **A from-scratch rewrite or port is already the goal** — that's [clean-room](../clean-room/SKILL.md) (its Transparent Mode covers code you own). If *this panel's* synthesis concludes the answer is a full rewrite, it routes to clean-room and **stops** — it never emits a rewrite DESIGN_DOC or PRP itself.
- **One module's deepening** — go straight to [improve-architecture](../improve-architecture/SKILL.md).
- **Executing anything** — the owners in the report execute; this panel only recommends.
- **Continuous drift detection** — [arch-drift-watch](../arch-drift-watch/SKILL.md) watches for *new* entropy on a schedule; this panel is a one-shot deep read.
- **Designing a not-yet-built feature** ([design-panel](../design-panel/SKILL.md)) or whole-system topology from requirements ([design-system](../../systems-design/design-system/SKILL.md)).
- **Tracking execution of the accepted sequence** — that's a [sprint-ticket-runner](../sprint-ticket-runner/SKILL.md) board or [plan-prune](../plan-prune/SKILL.md)'s reconciliation, not a mode of this skill. After a phase ships, re-run this panel **scoped to the changed area**; there is no campaign ledger.

## Operating Contract

Every recommendation must be **grounded, priced, and routed**. Grounded: it names files/symbols the mappers actually read, and the pain it retires cites evidence (defect history, an incident, a measured tax like "defined in four unsynced places"). Priced: it carries an effort class (`days` / `week-class` / `incremental`) and its position in the strangler sequence. Routed: it names the executor skill (or human decision) that owns it, one line each. A recommendation the synthesizer cannot ground in the mappers' output is **discarded, not softened** — first-principles thinking earns its place only when it survives contact with the real code.

The report leads with the **verdict**: what altitude the rebuild actually applies at ("the architecture survived; the substrate didn't"), because that one sentence is what the human decides with.

## Roles (maker ≠ checker)

| Role | Job | Never |
|---|---|---|
| **Mappers** (×N, parallel, read-only) | Ground truth: code map (size, seams, module inventory), git/defect history (where pain actually came from), docs + prior plans/decisions | Recommend anything |
| **Lenses** (×4, isolated) | Each answers "if rebuilt from scratch, what changes?" under ONE assigned directive (below) | See each other's work; propose ungrounded changes |
| **Skeptic** | Attack the pooled recommendations: cheaper in-place alternative? blast radius underpriced? keep-item mislabeled as change? | Soften findings; add recommendations |
| **Synthesizer** | Merge survivors into the single report: dedupe, rank, sequence, route; discard anything ungrounded | Invent new recommendations; execute |
| **Human** | Set scope, pick what to act on, own every go | — (direction stays human) |

The four lens directives — different directives force different findings, the same trick design-panel uses to force different shapes:

1. **Substrate** — the foundational choices everything cascades from: data model, wire/exchange formats, execution/concurrency model, how extension points are defined. One substrate defect typically explains many surface pains; say which.
2. **Keep-verbatim archaeologist** — what *survived contact with reality* and must be protected: designs validated by incidents, security boundaries that held, careful code that earned its complexity. The protect-list is a first-class deliverable, not a courtesy.
3. **Coupling / blast-radius** — where change is expensive today: god modules, define-it-in-N-places taxes, hidden lockstep coupling, the seams a strangler needs.
4. **Operability / cost** — what it's like to run: restart/resume behavior, scaling ceilings, budgets and cost controls, eval/verification gaps, tribal knowledge that should be mechanized.

## The process

1. **Frame with the human** — the target subsystem (name it precisely: package/dirs), what "significantly improve" means to them (reliability? velocity? cost? scale?), and any hard constraints (can't change the public API, must stay on X). Scope in, scope out.
2. **Recall** *(optional MemBerry)* — `berry_load(task: "rebuild analysis: <subsystem>", tags: ["project:<tag>"])`: prior reviews, shipped plans, known pain, past rejections.
3. **Map in parallel** — dispatch read-only mappers: (a) the code itself — LOC, module inventory, seams, extension points; (b) `git log`/tracker history over the target — recurring defect classes, fleet incidents, hot files; (c) docs/ADRs/prior plans. No recommendations leave this stage — only evidence.
4. **Run the four lenses, isolated** — each gets the full mapper output + its one directive, returns grounded from-scratch recommendations (or keep-items, for the archaeologist) with evidence and a rough effort class.
5. **Grill** — the skeptic attacks the pooled output *before* synthesis. Every finding gets a disposition (recommendation amended / dropped / defended with evidence).
6. **Synthesize** — one report, in this order: **verdict** → **keep-verbatim list** → **ranked load-bearing changes** (pain retired + evidence, each) → **strangler-fig sequence** (ordered phases, effort classes, what each unblocks, riders that come along free) → **owner routing table**. Template in [references/rebuild-kit.md](references/rebuild-kit.md).
7. **Human picks** — present the report; the human decides which recommendations become work and when. *(MemBerry)* store the verdict, the keep-list, and rejected recommendations with reasons.
8. **After a phase ships** — re-run the panel scoped to the changed area if wanted. The sequence lives in the report and, once accepted as work, in the executor's own state (a sprint board, an issue) — never in a panel-owned ledger.

## Routing — every recommendation names its owner

| Recommendation class | Owner | Fence |
|---|---|---|
| Verdict = "full rewrite is genuinely justified" | [clean-room](../clean-room/SKILL.md) | Route and STOP. This panel never writes the rewrite's design doc or PRP. |
| Build-class change (substrate swap, new subsystem) | [design-panel](../design-panel/SKILL.md) → [spec-driven-change](../spec-driven-change/SKILL.md) → [autonomous-advisor](../autonomous-advisor/SKILL.md) | The panel's recommendation is the *input* to that pipeline, not a spec. |
| Module deepening / seam reshape | [improve-architecture](../improve-architecture/SKILL.md) | **One candidate at a time** — it refuses batches by design. |
| Provably single-use over-engineering | [simplify-loop](../simplify-loop/SKILL.md) | Behavior-identical collapses only. |
| Confirmed-dead code | [dead-code-reaper](../dead-code-reaper/SKILL.md) | — |
| Measured hardening / perf / quality | [optimization-loop](../optimization-loop/SKILL.md) | — |
| Coverage gaps blocking safe migration | [test-backfill-loop](../test-backfill-loop/SKILL.md) | — |
| Sequenced execution of accepted phases | [sprint-ticket-runner](../sprint-ticket-runner/SKILL.md) | The board is theirs; the panel keeps no execution state. |

Routing is a column in the report, not a dispatch engine — the human invokes the owner skill when they're ready.

## Known pressure rationalizations

| Rationalization (the dodge) | Required response |
|---|---|
| "I know this codebase — I can write the recommendation without re-sweeping it." | Staleness is exactly how rebuild takes go wrong. The mappers run every time; a recommendation that cites no freshly-mapped evidence is discarded by contract. |
| "The keep-list is filler — the changes are what the user wants." | The keep-list is half the deliverable. An unlabeled keep-item gets bulldozed by the next migration; 'what survived contact with reality' is the most expensive knowledge in the report. |
| "This is big enough that I should just write the rewrite plan while I'm here." | That's clean-room's pipeline. The moment the verdict is 'rewrite,' route and stop — writing the PRP here duplicates clean-room Phase 1–2 without its gates. |
| "Batch the five module-deepening items into one improve-architecture handoff — efficient." | improve-architecture's own contract is one candidate at a time. Hand over the top one; the report holds the rest in sequence. |
| "Skip the skeptic — the lenses already argued with each other." | The lenses never saw each other's work (by design). The skeptic is the only pass that prices the pooled output. Maker ≠ checker survives every deadline. |
| "Track the migration in a little ledger here so the panel stays in the loop." | Execution state belongs to the executors (sprint board, issues, loop-state). A panel-owned campaign ledger was explicitly cut from this skill as duplicating three others — don't smuggle it back. |

## Common Mistakes

- **Recommendations without pain.** "Cleaner" is not pain. Each change names what it retires: a defect class, a define-it-twice tax, an outage mode, a cost line.
- **Big-bang framing.** The sequence is strangler-fig: phases with reversible steps, riding existing seams. If a phase can't name its seam, it isn't a phase yet — it's a wish.
- **Effort theater.** `days` / `week-class` / `incremental` is a class, not a schedule commitment. Precision beyond that is fiction at analysis time.
- **Letting the substrate lens win by default.** Substrate changes cascade — that's why they rank high *when grounded*, and why ungrounded ones are the most expensive mistake the panel can ship. The skeptic prices them hardest.
- **Losing the rejections.** A recommendation the human rejects is recorded with the reason (MemBerry or the report's appendix) — or it comes back at full cost next quarter.

## Optional accelerators

MemBerry (recall at step 2, store at step 7) and FUGAZI (mapper (a) may use `fugazi boundaries` / `health` / `dupes` for the structural map) are optional — absent, the mappers work from `rg`/`git` alone and the panel runs cold. Superpowers' brainstorming/dispatching skills are optional lineage; the bundled kit stands alone.

## Generated agents

Copy-ready generated agents live in [../agents/README.md](../agents/README.md), sourced from [../agents/manifest.json](../agents/manifest.json): `rebuild-mapper`, `rebuild-lens`, `rebuild-skeptic`, `rebuild-synthesizer`. Role prompts and the report template: [references/rebuild-kit.md](references/rebuild-kit.md).

---

*Upstream: nothing required — this panel is a front door. Downstream: every row of the routing table. The nearest relatives and their fences: [clean-room](../clean-room/SKILL.md) owns actual rewrites; [improve-architecture](../improve-architecture/SKILL.md) owns single-module deepening and receives candidates one at a time; [arch-drift-watch](../arch-drift-watch/SKILL.md) owns continuous detection; [sprint-ticket-runner](../sprint-ticket-runner/SKILL.md) owns execution boards.*
