---
name: design-panel
description: "Upgraded brainstorming for any non-trivial design: parallel exploration agents map the codebase/domain fast, optional MemBerry recalls prior designs and rejected approaches, then a design-it-twice rule forces at least two genuinely different shapes which an independent judge panel scores against named criteria — the human picks, a skeptic agent adversarially grills the winner (failure modes, scale, edge cases), and only then is the spec written and handed to planning. Use when designing a feature, component, or refactor before implementation and one-shot brainstorming isn't enough — when the user wants design alternatives compared, a design stress-tested, or says 'design it twice'. NOT for trivial changes (just build), full system/architecture intake with SLOs and topology (use systems-design skills), or when a PRP already exists (use autonomous-advisor)."
---

# Design Panel

Brainstorming's biggest failure mode isn't a bad idea — it's the **first plausible idea, iterated**. One designer converges early, explores the repo serially, forgets what past designs already settled, and the human approves a shape no rival shape ever challenged. This skill keeps brainstorming's collaborative dialogue and hard gate (no implementation before an approved design) and adds the jar's machinery: **parallel exploration**, **design memory**, a **design-it-twice panel**, and an **adversarial grilling** before anything becomes a spec.

**Output:** an approved design spec (`docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md` or the repo's convention) that survived a judged comparison and a skeptic's attack — plus the rejected alternatives recorded with reasons, so they aren't re-proposed next quarter.

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
| **Judge panel** (independent) | Score both against the named criteria; recommend with reasoning | Add a third design; rubber-stamp |
| **Skeptic** | Attack the chosen design: failure modes, scale limits, edge cases, hidden coupling, "what breaks first?" | Soften findings to be agreeable |
| **Human** | Set the criteria, pick the winner, accept/reject the skeptic's required changes | — (direction stays human) |

## The process

1. **Recall** *(optional MemBerry)* — `berry_load(task: "design: <topic>", tags: ["project:<tag>"])`: prior designs in this area, ADR-style decisions, and **previously rejected approaches with reasons**. A rejected approach is only re-proposed if its rejection reason no longer holds — say so explicitly.
2. **Explore in parallel** — dispatch read-only explorers (codebase seams + conventions, similar prior art, external constraints). Minutes instead of a serial read, and the designers start informed.
3. **Frame with the human** — brainstorming's dialogue: clarify intent one question at a time, then agree the **judging criteria** (e.g. locality, blast radius, migration cost, testability, time-to-ship). Criteria first, designs second — otherwise the judges improvise values.
4. **Design it twice** — two designers, isolated, each a complete approach: shape, interfaces, data flow, migration path, tradeoffs. If both come back the same shape, the framing over-constrained the problem — loosen it and redo. (A third design is allowed when the two reveal an obvious hybrid; more than three is churn.)
5. **Judge** — the panel scores both against the agreed criteria and recommends with reasoning. Present both + scores to the human; **the human picks**.
6. **Grill** — the skeptic attacks the winner. Each finding is resolved (design amended), accepted (recorded as a known tradeoff), or refuted (with reasoning). No unaddressed findings.
7. **Spec + record** — write the design doc; hand off to **writing-plans** / a PRP. *(MemBerry)* store the decision, the criteria, and the **losing design with why it lost**.

Prompt templates for every role: [references/panel-kit.md](references/panel-kit.md).

## Why two designs, judged — not one, iterated

Iterating one design explores a single basin: every critique gets patched into the same shape, and sunk cost does the rest. Two independent shapes priced against the same criteria expose what each is silently paying for — the comparison is the insight, and the graft ("A's core with B's storage seam") is frequently the real winner. This is the design-twice principle the jar's clean-room and improve-architecture skills already apply to interfaces, promoted to the front of the pipeline.

## Optional: MemBerry design memory

Skip every step marked *(MemBerry)* when the tools are absent — the panel works cold. When present: load prior decisions at step 1 (don't re-litigate what an ADR settled; don't re-propose a recorded rejection unless its reason expired), store at step 7 (the decision, the criteria used, the rejected alternative + reason — the *why*, not the spec text). Files (`docs/adr/`, the spec itself) stay authoritative; memory is the queryable index over them.

## Common Mistakes

- **Two variations instead of two designs.** "Same shape, different library" is one design twice. Force different *shapes* — different module boundaries, different data flow, different ownership.
- **Judging without criteria.** Score-first-define-later lets the panel rationalize a favorite. Agree the criteria with the human before any design exists.
- **The designer defending its design to the skeptic.** The grilling is against the *design*, answered by evidence and amendment — not a debate the author must win.
- **Skipping the human pick.** The panel recommends; it does not decide. Direction is the human's (or, in an autonomous-advisor run, the advisor's).
- **Losing the losers.** An unrecorded rejected design gets re-proposed in three months at full cost. Store it with the reason.

---

*Builds on the superpowers **brainstorming** skill (the dialogue, the no-code-before-approval gate, the spec artifact) and **dispatching-parallel-agents** (exploration + isolated designers) — but stands alone. Downstream: **writing-plans**, [to-prd / autonomous-advisor](../autonomous-advisor/SKILL.md) for execution; the systems-design category's [design-system](../../systems-design/design-system/SKILL.md) uses this panel for its architecture alternatives.*
