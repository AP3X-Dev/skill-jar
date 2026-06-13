# Triage Inbox -- jar-audit

> Discovery appends findings here; planning promotes one into loop-state.md Open
> Tasks. One finding = one heading block (NOT a table). Every finding needs a
> runnable Verification command. Enrich from references/state-templates.md.

## Findings

> Source for all F-* below: ecosystem-audit-1 (deep evidence-backed audit of all
> 23 skills, 2026-06-12). The structural gate is GREEN (208/208); these are
> defects the gate cannot see (routing, handoff wiring, external-dep framing,
> fresh-agent safety). The highest-leverage fixes from the same audit were
> already applied this cycle (see completed.md): bundled-template name alignment,
> the loop-architecture link, sprint-ticket-runner's launch gate, and
> docs/ecosystem-map.md. The items below are deferred for the next cycles.

### F-1 -- autonomous-advisor treats unbundled `memberry-setup` as a hard halt, and contradicts itself on whether MemBerry is optional
- **Source:** ecosystem-audit-1 (reference-integrity + verification-gates lenses)
- **Priority:** High
- **Risk:** medium
- **Evidence:** `development/autonomous-advisor/SKILL.md:57` "invoke the `memberry-setup` skill to bootstrap before continuing"; `:142` "If the call fails, surface the error and halt" vs `:585` "MemBerry memory — optional ... when available". `memberry-setup` is user-global, not bundled in the jar. A fresh jar-only checkout cannot satisfy the halt path. optimization-loop already frames MemBerry as an OPTIONAL adapter; make autonomous-advisor match.
- **Suggested owner:** implementer (then skill-forge-judge)
- **Verification command:** `grep -n "optional" development/autonomous-advisor/SKILL.md && ! grep -n "surface the error and halt" development/autonomous-advisor/SKILL.md`

### F-2 -- clean-room presents `memberry-setup` as default-mandatory rather than an optional accelerator
- **Source:** ecosystem-audit-1 (reference-integrity lens)
- **Priority:** Medium
- **Risk:** low
- **Evidence:** `development/clean-room/SKILL.md:263,265` "invoke the `memberry-setup` skill ... do **not** silently skip MemBerry setup" (has a §0 opt-out at `:734`, which softens it). Frame MemBerry the way FUGAZI is framed at `:655` ("if available"): absence is a clean skip, not a blocker.
- **Suggested owner:** implementer
- **Verification command:** `grep -n "if MemBerry is available\|optional" development/clean-room/SKILL.md`

### F-3 -- instrument-observability has no "NOT for" boundary; collides with diagnose-loop / optimization-loop on the "production debugging" trigger
- **Source:** ecosystem-audit-1 (routing-overlap + verification-gates lenses)
- **Priority:** Medium
- **Risk:** low
- **Evidence:** `development/instrument-observability/SKILL.md` description ends at "...only when the repo or user requires them." with no NOT-for clause; body has none. It is the only development skill with an empty negative boundary, yet lists "production debugging" as a trigger. Add a NOT-for: diagnose a single live incident → diagnose-loop; general hardening → optimization-loop; one known bug → bugfix. (Editing the description requires `python scripts/gen-index.py` to re-sync skills.json.)
- **Suggested owner:** implementer
- **Verification command:** `grep -iE "not for|when not to use" development/instrument-observability/SKILL.md && python scripts/audit-jar.py --quiet`

### F-4 -- add-to-jar has no "NOT for" boundary
- **Source:** ecosystem-audit-1 (map: add-to-jar)
- **Priority:** Low
- **Risk:** low
- **Evidence:** `development/add-to-jar/SKILL.md` has a clear trigger but no negative boundary (e.g. NOT for authoring a skill from scratch — that is skill-forge — or bulk-importing many skills in one pass). Same gen-index re-sync applies if the description changes.
- **Suggested owner:** implementer
- **Verification command:** `grep -iE "not for|when not to use" development/add-to-jar/SKILL.md && python scripts/audit-jar.py --quiet`

### F-5 -- external-skill redirects (`bugfix`, `tdd`, `to-issues`, `triage`, `writing-plans`) are named without an external/optional marker or fallback
- **Source:** ecosystem-audit-1 (reference-integrity lens)
- **Priority:** Medium
- **Risk:** low
- **Evidence:** loop-engineer (desc + `:66` "use **bugfix**"), optimization-loop (`:61` + desc), improve-architecture (handoffs `to-issues`/`triage`/`tdd`), unit-test-quality (`:32` "use TDD"), design-system (`:79` "feeds **writing-plans**"). None marks these as external/global skills absent from a jar-only checkout, and none gives a plain fallback. diagnose-loop and design-panel handle their external refs correctly (explicit optional + bundled fallback) — copy that pattern. Document the convention in docs/ecosystem-map.md §4 (already added) and hedge each redirect.
- **Suggested owner:** implementer
- **Verification command:** `grep -nE "external|optional|or just" development/loop-engineer/SKILL.md development/optimization-loop/SKILL.md development/unit-test-quality/SKILL.md systems-design/design-system/SKILL.md`

### F-6 -- loop-scaffold entrypoint paths are placeholdered/ambiguous in dependent loops
- **Source:** ecosystem-audit-1 (reference-integrity lens)
- **Priority:** Low
- **Risk:** low
- **Evidence:** `development/optimization-loop/SKILL.md:179` invokes `python <loop-engineer>/scripts/scaffold-loop.py ...` (unresolved placeholder); `development/bug-pipeline/SKILL.md:87` names `scaffold-loop.py` as if at repo `scripts/` (it lives at `development/loop-engineer/scripts/scaffold-loop.py`). Replace with the concrete relative path `../loop-engineer/scripts/scaffold-loop.py` (bug-pipeline already offers a "go minimal" fallback).
- **Suggested owner:** implementer
- **Verification command:** `grep -n "scaffold-loop.py" development/optimization-loop/SKILL.md development/bug-pipeline/SKILL.md | grep -v "<loop-engineer>"`

