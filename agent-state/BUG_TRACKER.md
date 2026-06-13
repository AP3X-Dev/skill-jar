# BUG_TRACKER.md -- skill-jar bug pipeline

## Meta

| Field | Value |
|---|---|
| Last Hunter Scan | 2026-06-12T00:00:00Z |
| Last Fixer Pass | 2026-06-12T00:00:00Z |
| Last Validator Pass | 2026-06-12T00:00:00Z |
| Total Found | 1 |
| Total Pending | 0 |
| Total In Progress | 0 |
| Total Fixed | 0 |
| Total In Validation | 0 |
| Total Verified | 1 |
| Total Reopened | 0 |
| Total Blocked | 0 |

---

## Sweep Notes

**Sweep 2 — 2026-06-12T00:00:00Z**
Focus: 8 edited skills (instrument-observability, autonomous-advisor, clean-room, dead-code-reaper, improve-architecture, plan-prune, test-backfill-loop, sprint-ticket-runner); 3 edited kits (reaper-kit.md, backfill-kit.md, drift-kit.md); loop-architecture.md; docs/ecosystem-map.md; cross-file consistency against development/agents/manifest.json and systems-design/agents/manifest.json.

1 finding filed (BUG-001). Verified clean:
- Kit template `name:` fields in all three kits match manifest role names exactly (dead-code-reaper-scout/-reaper/-validator, test-backfill-scout/-writer/-verifier, arch-drift-watcher).
- Ecosystem-map §5 installable roles column is consistent with manifest for all checked rows.
- All `references/` links in instrument-observability (investigation-model.md, instrumentation-playbook.md, sentry-patterns.md) resolve.
- MemBerry is correctly marked optional (clean skip) in both autonomous-advisor:57 and clean-room:262.
- plan-prune delete precondition (committed-clean only) is in place at SKILL.md:51.
- sprint-ticket-runner Operating Contract carries the launch gate and stop condition.
- loop-architecture.md companion links (state-templates.md, subagent-templates.md, automation-templates.md, safety-and-gates.md, worktree-isolation.md, role-skills/) and cross-skill link to optimization-loop all resolve.
- Defect: ecosystem-map:139 MemBerry row retains stale "see open findings" pointer for autonomous-advisor & clean-room after F-1/F-2/F-12 were closed by jar-audit-eco-1 (filed as BUG-001).

**Sweep 1 — 2026-06-09T18:30:00Z**
Focus: `scripts/audit-jar.py` logic bugs, `loop-engineering/scripts/scaffold-loop.py` logic bugs, cross-file consistency (`agent-state/loop-state.md`, `docs/prompts/jar-audit-driver.md`, `docs/prompts/bug-pipeline-driver.md`, `AGENTS.md`).

No findings above the bar. All code paths traced and verified correct:
- `skill_files()` path-parts filter correctly indexes `f.parts[len(ROOT.parts)]` for the immediate child of ROOT on both Unix and Windows.
- `check_links()` `inside` guard correctly handles parent traversal, root-resolving links, and path-traversal attacks.
- Idempotency regex `Summary: (\d+) created` matches scaffold-loop.py's output format; string comparison `== '0'` is correct.
- `scaffold-loop.py` correctly handles all `--host` values and builds no orphaned state.
- All `.claude/agents/` files referenced in driver prompts (`hunter.md`, `fixer.md`, `validator.md`) exist.
- Cross-file path references consistent across `AGENTS.md`, `loop-state.md`, `jar-audit-driver.md`, and `bug-pipeline-driver.md`.
- Audit gate runs clean: 27 checks, 0 failed.

---

## BUG-001 — Ecosystem-map §4 MemBerry row says "see open findings" after F-1/F-2/F-12 were closed

| Field | Value |
|---|---|
| ID | BUG-001 |
| Status | verified |
| Severity | low |
| File | docs/ecosystem-map.md:139 |
| Filed by | hunter sweep 2026-06-12 |

**Title:** Ecosystem-map §4 MemBerry dependency row still reads "should be optional — see open findings" for autonomous-advisor & clean-room after the open findings (F-1, F-2, F-12) were closed by jar-audit-eco-1.

**Evidence:** `docs/ecosystem-map.md:139`
```
| MemBerry + `memberry-setup` | ... | optimization-loop (optional), autonomous-advisor & clean-room (should be optional — see open findings) | optional persistence adapter; absent = files-only |
```
`agent-state/triage-inbox.md:11` confirms F-1, F-2, F-12 were "RESOLVED by jar-audit-eco-1". Both `autonomous-advisor/SKILL.md:57` and `clean-room/SKILL.md:262` now say MemBerry is an optional adapter with a clean skip on absence — the "should be optional" concern and the "see open findings" pointer are both obsolete.

**Observable symptom:** A fresh agent reading §4 of the ecosystem-map will see "see open findings" and search the triage-inbox for an actionable open finding about MemBerry optionality in these two skills. No such finding exists (the inbox header explicitly marks them resolved), causing confusion, wasted investigation, or a spurious "fix" attempt that re-edits correctly-implemented code.

**Repro:** Read `docs/ecosystem-map.md:139`; then read `agent-state/triage-inbox.md` header (lines 9–14) — the cross-reference resolves to an already-closed item.

**Fix scope:** Change the "Used by" cell for MemBerry from `autonomous-advisor & clean-room (should be optional — see open findings)` to `autonomous-advisor & clean-room (optional)` — matching the already-implemented posture.

**Fixer (jar-audit-eco-1, 2026-06-12):** Edited `docs/ecosystem-map.md:139` — the MemBerry "Used by" cell now reads `optimization-loop, autonomous-advisor, clean-room (all optional)`; the stale "see open findings" pointer is removed. Smallest diff (one table cell). `python scripts/audit-jar.py` -> 208 checks, 0 failed (ecosystem-map links still resolve). Status -> fixed; awaiting independent validator.

**Validator (independent, 2026-06-12):** VERIFIED. ecosystem-map.md:139 no longer contains "see open findings" or "should be optional"; cell now reads `optimization-loop, autonomous-advisor, clean-room (all optional)`. Implemented posture confirmed optional/clean-skip in autonomous-advisor/SKILL.md:57 ("optional persistence adapter, not a prerequisite ... clean skip, never a halt") and clean-room/SKILL.md:262 ("optional persistence adapter — its absence is a clean skip, not a blocker"). Grep of whole ecosystem-map for stale pointers: only :70 (unrelated prose) and :141 (references F-5, still OPEN in triage-inbox — correctly not stale). `python scripts/audit-jar.py` -> `Summary: 208 checks, 0 failed.` (exit 0). `git diff --stat` -> only docs/ecosystem-map.md (1 row) + agent-state/BUG_TRACKER.md; diff is one table cell, not a rewrite. F-1/F-2/F-12 confirmed closed (triage-inbox header lines 11-14; completed.md C-2026-06-12-T-ECO-2). Status -> verified.

<!-- HUNTER: Append new bugs above this line -->
