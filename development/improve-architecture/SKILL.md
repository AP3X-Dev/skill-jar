---
name: improve-architecture
description: "Find — then ship — deepening opportunities in a codebase: refactors that turn shallow modules into deep ones for testability, locality, and AI-navigability. Human-in-the-loop by design (a strategic human picks direction; the AI explores, drafts, and migrates): explore for friction, present candidates as a visual HTML report, grill the chosen one into a module shape, then convert the approved design into an issue and a careful migration. Informed by the domain language in CONTEXT.md and decisions in docs/adr/. Use when the user wants to improve architecture, find refactoring opportunities, consolidate tightly-coupled modules, reduce AI-driven architecture drift/entropy, make a codebase more testable, or wants a periodic architecture review. NOT for autonomous metric-driven hardening (use optimization-loop), defect repair (use bug-pipeline), or reimplementing a codebase from scratch (use clean-room)."
---

# Improve Codebase Architecture

Surface architectural friction and propose — then ship — **deepening opportunities**: refactors that turn shallow modules into deep ones. The aim is testability, locality, and AI-navigability.

Speed without architecture awareness creates entropy, and AI-assisted development accelerates both the speed and the entropy: every change that ignores the larger codebase can add a little duplication, hidden coupling, or an awkward dependency until the codebase is hard to understand, test, and safely change. The cure is not "cleaner code" — it's better architecture: deeper modules, clearer interfaces, stronger seams, better tests, better locality. This skill is the strategic counterweight to fast tactical change.

**Output:** a concrete architecture review package: a temp HTML report of candidate deepening opportunities, the human-selected candidate's approved module/interface shape, a tracked issue or repo doc containing the migration plan, and a verified behaviour-preserving migration when the human asks to ship it.

## Operating Contract

Every candidate must be evidence-backed and shippable in one bounded migration. Name the files, the current shallow interface, the proposed deeper interface, the behaviour that moves behind the seam, the tests that become the interface gate, and the expected locality/leverage gain. Do not present "cleaner", "more maintainable", or "better separation" as standalone benefits; translate them into glossary terms and concrete files. If a candidate cannot name its migration steps and acceptance gate, mark it `Speculative` or drop it.

## Human-in-the-loop by design

Do not run this as a fully autonomous pass. The split is deliberate:

- **Strategic (the human)** decides: which architecture problems matter, which refactor is worth doing, whether the proposed module shape is correct, which trade-offs are acceptable, whether the change improves long-term maintainability.
- **Tactical (the AI)** does: inspect the codebase, find shallow modules and missing seams, propose boundaries, draft interfaces, ground the design in concrete code, turn the approved decision into an issue and a careful migration.

The AI proposes; the human decides direction. Never let the AI pick architecture direction unreviewed — that is the same maker≠checker discipline the rest of the jar runs on, with the human as the checker on direction.

## Glossary

Use these terms exactly in every suggestion. Consistent language is the point — don't drift into "component," "service," "API," or "boundary." Full definitions in [LANGUAGE.md](references/LANGUAGE.md).

- **Module** — anything with an interface and an implementation (function, class, package, slice).
- **Interface** — everything a caller must know to use the module: types, invariants, error modes, ordering, config. Not just the type signature.
- **Implementation** — the code inside.
- **Depth** — leverage at the interface: a lot of behaviour behind a small interface. **Deep** = high leverage. **Shallow** = interface nearly as complex as the implementation.
- **Seam** — where an interface lives; a place behaviour can be altered without editing in place. (Use this, not "boundary.")
- **Adapter** — a concrete thing satisfying an interface at a seam.
- **Leverage** — what callers get from depth.
- **Locality** — what maintainers get from depth: change, bugs, knowledge concentrated in one place.

Key principles (see [LANGUAGE.md](references/LANGUAGE.md) for the full list):

- **Deletion test**: imagine deleting the module. If complexity vanishes, it was a pass-through. If complexity reappears across N callers, it was earning its keep.
- **The interface is the test surface.**
- **One adapter = hypothetical seam. Two adapters = real seam.**

This skill is _informed_ by the project's domain model. The domain language gives names to good seams; ADRs record decisions the skill should not re-litigate.

## When to run

Run this when the codebase resists change:

