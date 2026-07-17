# Decisions -- jar-audit

> Choices made and their rationale (the file-based fallback for what MemBerry
> would otherwise remember). Enrich from references/state-templates.md.

| Decision | Rationale | Cycle |
|----------|-----------|-------|
| Hook declarations live in role files and generated agent packs | Keeps hook behavior attached to the agent roles that produce evidence while `skill-forge` remains the only path that edits skills | hook-runtime-drop-in |
| Durable ecosystem knowledge goes in `docs/ecosystem-map.md`; the audit narrative is delivered in-response, not as a repo file | Avoids a point-in-time report rotting in the tree (the jar's own plan-prune philosophy). Edges between skills are the durable part; findings live in triage-inbox/decisions | ecosystem-audit-1 |
| Did NOT implement the proposed new audit gates this cycle | Audit-policy changes need separate review (maker != checker) and a careful false-positive assessment; proposed below with evidence + risk for human sign-off | ecosystem-audit-1 |
| Aligned bundled `references/*-kit.md` template `name:` to the manifest/install names | The agents/README "Naming" section already mandates skill-prefixed role names to avoid `scout`/`validator` collisions; the kits violated the repo's own stated policy. Names inside fenced blocks are invisible to the gate, so this was a real, gate-undetectable drift | ecosystem-audit-1 |
| Implemented the HD-1 + HD-2 audit gates (with maker != checker review) | These are the two narrow, additive checks ecosystem-audit-1 recommended APPROVE and deferred only for separate review + a false-positive assessment. This human-directed pass supplied both: an independent validator (stronger model) verified the audit-policy change PASS, and the false-positive risk was assessed (role-name/marker regexes are slug/word-bounded, scoped to installable skills and `*-kit.md`, with a `# example-only` hatch). Both ship green (239 checks) and permanently close gate-invisible drift classes. HD-4's broad noise-prone lints stay rejected. | jar-quality-pass |

## Human-Decision Items (pending)

> Audit-policy / public-contract questions surfaced by ecosystem-audit-1. Each
> needs a human yes before a maker acts. Do NOT silently change audit policy.

### HD-1 -- Add a gate: bundled kit template `name:` must resolve to a manifest role
- **Evidence:** Before this cycle, `reaper-kit.md`/`backfill-kit.md`/`drift-kit.md` shipped templates whose `name:` diverged from the manifest/install names. The audit gate strips fenced code blocks (`strip_code`) and only name-checks `references/role-skills/*.SKILL.md`, so embedded kit names are 100% invisible to it. The drift was fixed by hand this cycle but nothing prevents regression.
- **Proposed check:** parse `name:` from fenced ```md/```yaml frontmatter in `*/*/references/*-kit.md`; assert each is a real role in the sibling `agents/manifest.json` OR carries an explicit `# example-only` marker.
- **Risk:** moderate maintenance (a mini fenced-block parser + a whitelist for intentionally-generic examples). Net: closes a real, gate-undetectable drift class affecting 3+ skills at bounded cost.
- **Recommendation:** APPROVE as a narrow, additive check (does not weaken any existing gate).
- **Status:** IMPLEMENTED (jar-quality-pass) — `check_kit_role_names` in `scripts/audit-jar.py`, covered by `tests/test_audit_boundaries.py`. Scans `*/*/references/*-kit.md`; `# example-only` opts a file out.

### HD-2 -- Add a gate: every installable skill must carry a "NOT for" boundary
- **Evidence:** Exactly 2 of 23 skills (add-to-jar, instrument-observability) have no negative boundary; instrument-observability's empty boundary creates a real routing collision (F-3). All 21 others carry one.
- **Proposed check:** assert each `*/*/SKILL.md` contains a case-insensitive `not for` / `when not to use` marker.
- **Risk:** low (2 current violators, stable phrasing). The DEEPER check — that each NOT-for redirect resolves to a real jar skill or a hedged external one — is NOT recommended for automation: external redirects (`bugfix`/`tdd`/`writing-plans`) are legitimate and distinguishing "hedged-optional" from "dangling" needs judgment.
- **Recommendation:** APPROVE the marker-presence subset only; keep redirect-resolution a human review item.
- **Status:** IMPLEMENTED (jar-quality-pass) — `check_not_for_boundaries` in `scripts/audit-jar.py` (marker-presence only, word-bounded regex; redirect-resolution deliberately NOT automated), covered by `tests/test_audit_boundaries.py`.

### HD-3 -- Add a gate: maturity vs. evidence consistency
- **Evidence:** The gate verifies `evidence:` paths EXIST but not that they hold real proof. `bug-pipeline` declares `maturity: dogfooded` against `proof/bug-pipeline/README.md` which still says "No completed public proof packet has been added yet." `skill-forge` is honest (`maturity: dry-run` + empty packet).
- **Proposed check:** if maturity is in {dogfooded, external-tested, battle-tested}, assert the evidence file does NOT contain the placeholder sentinel line.
- **Risk:** low/medium — sentinel string is a brittle magic constant; gating only top tiers is a judgment boundary.
- **Recommendation:** Either APPROVE the top-tier sentinel check, OR (lower effort) downgrade bug-pipeline to `maturity: linted` until a real packet lands. Pick one.

### HD-4 -- Do NOT add the broad "automation without a stop condition" or "redirect resolves to a real skill" lints
- **Evidence:** Both are valuable in concept but judgment-heavy and noise-prone: a keyword lint would mis-flag detection-only / by-design-autonomous skills; redirect-resolution can't mechanically tell a hedged external skill from a dangling one.
- **Recommendation:** REJECT for CI. Keep only the mechanical subsets (HD-2 marker presence; and the already-applied launch-gate fix for sprint-ticket-runner). A high false-positive rate would erode trust in the GREEN signal — the opposite of the goal.

### HD-5 -- MemBerry / `memberry-setup` contract: optional adapter, jar-wide
- **Evidence:** autonomous-advisor (F-1) and clean-room (F-2) present an unbundled user-global skill as a hard prerequisite/halt, contradicting optimization-loop's "OPTIONAL adapter" posture and the user's recorded "jar skills self-contained" rule.
- **Recommendation:** APPROVE the stance "MemBerry is an optional persistence adapter; absence is a clean skip" jar-wide, and let F-1/F-2 fixers reframe the two skills to match. Documented in docs/ecosystem-map.md §4.

### D-2026-07-16 -- rebuild-panel ships as an analysis panel only; campaign mode cut
- **Context:** The user asked for a "skill loop" for first-principles refactor/improvement analysis ("if we were rebuilding the orchestrator from first principles... what would you recommend?") and initially picked panel + optional campaign mode.
- **Evidence:** The redundancy skeptic found campaign mode (a panel-owned ledger tracking a strangler sequence phase-by-phase) duplicates three skills: sprint-ticket-runner (sequenced board), plan-prune (post-ship reconciliation), and arch-drift-watch (finding router). It also collides with the ecosystem-map section 6 no-cross-file discipline.
- **Decision (human):** Cut campaign mode. The iterate-after-a-phase behavior is "re-run the panel scoped to the changed area" -- zero new machinery. Execution state belongs to the executors.
- **Also binding:** a full-rewrite verdict routes to clean-room and STOPS (the panel never writes a rewrite DESIGN_DOC/PRP -- that is clean-room Transparent Phase 1-2); improve-architecture receives deepening candidates ONE at a time per its own contract.
