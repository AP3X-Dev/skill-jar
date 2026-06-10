# Panel kit

Bundled prompt templates and the scoring rubric for [design-panel](../SKILL.md). Self-contained — adapt `<placeholders>`.

## Explorer dispatch (×N, parallel, read-only)

Split by concern, not by directory. Typical trio:

```md
Explorer 1 — seams & conventions: Map the code the design must respect around
<area>: module boundaries, naming/error/test conventions, the seams a new
design could plug into. Return a tight map with file:line anchors, no proposals.

Explorer 2 — prior art: Find how this repo (and its deps) already solve
problems shaped like <topic>. Return each precedent, where it lives, and what
it implies a new design should reuse or avoid.

Explorer 3 — constraints: Find the hard constraints on <topic>: public
contracts that can't move, performance/SLO notes, ADRs or docs that settle
related questions. Return the constraint list with sources.
```

## Designer prompt (×2, isolated — do not show them each other)

```md
You are Designer <A|B>. Produce a COMPLETE design for: <framed problem>.

Inputs: the exploration maps and constraints (attached), the judging criteria
(attached). Honor every constraint; you may challenge one explicitly if you
believe it's wrong — flag it, don't silently violate it.

Deliver: the shape (modules/boundaries + a small diagram), key interfaces
(signatures + invariants, not full code), data flow, migration path from
today's code, what this design is BAD at (mandatory — every design pays
somewhere), and effort ballpark.

Differentiation directive: <A: optimize for <e.g. locality / smallest change>;
B: optimize for <e.g. long-term seam / deletion of existing complexity>>.
```

Give A and B different optimization directives — that's what forces different shapes rather than two drafts of the same idea.

## Judge panel prompt

```md
You are an independent judge. Two designs for <problem> are attached, plus the
agreed criteria. You did not write either.

For each criterion, score both designs 1–5 WITH a sentence of evidence from
the design text (no vibes). Then: name what each design is silently paying
for, whether a hybrid beats both (say exactly what to graft), and your
recommendation with the deciding factor.

You may not introduce a new design or new criteria. Return the scorecard.
```

Run 1 judge for ordinary decisions, 3 (majority) when the stakes are high; never let a designer judge.

### Scoring rubric (default criteria — replace with the human's)

| Criterion | 5 looks like | 1 looks like |
|---|---|---|
| Locality | The change/bugs/knowledge concentrate in one place | Every future change touches N modules |
| Blast radius | Failure is contained, reversible | Failure cascades across seams |
| Migration cost | Small reversible steps, tests green between | Big-bang cutover |
| Testability | The interface is the test surface | Tests need heavy setup/mocks |
| Simplicity | Solves the problem with the least mechanism | Speculative generality, extra layers |

## Skeptic prompt (grills the winner)

```md
You are the skeptic. The chosen design is attached. Your job is to break it
on paper before code exists — not to be agreeable.

Attack, in order: failure modes (what breaks first under partial failure?),
scale (where does it fall over at 10x?), edge cases the interfaces don't
admit, hidden coupling (what must change in lockstep?), migration risk, and
the constraint list (does it actually honor every one?).

Return findings as: claim | severity | the concrete scenario that triggers it.
No finding without a scenario.
```

Every finding gets one of three dispositions, recorded in the spec: **resolved** (design amended), **accepted** (known tradeoff, written down), **refuted** (with reasoning). An unaddressed finding blocks the spec.

## MemBerry store shape (optional)

```
berry_store(
  session_id: "<session>",
  task: "[project:<tag>] design: <topic>",
  content: "CHOSE: <winning shape, one line> | CRITERIA: <list> |
            REJECTED: <losing shape> BECAUSE <the deciding factor> |
            SKEPTIC TRADEOFFS ACCEPTED: <list>",
  outcome: "approved"
)
```

Load form at the start of a new panel: `berry_load(task: "design: <topic>", tags: ["project:<tag>"])`. A recorded rejection is re-proposed only with an explicit "its rejection reason no longer holds because <X>".
