# Triage Inbox -- jar-audit

> Discovery appends findings here; planning promotes one into loop-state.md Open
> Tasks. One finding = one heading block (NOT a table). Every finding needs a
> runnable Verification command. Enrich from references/state-templates.md.

## Findings

> Source for all F-* below: ecosystem-audit-1 (deep evidence-backed audit of all
> 23 skills, 2026-06-12). The structural gate is GREEN; these are defects the
> gate cannot see. RESOLVED by jar-audit-eco-1 (see completed.md): F-1, F-2, F-3,
> F-8, F-10, F-12 and the instrument-observability->production-readiness /
> arch-drift-watch reciprocity edges of F-7. The blocks below are the remaining
> open findings.

### F-4 -- add-to-jar has no "NOT for" boundary
- **Source:** ecosystem-audit-1 (map: add-to-jar)
- **Priority:** Low
- **Risk:** low
- **Evidence:** `development/add-to-jar/SKILL.md` has a clear trigger but no negative boundary (e.g. NOT for authoring a skill from scratch — that is skill-forge — or bulk-importing many skills in one pass). Changing the description requires `python scripts/gen-index.py` to re-sync skills.json.
- **Suggested owner:** implementer
- **Verification command:** `grep -iE "not for|when not to use" development/add-to-jar/SKILL.md && python scripts/audit-jar.py --quiet`

### F-5 -- external-skill redirects (`bugfix`, `tdd`, `to-issues`, `triage`, `writing-plans`) are named without an external/optional marker or fallback
- **Source:** ecosystem-audit-1 (reference-integrity lens)
- **Priority:** Medium
- **Risk:** low
- **Evidence:** loop-engineer (desc + `:66` "use **bugfix**"), optimization-loop (`:61` + desc), improve-architecture (handoffs `to-issues`/`triage`/`tdd`), unit-test-quality (`:32` "use TDD"), design-system (`:79` "feeds **writing-plans**"). None marks these as external/global skills absent from a jar-only checkout, and none gives a plain fallback. diagnose-loop and design-panel handle their external refs correctly (explicit optional + bundled fallback) — copy that pattern. Convention documented in docs/ecosystem-map.md §4.
- **Suggested owner:** implementer
- **Verification command:** `grep -nE "external|optional|or just" development/loop-engineer/SKILL.md development/optimization-loop/SKILL.md development/unit-test-quality/SKILL.md systems-design/design-system/SKILL.md`

### F-6 -- loop-scaffold entrypoint paths are placeholdered/ambiguous in dependent loops
- **Source:** ecosystem-audit-1 (reference-integrity lens)
- **Priority:** Low
- **Risk:** low
- **Evidence:** `development/optimization-loop/SKILL.md:179` invokes `python <loop-engineer>/scripts/scaffold-loop.py ...` (unresolved placeholder); `development/bug-pipeline/SKILL.md:87` names `scaffold-loop.py` as if at repo `scripts/` (it lives at `development/loop-engineer/scripts/scaffold-loop.py`). Replace with the concrete relative path `../loop-engineer/scripts/scaffold-loop.py` (bug-pipeline already offers a "go minimal" fallback).
- **Suggested owner:** implementer
- **Verification command:** `grep -n "scaffold-loop.py" development/optimization-loop/SKILL.md development/bug-pipeline/SKILL.md | grep -v "<loop-engineer>"`

### F-7 -- remaining missing/one-directional handoffs (partial; arch-drift + instrument edges resolved by jar-audit-eco-1)
- **Source:** ecosystem-audit-1 (relationships lens)
- **Priority:** Medium
- **Risk:** low
- **Evidence:** Still open: (a) autonomous-advisor lists review-panel only as "related", not a branch-gate handoff (its Branch gate = PR URL/merge SHA is the canonical consumer of an adversarial pre-merge review); (b) design-panel hands off to autonomous-advisor but omits the spec->PRP transition (autonomous-advisor rejects "no PRP"); (c) plan-prune does not reciprocally name sprint-ticket-runner ("to EXECUTE a reconciled plan, use sprint-ticket-runner"); (d) design-system cites clean-room by bare name with no link. docs/ecosystem-map.md §2 documents the intended edges.
- **Suggested owner:** implementer
- **Verification command:** `grep -n "review-panel" development/autonomous-advisor/SKILL.md && grep -n "clean-room" systems-design/design-system/SKILL.md`

### F-9 -- bug-pipeline worked example uses bare `hunter/fixer/validator` names alongside install-directed `bug-pipeline-*` roles
- **Source:** ecosystem-audit-1 (reference-integrity lens)
- **Priority:** Low
- **Risk:** low
- **Evidence:** `development/bug-pipeline/SKILL.md:170` directs installing `bug-pipeline-hunter/-fixer/-validator`, while the inline templates and dogfooded example use bare `.claude/agents/hunter.md` etc. Both exist; the ambiguity is which is canonical. State that the bare names are the jar's legacy dogfooded instance and the prefixed manifest roles are the canonical installable artifacts. (Mirrors the now-fixed kit-name drift in dead-code-reaper/test-backfill-loop/arch-drift-watch.)
- **Suggested owner:** implementer
- **Verification command:** `grep -n "legacy\|illustrative\|canonical" development/bug-pipeline/SKILL.md`

### F-11 -- SKILL.md install pointers send agents to `../agents/README.md`, which does not list the named roles
- **Source:** ecosystem-audit-1 (reference-integrity + documentation lenses)
- **Priority:** Low
- **Risk:** low
- **Evidence:** dead-code-reaper, diagnose-loop, review-panel, improve-architecture, production-readiness (and others) say "Copy-ready generated agents live in ../agents/README.md" then name roles, but `development/agents/README.md` documents only test-backfill-loop and review-panel examples and otherwise defers to manifest.json; `systems-design/agents/README.md` names none. Roles DO exist in manifest.json and the generated `claude/`/`codex/` files. Fix: point install lines at `../agents/manifest.json` and `../agents/<host>/<role>` directly, OR list the role names in the README (see decisions HD: a gate is borderline — prefer the content fix).
- **Suggested owner:** implementer
- **Verification command:** `python -c "import json; n=set(r['name'] for r in json.load(open('development/agents/manifest.json'))['agents']); t=open('development/agents/README.md').read(); print(sum(x in t for x in n),'of',len(n))"`