### F-7 -- missing/one-directional handoff wiring across naturally-paired skills
- **Source:** ecosystem-audit-1 (relationships lens; 8 documented missing edges)
- **Priority:** Medium
- **Risk:** low
- **Evidence:** (a) instrument-observability ↔ production-readiness absent both ways (instrument-observability has empty related/handoff arrays) though it produces production-readiness's telemetry input; (b) improve-architecture and dead-code-reaper do not name arch-drift-watch as their upstream detector (arch-drift-watch names them); (c) autonomous-advisor lists review-panel only as "related", not a branch-gate handoff; (d) test-backfill-loop's suspected-bug escalation never names the canonical `agent-state/BUG_TRACKER.md` sink; (e) design-panel→autonomous-advisor handoff omits the spec→PRP transition (autonomous-advisor rejects "no PRP"); (f) plan-prune does not reciprocally name sprint-ticket-runner; (g) design-system cites clean-room by bare name with no link. docs/ecosystem-map.md §2 now documents the intended edges — wire the SKILL.md bodies to match.
- **Suggested owner:** implementer
- **Verification command:** `grep -l "production-readiness" development/instrument-observability/SKILL.md && grep -l "arch-drift-watch" development/improve-architecture/SKILL.md development/dead-code-reaper/SKILL.md`

### F-8 -- test-backfill-loop suspected-bug escalation has no concrete sink
- **Source:** ecosystem-audit-1 (relationships + map: test-backfill-loop)
- **Priority:** Medium
- **Risk:** low
- **Evidence:** `development/test-backfill-loop/SKILL.md:32` "it's a **defect to file** (to a tracker, or hand it to diagnose-loop)" and `references/backfill-kit.md` writer marks `blocked-suspected-bug` — but neither names `agent-state/BUG_TRACKER.md` or defines who routes the entry onward. Blocked entries pile up with nothing downstream consuming them. Name BUG_TRACKER.md as the canonical sink and state the route.
- **Suggested owner:** implementer
- **Verification command:** `grep -n "BUG_TRACKER" development/test-backfill-loop/SKILL.md development/test-backfill-loop/references/backfill-kit.md`

### F-9 -- bug-pipeline worked example uses bare `hunter/fixer/validator` names alongside install-directed `bug-pipeline-*` roles
- **Source:** ecosystem-audit-1 (reference-integrity lens)
- **Priority:** Low
- **Risk:** low
- **Evidence:** `development/bug-pipeline/SKILL.md:170` directs installing `bug-pipeline-hunter/-fixer/-validator`, while the inline templates and dogfooded example use bare `.claude/agents/hunter.md` etc. Both exist; the ambiguity is which is canonical. State that the bare names are the jar's legacy dogfooded instance and the prefixed manifest roles are the canonical installable artifacts. (Mirrors the now-fixed kit-name drift in dead-code-reaper/test-backfill-loop/arch-drift-watch.)
- **Suggested owner:** implementer
- **Verification command:** `grep -n "legacy\|illustrative\|canonical" development/bug-pipeline/SKILL.md`

### F-10 -- plan-prune can permanently delete UNCOMMITTED planning docs (relies on "git history is the archive" without checking it)
- **Source:** ecosystem-audit-1 (map: plan-prune, fresh-agent-unsafe)
- **Priority:** Medium
- **Risk:** medium
- **Evidence:** `development/plan-prune/SKILL.md:115` "delete it after its useful claims are represented ... Git history is the archive." Preflight only checks tree dirtiness; nothing requires the doc being deleted to be committed first. A fresh agent could delete an untracked/dirty planning doc, losing content git never held. Add a precondition: never delete a planning doc unless it is committed clean; archive/block untracked or dirty ones instead.
- **Suggested owner:** implementer (then verifier)
- **Verification command:** `grep -in "committed\|untracked\|git ls-files" development/plan-prune/SKILL.md`

### F-11 -- SKILL.md install pointers send agents to `../agents/README.md`, which does not list the named roles
- **Source:** ecosystem-audit-1 (reference-integrity + documentation lenses)
- **Priority:** Low
- **Risk:** low
- **Evidence:** dead-code-reaper, diagnose-loop, review-panel, improve-architecture, production-readiness (and others) say "Copy-ready generated agents live in ../agents/README.md" then name roles, but `development/agents/README.md` documents only test-backfill-loop and review-panel examples and otherwise defers to manifest.json; `systems-design/agents/README.md` names none. Roles DO exist in manifest.json and the generated `claude/`/`codex/` files. Fix: point install lines at `../agents/manifest.json` and `../agents/<host>/<role>` directly, OR list the role names in the README.
- **Suggested owner:** implementer
- **Verification command:** `python -c "import json; n=set(r['name'] for r in json.load(open('development/agents/manifest.json'))['agents']); t=open('development/agents/README.md').read(); print(sum(x in t for x in n),'of',len(n))"`

### F-12 -- autonomous-advisor "Confirming the Loop Is Running" list double-numbers item 3
- **Source:** ecosystem-audit-1 (map: autonomous-advisor)
- **Priority:** Low
- **Risk:** low
- **Evidence:** `development/autonomous-advisor/SKILL.md:471` "3. The loop is self-sustaining." and `:478` "3. Loop termination." — the second should be 4. Muddies a step-by-step procedure.
- **Suggested owner:** implementer
- **Verification command:** `grep -nE "^[0-9]+\. " development/autonomous-advisor/SKILL.md`