- a feature touches too many unrelated files
- the same business rule is duplicated, especially when frontend and backend can drift apart
- a module has a complicated interface but little useful implementation behind it (shallow)
- tests need too much setup, or a behaviour has no single owner
- bugs keep reappearing in scattered places (low locality)
- parallel implementations must be kept in sync by hand
- you are preparing a legacy codebase for AI-assisted development

**Cadence — architecture review is periodic, not one-shot.** Entropy compounds; catch it while a refactor is still small:

- **Active / AI-heavy development** — every couple of days, and after every significant burst of AI-generated changes (a finished sprint or major feature).
- **Legacy codebases** — before major feature work, so the new feature lands on a sound shape.

## Process

### 1. Explore

Read the project's domain glossary (CONTEXT.md) and any ADRs (`docs/adr/`) in the area you're touching first — see [CONTEXT-FORMAT.md](references/CONTEXT-FORMAT.md) and [ADR-FORMAT.md](references/ADR-FORMAT.md) for the formats this skill reads and writes.

Then use the Agent tool with `subagent_type=Explore` to walk the codebase. Don't follow rigid heuristics — explore organically and note where you experience friction:

- Where does understanding one concept require bouncing between many small modules?
- Where are modules **shallow** — interface nearly as complex as the implementation?
- Where have pure functions been extracted just for testability, but the real bugs hide in how they're called (no **locality**)?
- Where do tightly-coupled modules leak across their seams?
- Which parts of the codebase are untested, or hard to test through their current interface?

Apply the **deletion test** to anything you suspect is shallow: would deleting it concentrate complexity, or just move it? A "yes, concentrates" is the signal you want.

