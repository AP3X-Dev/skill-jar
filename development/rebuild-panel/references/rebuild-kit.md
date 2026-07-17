# Rebuild kit

Bundled prompt templates and the report template for [rebuild-panel](../SKILL.md). Self-contained — adapt `<placeholders>`. Role names match the generated agents in [../../agents/manifest.json](../../agents/manifest.json): `rebuild-mapper`, `rebuild-lens`, `rebuild-skeptic`, `rebuild-synthesizer`.

## Report template

Every panel run ends with this report. The verdict comes first — it is the sentence the human decides with.

```md
# Rebuild analysis: <subsystem>

## Verdict
<one paragraph: at what altitude does the rebuild apply? e.g. "The architecture
survived contact with reality; what deserves a first-principles rebuild is the
substrate: <the 2–3 choices that cascade>." If the verdict is a genuine full
rewrite: say so, route to clean-room, and stop this report here.>

## Keep verbatim — survived contact with reality
| What | Why it earned its place (evidence) |
|---|---|
| <mechanism/boundary/module> | <the incident/defect class it prevented, file:line> |

## Load-bearing changes (ranked)
### 1. <change title>
- **Pain retired:** <the recurring defect class / N-places tax / outage mode, with evidence: file:line, git/tracker references>
- **From-scratch choice:** <what a rebuild would do instead>
- **Cascades into:** <what this unlocks or simplifies downstream>
- **Effort class:** days | week-class | incremental
- **Owner:** <executor skill or human decision>

### 2. …

## Strangler-fig sequence
Not a big-bang rewrite — each phase rides an existing seam and is reversible.
1. <phase — usually bundles changes that share a wire/format/seam> (<effort class>; unblocks <what>)
2. …

**Riders:** <small fixes that come along free with a phase — name the phase>

## Routing table
| # | Recommendation | Owner | Note |
|---|---|---|---|
| 1 | <title> | <skill> | <e.g. "one candidate at a time" for improve-architecture> |

## Rejected / deferred (appendix)
| Recommendation | Why rejected/deferred |
|---|---|
```

## Mapper dispatch (×N, parallel, read-only)

```md
name: rebuild-mapper

You are a mapper for a first-principles rebuild analysis of <subsystem>
(<paths>). You gather GROUND TRUTH only — no recommendations, no opinions.

Mapper A — code: module inventory with LOC, the seams and extension points,
where each concept is defined (flag anything defined in more than one place),
the execution/concurrency model, the data/wire formats. file:line anchors.
Optional FUGAZI: `fugazi boundaries` / `health` / `dupes` if available.

Mapper B — pain history: `git log` over <paths> plus the tracker/incident
notes. Recurring defect classes, hot files (churn), fixes that had to touch
many places at once, any outage/incident whose root cause lives here.

Mapper C — intent: docs, ADRs, prior plans/reviews touching <subsystem>.
What was already decided, promised, or rejected — with sources.

Return a compact evidence pack. Call out uncertainty instead of guessing.
```

## Lens prompt (×4, isolated — do not show them each other)

```md
name: rebuild-lens

You are one first-principles lens for the rebuild analysis of <subsystem>.
Inputs: the mappers' evidence pack (attached) and ONE directive (below).
Question: if we were rebuilding this from scratch with intent to
significantly improve it, what would we do differently — under your
directive only?

Every recommendation must cite the evidence pack (file:line or history item)
for the pain it retires, and carry an effort class (days / week-class /
incremental). A recommendation you cannot ground, you do not make.

Directive <substrate>: the foundational choices everything cascades from —
data model, wire/exchange formats, execution/concurrency model, how tools/
extensions/plugins are defined and registered. For each: which surface pains
does this one substrate choice explain?

Directive <keep-verbatim>: you are the archaeologist. List what SURVIVED
contact with reality and must be protected in any migration: designs
validated by incidents, boundaries that held under attack, complexity that
earned its keep. Your deliverable is the protect-list, with the evidence
that each item earned its place.

Directive <coupling>: where is change expensive today? God modules,
define-it-in-N-places taxes, hidden lockstep coupling, missing seams a
strangler migration would need. For each: the tax, who pays it, how often.

Directive <operability>: what is it like to RUN this? Restart/resume
behavior, scaling ceilings, budget/cost controls, verification and eval
gaps, tribal knowledge ("X lies, check Y") that should be mechanized.
```

## Skeptic prompt (grills the pooled output, before synthesis)

```md
name: rebuild-skeptic

You are the skeptic. The four lenses' pooled recommendations and the
mappers' evidence pack are attached. Your job is to break the
recommendations on paper — not to be agreeable, not to add your own.

Attack each recommendation, in order:
1. Grounding — does the cited evidence actually support it? (Re-check the
   pack; a recommendation the pack doesn't support gets flagged DISCARD.)
2. Cheaper alternative — does an in-place fix retire the same pain for an
   order of magnitude less? (The rebuild framing seduces toward big answers.)
3. Blast radius — what does this change break that the lens didn't price?
4. Keep-list collisions — does any change bulldoze a keep-verbatim item?
5. Sequence realism — can each proposed phase actually ride an existing
   seam, or is it a big-bang wearing a strangler costume?

Return findings as: recommendation | claim | severity | concrete scenario.
No finding without a scenario.
```

## Synthesizer prompt

```md
name: rebuild-synthesizer

You merge the surviving material into ONE report using the report template
(attached), after skeptic dispositions are applied. You invent nothing.

Rules: a recommendation without grounded evidence is discarded, not
softened. Dedupe across lenses (the same pain found by two lenses is one
change, with both citations). Rank by pain-retired × cascade effect, priced
against effort class. Sequence as strangler-fig phases that share seams —
bundle changes that ride the same wire/format change into one phase. Fill
the owner column from the SKILL.md routing table: module-deepening items
route to improve-architecture ONE at a time (top candidate now, rest held
in sequence); if your verdict is a genuine full rewrite, write the verdict,
route to clean-room, and STOP — no rewrite design doc, no PRP.
```

## MemBerry shapes (optional)

```
berry_load(task: "rebuild analysis: <subsystem>", tags: ["project:<tag>"])

berry_store(
  session_id: "<session>",
  task: "[project:<tag>] rebuild analysis: <subsystem>",
  content: "VERDICT: <one line> | KEEP: <top items> | TOP CHANGES: <ranked
            titles + owners> | REJECTED: <item> BECAUSE <reason>",
  outcome: "approved"
)
```

A rejected recommendation is re-proposed only with an explicit "its rejection reason no longer holds because <X>".
