---
name: design-panel
description: "Upgraded brainstorming for any non-trivial design: parallel exploration agents map the codebase/domain fast, optional MemBerry recalls prior designs and rejected approaches, then a design-it-twice rule forces at least two genuinely different shapes which an independent judge panel scores against named criteria — the human picks, a skeptic agent adversarially grills the winner (failure modes, scale, edge cases), and only then is the spec written and handed to planning. Use when designing a feature, component, or refactor before implementation and one-shot brainstorming isn't enough — when the user wants design alternatives compared, a design stress-tested, or says 'design it twice'. NOT for trivial changes (just build), full system/architecture intake with SLOs and topology (use systems-design skills), or when a PRP already exists (use autonomous-advisor)."
---

# Design Panel

Brainstorming's biggest failure mode isn't a bad idea — it's the **first plausible idea, iterated**. One designer converges early, explores the repo serially, forgets what past designs already settled, and the human approves a shape no rival shape ever challenged. This skill keeps brainstorming's collaborative dialogue and hard gate (no implementation before an approved design) and adds the jar's machinery: **parallel exploration**, **design memory**, a **design-it-twice panel**, and an **adversarial grilling** before anything becomes a spec.

**Output:** an approved design spec (`docs/agent-runs/specs/YYYY-MM-DD-<topic>-design.md` or the repo's convention) that survived a judged comparison and a skeptic's attack — plus the rejected alternatives recorded with reasons, so they aren't re-proposed next quarter.

## Superpowers is optional

This skill can use Superpowers skills when they are installed, but it does not require them. If `brainstorming`, `dispatching-parallel-agents`, or `writing-plans` are unavailable, run this `SKILL.md` directly: use the bundled role prompts in [references/panel-kit.md](references/panel-kit.md), save the spec to the repo's normal design-doc location, and hand off by writing an implementation plan or PRP.

## Operating Contract

The panel produces a concrete design package, not a brainstorming summary. Before any designer runs, write the framed problem, hard constraints, explicit non-goals, and judging criteria. Each proposed design must name module boundaries, interfaces, data flow, migration path, tests/gates, risks, and tradeoffs. The judge scores only against the agreed criteria, with evidence from the design text. The skeptic's findings are resolved, accepted, or refuted in the final spec; an unaddressed finding blocks handoff.

**The four gates are non-negotiable and survive every deadline.** This skill exists only because each gate fires: (1) two *genuinely different shapes* exist before any judging; (2) the judge is a separate pass that did not author either design; (3) the skeptic grills the winner *before* the spec is written; (4) the human picks. A tight deadline, a "keep it tight" instruction, or a confident hunch shrinks the *artifact* — terser prose, smaller diagram, fewer criteria — never the gates. If you cannot run all four gates in the time available, run a smaller-scope panel (fewer criteria, two-sentence designs) rather than dropping a gate. Skipping a gate means you ran brainstorming, not this skill; say so honestly rather than claiming a panel ran.

## Known pressure rationalizations

These are the dodges a deadline produces. Each is a violation of a gate above. If you catch yourself reasoning any of these, stop and run the gate.

| Rationalization (the dodge) | Required response |
|---|---|
| "The right answer is obvious — a second design would just be a strawman I already know loses." | The second design is not theater; if the first is truly dominant the *judge* proves it cheaply against the criteria. You don't get to skip the comparison by predicting its result — that prediction IS the first-idea-wins failure this skill exists to break. Produce a genuinely different shape and let it be scored. |
| "I designed it, so I understand the tradeoffs best — being my own judge is just extra steps; I'll be honest." | Maker ≠ checker is structural, not a trust test. The author cannot judge — independence is the mechanism, not a formality. Run a separate judge pass (a fresh persona/agent with only the designs + criteria, no memory of authoring). Honesty does not substitute for independence. |
| "User said 'keep it tight' / 'review on my phone' — they want the conclusion, not the panel." | "Tight" constrains the output's length, not the process's gates. Deliver a phone-readable package (the design-package table is already terse), but the two-shapes / independent-judge / pre-spec-skeptic / human-pick gates all still fire. Shrink the artifact, never the gates. |
| "The grilling and the spec are the same activity — I'll address edge cases inline in 'Risks and Mitigations.'" | The skeptic runs as a *separate pass before* the spec, against the winner, with no obligation to be agreeable — precisely so the spec is written knowing what breaks. Writing the spec first and self-addressing risks is the author defending their own design. Grill first; the findings (with dispositions) then populate the spec. |
| "There's a stubbed `RateLimiter` interface and a Redis client already — the shape is half-decided; a second shape fights the codebase." | Existing scaffolding is a *constraint to honor or challenge*, not a decision that collapses the design space to one shape. A designer may challenge a constraint explicitly. Produce a second shape that respects the seams differently (or argues to move them); do not let a month-old stub pre-pick the winner. |
| "I'll make design B a thin variant (token-bucket vs sliding-window-log) — both Redis counters, but it fills the 'two designs' box." | Two implementations of one shape is one design twice. Differentiate by *module boundaries, data flow, ownership, or failure model* — give A and B opposing optimization directives. A judge that can't name a real tradeoff between them proves the framing over-constrained the problem: loosen it and redo. |
| "If the spec has a hole, the implementer or Monday's review will catch it — the review IS the skeptic." | The skeptic is an on-paper adversarial pass you run *before* handoff, not the downstream review. Outsourcing it ships an ungrilled spec into the weekend and burns the review on defects the panel was supposed to surface. Run the grill now; an unaddressed finding blocks the spec. |

## When to Use

- A feature/component/refactor is worth designing before building, and the solution space is wide enough that the first idea shouldn't win by default.
- The user wants alternatives compared, says "design it twice," or wants a design stress-tested before code.
- Design decisions in this area keep getting re-litigated — memory and recorded rejections fix that.

## When NOT to Use

- Trivial or fully-specified changes — just build them.
- Whole-system intake (SLOs, topology, data path, failure path) — that's the systems-design category's [design-system](../../systems-design/design-system/SKILL.md) skill; it can *use* this panel for its alternatives step.
- A PRP already exists for hands-off execution — **autonomous-advisor** owns that pipeline (its advisor can run this skill's panel internally).

## Roles (maker ≠ checker)

The designer never judges its own design — that's how the first idea wins.

| Role | Job | Never |
|---|---|---|
| **Explorers** (×N, parallel) | Map what the design must respect: existing seams, conventions, similar prior art in the repo, constraints | Propose the design |
| **Designer A / Designer B** | Each produces a complete, *genuinely different* approach — different shape, not a parameter tweak | See each other's work before submitting |
| **Judge panel** (independent) | Score both against the named criteria; recommend with reasoning | Add a third design; rubber-stamp; **be the same persona that authored a design** (independence is structural, not a self-honesty promise) |
| **Skeptic** | Attack the chosen design: failure modes, scale limits, edge cases, hidden coupling, "what breaks first?" | Soften findings to be agreeable |
| **Human** | Set the criteria, pick the winner, accept/reject the skeptic's required changes | — (direction stays human) |

## The process

1. **Recall** *(optional MemBerry)* — `berry_load(task: "design: <topic>", tags: ["project:<tag>"])`: prior designs in this area, ADR-style decisions, and **previously rejected approaches with reasons**. A rejected approach is only re-proposed if its rejection reason no longer holds — say so explicitly.
2. **Explore in parallel** — dispatch read-only explorers (codebase seams + conventions, similar prior art, external constraints). Minutes instead of a serial read, and the designers start informed.
3. **Frame with the human** — clarify intent one question at a time, then agree the **judging criteria** (e.g. locality, blast radius, migration cost, testability, time-to-ship). Criteria first, designs second — otherwise the judges improvise values.
4. **Design it twice** — two designers, isolated, each a complete approach: shape, interfaces, data flow, migration path, tradeoffs. Different *shapes* (boundaries/data-flow/ownership), not the same shape with a swapped algorithm or library. A confident hunch that one answer is obvious is not grounds to skip the second shape — the judge prices that hunch in step 5. Existing scaffolding (a stub, a client) is a constraint to honor or explicitly challenge, not a pre-made decision that collapses the space to one shape. If both come back the same shape, the framing over-constrained the problem — loosen it and redo. (A third design is allowed when the two reveal an obvious hybrid; more than three is churn.)
5. **Judge** — the panel scores both against the agreed criteria and recommends with reasoning. Present both + scores to the human; **the human picks**.
6. **Grill** — the skeptic attacks the winner, as a separate pass *before* the spec is written — not folded into the spec's risks section and not deferred to the implementer or the downstream review. Each finding is resolved (design amended), accepted (recorded as a known tradeoff), or refuted (with reasoning). No unaddressed findings. The spec is written *after* the grill, populated by its dispositions.
7. **Spec + record** — write the design doc; hand off to an implementation plan / PRP. *(MemBerry)* store the decision, the criteria, and the **losing design with why it lost**.

Prompt templates for every role: [references/panel-kit.md](references/panel-kit.md).

## Why two designs, judged — not one, iterated

Iterating one design explores a single basin: every critique gets patched into the same shape, and sunk cost does the rest. Two independent shapes priced against the same criteria expose what each is silently paying for — the comparison is the insight, and the graft ("A's core with B's storage seam") is frequently the real winner. This is the design-twice principle the jar's clean-room and improve-architecture skills already apply to interfaces, promoted to the front of the pipeline.

## Optional: MemBerry design memory

Skip every step marked *(MemBerry)* when the tools are absent — the panel works cold. When present: load prior decisions at step 1 (don't re-litigate what an ADR settled; don't re-propose a recorded rejection unless its reason expired), store at step 7 (the decision, the criteria used, the rejected alternative + reason — the *why*, not the spec text). Files (`docs/adr/`, the spec itself) stay authoritative; memory is the queryable index over them.

## Generated agents

Copy-ready generated agents live in [../agents/README.md](../agents/README.md) and are sourced from [../agents/manifest.json](../agents/manifest.json). Install only the roles needed for the active design panel: `design-explorer`, `design-designer`, `design-judge`, `design-skeptic`.

## Common Mistakes

- **Two variations instead of two designs.** "Same shape, different library" is one design twice. Force different *shapes* — different module boundaries, different data flow, different ownership.
- **Judging without criteria.** Score-first-define-later lets the panel rationalize a favorite. Agree the criteria with the human before any design exists.
- **The designer defending its design to the skeptic.** The grilling is against the *design*, answered by evidence and amendment — not a debate the author must win.
- **Skipping the human pick.** The panel recommends; it does not decide. Direction is the human's (or, in an autonomous-advisor run, the advisor's).
- **Losing the losers.** An unrecorded rejected design gets re-proposed in three months at full cost. Store it with the reason.

---

*Borrows the Superpowers brainstorming and parallel-agent disciplines when available, but stands alone through the bundled panel prompts. Downstream: an implementation plan / PRP, [autonomous-advisor](../autonomous-advisor/SKILL.md) for hands-off execution, or the repo's normal planning workflow; the systems-design category's [design-system](../../systems-design/design-system/SKILL.md) uses this panel for its architecture alternatives.*