**Optional — ground the exploration with FUGAZI.** If [FUGAZI](https://github.com/AP3X-Dev/FUGAZI) (CLI `fugazi` or the `fugazi-mcp` MCP server) is available, run it read-only to turn "I feel friction here" into deterministic signals before you write the report: `fugazi circular-deps --format json` (coupling the deletion test can't see by eye), `fugazi boundaries --format json` (seam violations against declared zones), `fugazi health --format json` (the `complexity-hotspot` / `cognitive-complexity` functions — frequently shallow modules hiding a complex implementation), and `fugazi dupes --format json` (the same rule implemented twice, especially across a front/back seam where it can drift). These tell you *where to look*, never *what to ship* — every candidate still goes through the human-judged grilling loop. Skip entirely if FUGAZI isn't installed; organic exploration is the baseline.

### 2. Present candidates as an HTML report

Write a self-contained HTML file to the OS temp directory so nothing lands in the repo. Resolve the temp dir from `$TMPDIR`, falling back to `/tmp` (or `%TEMP%` on Windows), and write to `<tmpdir>/architecture-review-<timestamp>.html` so each run gets a fresh file. Open it for the user — `xdg-open <path>` on Linux, `open <path>` on macOS, `start <path>` on Windows — and tell them the absolute path.

The report uses **Tailwind via CDN** for layout and **Mermaid via CDN** for graph-shaped diagrams, mixed with hand-built CSS/SVG visuals for the editorial ones (mass diagrams, cross-sections, collapse animations). Each candidate gets a **before/after visualisation**. Be visual.

For each candidate, render a card with: **Files** involved · **Problem** (why the architecture causes friction) · **Solution** (plain English) · **Benefits** (in terms of locality and leverage, and how tests improve) · **Before/After diagram** (side-by-side, illustrating the shallowness and the deepening) · **Recommendation strength** badge (`Strong`, `Worth exploring`, `Speculative`). End with a **Top recommendation** section.

Apply the candidate evidence contract in [HTML-REPORT.md](references/HTML-REPORT.md). A candidate with no file anchors, no current/proposed interface, or no acceptance gate is too abstract to show as `Strong`.

**Use CONTEXT.md vocabulary for the domain, and [LANGUAGE.md](references/LANGUAGE.md) vocabulary for the architecture.** If `CONTEXT.md` defines "Order," talk about "the Order intake module" — not "the FooBarHandler," and not "the Order service."

**ADR conflicts**: if a candidate contradicts an existing ADR, only surface it when the friction is real enough to warrant revisiting the ADR. Mark it clearly in the card (e.g. a warning callout: _"contradicts ADR-0007 — but worth reopening because…"_). Don't list every theoretical refactor an ADR forbids.

See [HTML-REPORT.md](references/HTML-REPORT.md) for the full HTML scaffold, diagram patterns, and styling guidance.

Do NOT propose interfaces yet. After the file is written, ask the user: "Which of these would you like to explore?"

### 3. Grilling loop

Once the user picks a candidate, drop into a grilling conversation. Walk the design tree with them — constraints, dependencies, the shape of the deepened module, what sits behind the seam, what tests survive.

Side effects happen inline as decisions crystallize:

- **Naming a deepened module after a concept not in `CONTEXT.md`?** Add the term to `CONTEXT.md` ([CONTEXT-FORMAT.md](references/CONTEXT-FORMAT.md)). Create the file lazily if it doesn't exist.
- **Sharpening a fuzzy term during the conversation?** Update `CONTEXT.md` right there.
- **User rejects the candidate with a load-bearing reason?** Offer an ADR ([ADR-FORMAT.md](references/ADR-FORMAT.md)), framed as: _"Want me to record this as an ADR so future architecture reviews don't re-suggest it?"_ Only offer when the reason would actually be needed by a future explorer to avoid re-suggesting the same thing — skip ephemeral reasons ("not worth it right now") and self-evident ones.
- **Want to explore alternative interfaces for the deepened module?** See [INTERFACE-DESIGN.md](references/INTERFACE-DESIGN.md).

### 4. Ship the approved deepening

Once grilling converges on a module shape the human approves, take it the rest of the way — convert the design into an issue and execute a careful, behaviour-preserving migration. See [SHIP-IT.md](references/SHIP-IT.md).

Two gates before any code moves:

- **Design signed off.** Don't start moving code on a shape the human hasn't approved.
- **Depth check.** Re-confirm the change actually deepens: does the interface get simpler, does the module hide more, does the caller need to know less, does related behaviour move into one place? If the honest answer is no, the refactor is only rearranging files — stop and rework the shape, don't ship it.

The migration is small, reversible steps with tests green between each, ending with the deep-module checklist as the acceptance gate.

## Optional: memory, and turning detection into a loop

Both are off by default — this skill is human-in-the-loop, and `CONTEXT.md` + the ADRs are the authoritative record. These only add reach when the tools are present.

- **(MemBerry)** If a MemBerry-style memory MCP is available, `berry_load(task: "architecture review: <area>", tags: ["project:<tag>"])` at the start of Explore to recall prior reviews and the directions you already rejected, and `berry_store` the **decision and its load-bearing reason** after a candidate is accepted or rejected — the same thing an ADR captures, in queryable form. On any conflict, the ADR / `CONTEXT.md` files win; memory is a convenience index over them, never the source of truth.
- **Detection on a schedule.** The *finding* half of this skill can run unattended even though the *deciding* half can't. Point [dead-code-reaper](../dead-code-reaper/SKILL.md) at the removal side, or stand up a [loop-engineer](../loop-engineer/SKILL.md) loop that watches `fugazi boundaries` / `circular-deps` and files new drift to a triage inbox for your next review. The human still owns every architecture decision; the loop just keeps the candidate list fresh between reviews.

## Generated agents

Copy-ready generated agents live in [../agents/README.md](../agents/README.md) and are sourced from [../agents/manifest.json](../agents/manifest.json). Install only the roles needed for the active architecture pass: `architecture-explorer`, `architecture-interface-designer`, `architecture-depth-checker`.

## Common Mistakes

- **Running it autonomously.** This needs human judgment on direction. The AI explores and drafts; it does not decide what is healthy for the codebase.
- **Shipping a rename.** A change that moves files between modules without shrinking an interface or concentrating behaviour is not a deepening. The depth check exists to catch this.
- **Drifting vocabulary.** "Component / service / boundary / wrapper" erode the whole point. Use the glossary terms exactly.
- **Fixing the whole codebase at once.** Pick one candidate. Deepen it. Then run the review again.
- **Layering tests instead of replacing them.** Old unit tests on the shallow modules become waste once the deepened interface is tested. Delete them — see [DEEPENING.md](references/DEEPENING.md).

---

**Guiding principle:** AI agents are strong tactical programmers — fast to inspect and change code. Architecture still needs a strategic programmer. Use the AI to explore, propose, and implement; use human judgment to decide the long-term shape.
