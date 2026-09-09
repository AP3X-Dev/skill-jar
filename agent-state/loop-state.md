# Loop State -- skill-jar

> The REQUIRED restart spine. A restarted loop-agent reads THIS file to learn
> what is done, what verifies the work, and what to do next. Keep host-neutral.
>
> Autonomy level: 2 (isolated implementation) -- the maker fixes one item per
> cycle, the checker gates it, a human reviews diffs before push. Raise to
> Level 3+ only after several cycles where the checker's verdicts matched the
> human's review and no diff went out of scope.

## Current Objective

Keep the skill jar publish-ready via three loops, one task per cycle each:

- **jar-audit** -- fix structural failures surfaced by the audit gate
  (frontmatter, triggers, naming, links, script compile + idempotency).
  Driver: `docs/prompts/jar-audit-driver.md`.
- **bug-pipeline** -- hunt, fix, and validate content/script defects via
  `agent-state/BUG_TRACKER.md` (Hunter -> Fixer -> Validator).
  Driver: `docs/prompts/bug-pipeline-driver.md`.
- **skill-forge** -- pressure-test and harden every jar skill via
  `agent-state/SKILL_FORGE_TRACKER.md`, one skill-stage per cycle.
  Driver: `docs/prompts/skill-forge-driver.md`.

## Verification Commands

- `python scripts/audit-jar.py` (THE gate -- exits 0/1; covers frontmatter,
  trigger phrases, skill naming, relative-link resolution, .py compile, and
  scaffold-loop.py idempotency)

## Open Tasks

> ecosystem-audit-1 promoted T-ECO-1..4 here; jar-audit-eco-1 closed all four
> (see Completed Tasks below). Remaining findings F-4..F-11 stay in
> `agent-state/triage-inbox.md` until a future cycle promotes one. One task per
> cycle, maker then a separate checker.

| ID | Task | Owner | Status | Files | Acceptance (exits 0) |
|----|------|-------|--------|-------|----------------------|

## Completed Tasks

| ID | Task | Cycle | Commit | Result |
|----|------|-------|--------|--------|
| C-2026-09-09-SF-034-FORGED | Add and forge decision-evidence-ledger | decision-evidence-ledger | not committed | Original read-only-by-default implementation; RED captured; current-revision scenario judges passed 5/5, 5/5, and 5/5; behavioral acceptance passed 11/11; write safety passed 5/5; contamination, quick validation, 91 tests, and the 324-check audit passed. No push performed. |
| C-2026-09-08-SF-033-FORGED | Add and forge verification-evidence-plan | verification-evidence-plan | not committed | Original read-only implementation; RED captured; current-revision scenario judges passed 7/7, 6/6, and 6/6; behavioral acceptance passed 11/11; adversarial planning passed 5/5; contamination, quick validation, 91 tests, and the 319-check audit passed. No push performed. |
| C-2026-09-08-SF-032-FORGED | Add and forge change-impact-proof | change-impact-proof | this commit | Original clean-room implementation; RED captured; 3/3 executable judges COMPLY; 11/11 behavioral acceptance; attribution scan clean; 91 tests and 321-check audit passed. |
| C-2026-06-12-SF-QUEUE | Forge remaining 17 skills (SF-006..022, SF-021) | skill-forge-queue | this commit | Concurrent RED->GREEN->judge x3 per skill (85 agents, forger != judge); 17/17 forged 3/3; gate 208; run packages written; tracker de-fragmented. Forge queue now 23/23. |
| C-2026-06-12-SF-005-FORGED | Forge clean-room (SF-005) | skill-forge-batch1 | this commit | 3/3 independent judges COMPLY on the firewall/parity scenario; SF-005 -> forged. |
| C-2026-06-12-SF-023-GREEN-FORGED | GREEN + forge instrument-observability (SF-023) | skill-forge-batch1 | this commit | Forger closed the captured RED rationalizations (45/+2- diff, description unchanged); 3/3 independent judges COMPLY (forger != judge); SF-023 -> forged. |
| C-2026-06-12-T-ECO-1 | instrument-observability NOT-for + production-readiness handoff (F-3) | jar-audit-eco-1 | this commit | Added a "When NOT to use" boundary (diagnose-loop / optimization-loop / host bugfix) + description NOT-for clause (900 chars) + a handoff sentence to production-readiness. Maker + independent checker PASS. |
| C-2026-06-12-T-ECO-2 | MemBerry reframed optional in autonomous-advisor + clean-room (F-1, F-2, F-12; HD-5) | jar-audit-eco-1 | this commit | Removed the "surface the error and halt" mandatory framing; MemBerry/memberry-setup is now an optional adapter (clean skip on absence), consistent across both skills; fixed duplicate list numbering. Checker rejected one inaccurate "FUGAZI above" cross-ref; reworded and re-verified PASS. |
| C-2026-06-12-T-ECO-3 | Reciprocal handoffs: arch-drift-watch upstream + BUG_TRACKER.md sink (F-7 partial, F-8) | jar-audit-eco-1 | this commit | improve-architecture and dead-code-reaper now name arch-drift-watch as upstream detector; test-backfill-loop names agent-state/BUG_TRACKER.md as the suspected-bug sink. Maker + independent checker PASS. |
| C-2026-06-12-T-ECO-4 | plan-prune delete precondition: committed-clean only (F-10) | jar-audit-eco-1 | this commit | Delete allowed only when git already holds the doc (tracked + committed clean); untracked/dirty docs are archived or blocked. Maker + independent checker PASS. |
| C-2026-06-12-ECO-MAP | Add docs/ecosystem-map.md | ecosystem-audit-1 | this commit | Edges-between-skills map: routing table, two pipeline backbones, autonomy ladder + human gate, dependency matrix, 23-skill relationship table, state-files map, gates note. |
| C-2026-06-12-ECO-KIT-NAMES | Align bundled kit template names with manifest roles | ecosystem-audit-1 | this commit | Renamed fenced `name:` in reaper/backfill/drift kits to dead-code-reaper-*/test-backfill-*/arch-drift-watcher; closes gate-invisible drift; independent checker verified. |
| C-2026-06-12-ECO-SPRINT-GATE | Add launch gate + stop condition to sprint-ticket-runner | ecosystem-audit-1 | this commit | The lone auto-launch/no-stop loop skill now offers launch and defines a stop condition; aligns with the "ask before launching loops" rule; independent checker verified. |
| C-2026-06-12-ECO-LINK | Normalize loop-architecture state-templates link | ecosystem-audit-1 | this commit | `../references/state-templates.md` -> `./state-templates.md` (same target, already gate-green); removes the inconsistency one audit lens mis-read as a break. |
| C-2026-06-10-SF-001-RED | Capture RED pressure evidence for `arch-drift-watch` | skill-forge-1 | this commit | RED surfaced six concrete rationalizations: ad hoc `rg` scanning instead of FUGAZI, inferred zones, silent baseline reset, immediate auto-fix, audit-gate overconfidence, and loose triage routing. |
| C-2026-06-10-SF-001-GREEN | Patch `arch-drift-watch` for captured RED rationalizations | skill-forge-2 | this commit | GREEN tightened `development/arch-drift-watch/SKILL.md` against ad hoc scanning, inferred zones, silent baseline resets, detection-cycle fixes, audit-green overconfidence, and vague triage routing. |
| C-2026-06-10-SF-001-REF1 | Judge `arch-drift-watch` pressure pass 1 | skill-forge-3 | this commit | Independent judge returned COMPLY and counted clean run 1/3 for the captured pressure scenario. |
| C-2026-06-10-SF-001-REF2 | Judge `arch-drift-watch` pressure pass 2 | skill-forge-4 | this commit | Independent judge returned COMPLY and counted clean run 2/3, with residual risk noted around "equivalent structural analyzer" judgment. |
| C-2026-06-10-SF-001-FORGED | Forge `arch-drift-watch` | skill-forge-5 | this commit | Third independent judge returned COMPLY, final lint passed, and SF-001 advanced to `forged` with 3/3 clean runs. |
| C-2026-06-10-SF-002-RED | Capture RED pressure evidence for `auto-research` | skill-forge-6 | this commit | RED surfaced eight rationalizations around starting experiments before one scalar metric, frozen harness, fixed budget, repeated baseline, immutable scoring, append-only ledger, and explicit launch approval. |
| C-2026-06-10-SF-002-GREEN | Patch `auto-research` for captured RED rationalizations | skill-forge-7 | this commit | GREEN added a pressure-rationalization table that closes deadline, weak-signal, multi-metric, baseline, budget, mutable-harness, auto-launch, and ledger-reconstruction dodges. |
| C-2026-06-10-SF-002-REF1 | Judge `auto-research` pressure pass 1 | skill-forge-8 | this commit | Independent judge returned COMPLY and counted clean run 1/3 for the captured pressure scenario. |
| C-2026-06-10-SF-002-REF2-LOOPHOLE | Judge `auto-research` pressure pass 2 | skill-forge-9 | this commit | Independent judge found a loophole in the second-baseline exception and reset SF-002 to `red-captured` with 0/3 clean runs. |
| C-2026-06-10-SF-002-GREEN2 | Patch `auto-research` second-baseline waiver | skill-forge-10 | this commit | GREEN tightened the second-baseline waiver so it requires concrete time/cost/quota justification plus explicit human consent before launch may proceed. |
| C-2026-06-10-SF-002-REF1B | Judge `auto-research` pressure pass 1 after waiver patch | skill-forge-11 | this commit | Independent judge returned COMPLY and counted clean run 1/3 after the baseline-waiver patch. |
| C-2026-06-10-SF-002-REF2B | Judge `auto-research` pressure pass 2 after waiver patch | skill-forge-12 | this commit | Independent judge returned COMPLY and counted clean run 2/3 after the baseline-waiver patch. |
| C-2026-06-10-SF-002-FORGED | Forge `auto-research` | skill-forge-13 | this commit | Third post-waiver judge returned COMPLY, final lint passed, and SF-002 advanced to `forged` with 3/3 clean runs. |
| C-2026-06-10-SF-003-RED | Capture RED pressure evidence for `autonomous-advisor` | skill-forge-14 | this commit | RED surfaced eight rationalizations around missing PRPs, skipped phase gates, missing run state, self-review, weak tests, direct main push, production deploy, and unattended optimization. |
| C-2026-06-10-SF-003-GREEN | Patch `autonomous-advisor` for captured RED rationalizations | skill-forge-15 | this commit | GREEN added hard stops and tightened gates for PRP validation, run state, verifier separation, PRP-tied tests, release checkpoints, and optimization governance. |
| C-2026-06-10-SF-003-REF1 | Judge `autonomous-advisor` pressure pass 1 | skill-forge-16 | this commit | Independent judge returned COMPLY and counted clean run 1/3 for the captured pressure scenario. |
| C-2026-06-10-SF-003-REF2 | Judge `autonomous-advisor` pressure pass 2 | skill-forge-17 | this commit | Independent judge returned COMPLY and counted clean run 2/3, including the zero-human-input release/deploy abuse angle. |
| C-2026-06-10-SF-003-FORGED | Forge `autonomous-advisor` | skill-forge-18 | this commit | Third independent judge returned COMPLY, final lint passed, and SF-003 advanced to `forged` with 3/3 clean runs. |
| C-2026-06-10-SF-004-RED | Capture RED pressure evidence for `bug-pipeline` | skill-forge-19 | this commit | RED surfaced seven rationalizations around weak/static evidence, style-smell bugs, fixer self-verification, skipped validator, batched fixes, gate weakening, and deleting reopened bugs. |
| C-2026-06-10-SF-004-GREEN | Patch `bug-pipeline` for captured RED rationalizations | skill-forge-20 | this commit | GREEN added refusal rules and role-template reinforcements for evidence quality, maker-checker separation, one bug per cycle, gate integrity, and reopened bug durability. |
| C-2026-06-10-SF-004-REF1 | Judge `bug-pipeline` pressure pass 1 | skill-forge-21 | this commit | Independent judge returned COMPLY and counted clean run 1/3 for the captured hunter/fixer/validator shortcut scenario. |
| C-2026-06-10-SF-004-REF2 | Judge `bug-pipeline` pressure pass 2 | skill-forge-22 | this commit | Independent judge returned COMPLY and counted clean run 2/3 for the captured hunter/fixer/validator shortcut scenario. |
| C-2026-06-10-SF-004-FORGED | Forge `bug-pipeline` | skill-forge-23 | this commit | Third independent judge returned COMPLY, final lint passed, and SF-004 advanced to `forged` with 3/3 clean runs. |
| C-2026-06-10-SF-005-RED | Capture RED pressure evidence for `clean-room` | skill-forge-24 | this commit | RED surfaced eight rationalizations around internal/time-boxed ownership, side-by-side parity copying, implementer peeking, eyeballed gaps, skipped mode lock, helper source snippets, deferred contamination scans, and compare-port-test cleanup. |
| C-2026-06-10-SF-005-GREEN | Patch `clean-room` for captured RED rationalizations | skill-forge-25 | this commit | GREEN added pressure-rationalization rules and tightened mode lock, Phase 3 firewall, research leakage, inventory grounding, contamination scan timing, and red flags. |
| C-2026-06-11-UNIT-TEST-QUALITY | Add unit-test-quality skill from research report | report-derived-skills-1 | this commit | Added `development/unit-test-quality` with a lean SKILL.md, report-derived reference playbook, generated index/plugin updates, and a pending Skillforge tracker row. |
| C-2026-06-11-UNIT-TEST-SLOP-GATE | Tighten unit-test-quality around real tests and AI slop rejection | report-derived-skills-2 | this commit | Reframed `development/unit-test-quality` around building useful unit tests, auditing existing suites, and rejecting AI-generated tests that only execute code, assert tautologies, or chase coverage. |

## Failed Attempts

| ID | Task | What Failed | Lesson |
|----|------|-------------|--------|

## Current Rules

- The gate is `python scripts/audit-jar.py`; a task is never COMPLETED while it
  exits non-zero.
- CI (`.github/workflows/audit.yml`) runs the same gate on every push/PR --
  jar-audit's discovery is continuous now; cycles fix what CI flags. A red
  badge is an automatic top-priority inbox finding.
- `skills.json` and `.claude-plugin/*.json` are generated/declared wrapper
  artifacts with their own gate checks (index sync, skill-list drift). Adding a
  skill means: create the folder, run `python scripts/gen-index.py`, add the
  path to `.claude-plugin/plugin.json`, and the gate confirms all three agree.
- jar-audit findings live in `triage-inbox.md`; bug-pipeline findings live in
  `BUG_TRACKER.md`. Do not cross-file them.
- skill-forge findings live in `SKILL_FORGE_TRACKER.md`, with evidence packages
  under `agent-state/skill-forge-runs/`. Do not file forge pressure results in
  `triage-inbox.md` or `BUG_TRACKER.md`.
- Fixer never validates its own fix (maker != checker); the validator runs on a
  stronger/different model than the fixer.
- A skill-forge patch must cite a RED rationalization, a known routing/install
  defect, or a concrete user requirement. No taste-only skill rewrites.
- A skill is not `forged` until it has RED evidence, 3/3 clean judge runs, and
  `python scripts/audit-jar.py` exits 0.
- Dropped-in skills are reconciled with `python scripts/sync-jar.py`, which
  updates generated metadata, preserves tracker history, creates missing
  skill-forge rows, and ensures hook evidence state exists.
- Hooks record usage, failure, and improvement candidates only; they do not
  edit `SKILL.md` files directly.
- Generated agent packs inject default usage/failure hooks into every generated
  role, and repo-local loop roles declare their own hook sections.
- Loops commit locally only. Pushing to the remote is the human's call.
- `assets/` and git history are off-limits to all loops.

## Next Run Instructions

jar-audit(1) closed clean: gate green (27 checks, 0 failed), inbox empty, no
task taken. Next jar-audit cycle: run the gate; if green and the inbox is
empty, record another clean cycle and stop. bug-pipeline(1) closed clean:
hunter swept the fresh scripts + cross-file consistency (30+ probes), filed 0
findings, tracker created. Next bug-pipeline cycle: hunter focus rotates to
`development/loop-engineer/references/` content -- verify the reference templates'
instructions/commands are internally consistent and match the drivers; then
fix/validate ONE pending bug if any. skill-forge(1-5) forged SF-001
`arch-drift-watch`; skill-forge(6-13) forged SF-002 `auto-research`; and
skill-forge(14-18) forged SF-003 `autonomous-advisor`. skill-forge(19)
captured RED evidence for SF-004 `bug-pipeline`; skill-forge(20) patched the
target skill for those named rationalizations; skill-forge(21) counted
REFACTOR judge pass 1 clean; skill-forge(22) counted REFACTOR judge pass 2
clean; skill-forge(23) forged SF-004 `bug-pipeline` after the third clean
judge pass plus final lint; skill-forge(24) captured RED evidence for SF-005
`clean-room`; and skill-forge(25) patched the target skill for those named
rationalizations, leaving SF-005 at `patched` with 0/3 clean runs. Next
skill-forge cycle: run REFACTOR judge pass 1 for SF-005 only, using the
scenario in `agent-state/skill-forge-runs/clean-room.md` with
`development/clean-room/SKILL.md` loaded. If the judge returns COMPLY, mark
`refactor-clean-1`; if it finds a loophole, quote it, reset SF-005 to
`red-captured`, run `python scripts/audit-jar.py`, commit state, and stop.

report-derived-skills(1) added SF-021 `unit-test-quality` from
`C:\Users\Guerr\Downloads\deep-research-report (5).md`. Next jar-audit cycle:
run `python scripts/audit-jar.py`; if green, preserve the generated
`skills.json` and plugin manifest updates. Next skill-forge cycle: continue
the existing queue order and eventually run RED for SF-021 using weak-assertion,
coverage-chasing, mutation-skipping, and flaky-test pressure.

report-derived-skills(2) tightened SF-021 from the user's concrete requirement:
the skill must build real unit tests and audit or replace AI-generated slop
tests. Next skill-forge cycle remains formal RED capture; SF-021 is still
`pending-red`, with pressure expanded to AI slop tests, weak assertions, and
coverage-metric shortcuts.

For future drop-in skills, run `python scripts/sync-jar.py` before
`python scripts/audit-jar.py`; missing skill-forge rows should appear as
`pending-red`, and hook evidence should accumulate in
`agent-state/skill-usage.md`.

ecosystem-audit-1 ran a deep, evidence-backed audit of all 23 skills (29-agent
workflow: one reader per skill + 6 cross-cutting lenses). The structural gate is
GREEN (208 checks, 0 failed after this cycle's edits). It applied the four
highest-leverage fixes this cycle (kit-name alignment, sprint-ticket-runner
launch gate, the loop-architecture link, and `docs/ecosystem-map.md`) and filed
the rest to `triage-inbox.md` (F-1..F-12) and `decisions.md` (HD-1..HD-5). Next
jar-audit cycle: take ONE Open Task (T-ECO-1 recommended first — instrument-
observability NOT-for is low-risk and resolves a real routing collision), maker
fixes it, a SEPARATE checker verifies, run `python scripts/audit-jar.py`, commit
code + state together, stop. The proposed new gates (HD-1..HD-3) are audit-policy
changes that need explicit human approval before a maker implements them — do not
add them silently. Note: prior "27 checks"/"182 checks" narration in this file is
stale; the current count is 208.

jar-audit-eco-1 (user-authorized autonomous run, all-three-loops rotation, until
done/blocked) closed all four Open Tasks T-ECO-1..4 via a maker->checker workflow
(8 agents): T-ECO-1/3/4 passed first try; T-ECO-2 was rejected by its checker for
one inaccurate "FUGAZI above" cross-reference, corrected, and re-verified PASS by
an independent validator. skills.json was regenerated for the instrument-
observability description change. Gate green (208 checks, 0 failed). Closed
findings F-1, F-2, F-3, F-8, F-10, F-12 and the arch-drift/instrument edges of
F-7; remaining open findings F-4, F-5, F-6, F-7 (partial), F-9, F-11 stay in
triage-inbox. Next in the authorized rotation: bug-pipeline hunter sweep (focus
the files changed this run + cross-file consistency), then skill-forge on the
queue (SF-005 clean-room needs REFACTOR judge runs; SF-023 instrument-
observability re-baselines after this run's edits; SF-006..022 pending-red).

skill-forge-batch1 (user-authorized rotation) forged SF-005 clean-room (3/3
judges COMPLY on the existing GREEN) and SF-023 instrument-observability (forger
applied the GREEN patch closing the captured RED rationalizations; 3/3 independent
judges COMPLY; forger != judge). Gate green (208). Forge queue now: SF-001..005
and SF-023 = forged (6 of 23); SF-006..022 + SF-021 still pending-red (need RED
scenario authoring + capture, then GREEN, then 3 judge runs each). Next skill-forge
batch: pick the next pending-red skills, run RED (fresh agents WITHOUT the skill)
to capture rationalizations, GREEN-patch to close them, then 3 judge runs; advance
in reviewable batches. Note: forging the ~17 remaining is multi-batch — each is a
content-editing RED->GREEN->judge x3 pipeline.

skill-forge-queue forged ALL 17 remaining skills in one concurrent workflow
(85 agents, forger != judge, disjoint files): 17/17 surfaced a real RED failure,
were GREEN-patched, and returned 3/3 COMPLY from independent judges; gate green
(208). The FORGE QUEUE IS NOW COMPLETE — 23/23 forged. With this, the
user-authorized "all three loops, until done or blocked" rotation is finished:
jar-audit (T-ECO-1..4 closed), bug-pipeline (BUG-001 verified), skill-forge
(23/23 forged). No loop has open/ready work. Remaining repo work is human-gated:
the open triage-inbox findings F-4, F-5, F-6, F-7 (partial), F-9, F-11 (low/medium,
not yet promoted) and the audit-policy decisions HD-1..HD-5 in decisions.md
(propose new gates — need explicit human approval before a maker implements them).
NOTE on forge maturity: these are first-pass forges gated by LLM judges + the
structure gate; `forged` means RED-evidenced + 3/3 clean + gate-green, which is
distinct from the `dogfooded`/`battle-tested` maturity tiers (real-use evidence).

## Current Restart Status -- 2026-08-31

The historical completion statement above is superseded for current execution.
SF-001 `arch-drift-watch` and SF-029 `guardrail-forge` are reopened at `0/3`
after independent executable counterexamples; the forge queue therefore has
open work. The current implementation is the fifty-sixth GREEN described in
`GUARDRAIL_FORGE_HANDOFF.md` and the two forge run packages. Its exact next
action is the full focused/full/audit/skill/diff gate sequence followed by three
fresh read-only judges. Do not reuse any prior clean verdict or mark either row
forged before all three current-revision judges comply.

## Release Preparation -- 2026-08-31

The human directed the completed local guardrail-forge build to be committed,
merged, and pushed without continuing the optional adversarial certification
loop. Pre-commit verification on the current implementation passed all 91 tests
and the mandatory jar audit passed all 299 checks. SF-001 and SF-029 remain
honestly labeled `reopened` at `0/3`; shipping the integrated implementation does
not relabel either skill as `forged`.

## Current Restart Status -- 2026-09-08

SF-032 `change-impact-proof` is complete in the isolated
`feat/change-impact-proof` worktree and is not committed. Its clean-room
implementation passed 3/3 independent executable judges, 11/11 behavioral
acceptance checks, the no-attribution contamination review, 91 unit tests, and
the mandatory jar audit at 321/321. The exact next action is human review and
approval of the proposed local commit message; do not push.

## Current Restart Status -- 2026-09-08 (SF-033)

SF-033 `verification-evidence-plan` is complete in the isolated
`feat/verification-evidence-plan` worktree and is not committed. Its original
read-only implementation passed 3/3 independent scenario judges, 11/11
behavioral acceptance, 5/5 adversarial planning, the 355-line contamination
gate, 91 unit tests, and the mandatory jar audit at 319/319. The exact next
action is human review and approval of a proposed local commit message; do not
push.

## Current Restart Status -- 2026-09-09 (SF-034)

SF-034 `decision-evidence-ledger` is complete in the isolated
`feat/decision-evidence-ledger` worktree and is not committed. Its original
read-only-by-default implementation passed 3/3 independent scenario judges at
5/5 each, 11/11 behavioral acceptance, 5/5 write safety, the independent
contamination review, 91 unit tests, and the mandatory jar audit at 324/324.
The exact next action is human review and approval of a proposed local commit
message; do not push.

## Current Restart Status -- 2026-09-08 (SF-035)

SF-035 `runtime-path-forensics` is implemented in the isolated
`feat/runtime-path-forensics` worktree and is not committed. The captured RED
response reached a bounded conclusion but omitted stable record/hop IDs, typed
edges, interval timeline records, explicit per-record strengths, per-hop
alternatives, and discriminator owner/access/cost fields. The GREEN skill and
integration are present; quick validation, 91 tests, the 329-check jar audit,
the 11-path allowlist, protected-input verification, added-content scan, and
diff check passed. Three independent current-revision scenario judges complied;
schema promotion complied and final acceptance passed, with all six raw response
hashes recorded in the run package. SF-035 is `forged` at `3/3`. The exact next
action is human review and approval of a proposed local commit message. Do not
commit, merge, or push without that approval.

## Current Restart Status -- 2026-09-08 (SF-036)

SF-036 `handoff-recovery` is implemented in the isolated
`feat/handoff-recovery` worktree and is not committed. RED captured provisional
branch selection before task binding, placeholder worktree commands, prose-only
recovery without complete input identity and promotion rules, and unbounded
sensitive-history inspection. The GREEN skill and integration are present;
quick validation, 91 tests, the 334-check jar audit, the 11-path allowlist,
protected-input verification, contamination scan, and diff check passed.
Three independent current-revision scenario judges returned COMPLY; schema and
verdict promotion returned COMPLY, and final acceptance passed 16/16. All seven
raw evaluator-response hashes are recorded in the run package. SF-036 is
`forged` at `3/3`. The exact next action is human review and approval of the
exact local commit message. Do not commit, merge, or push without that approval.

## Current Restart Status -- 2026-09-08 (SF-037)

SF-037 `subsystem-explanation` is complete in the isolated
`feat/subsystem-explanation` worktree and is not committed. RED captured a
prose-only explanation without stable evidence relationships and a diagram that
continued through admitted assumptions. The original GREEN skill was repaired
after hostile design and schema rejections, then passed three independent
current-revision scenarios at 5/5 each, schema promotion at 6/6, and final
acceptance at 16/16. Quick validation, 91 tests, the 339-check jar audit, the
eleven-path allowlist, nine protected gate inputs, change-surface contamination
scan, and diff check passed. The final-state jar audit passed 339/339. The exact
next action is human approval of the exact local commit message. Do not commit,
merge, or push without that approval.
## Current Restart Status -- 2026-09-09 (SF-038)

SF-038 `visual-parity-proof` is complete in the isolated
`feat/visual-parity-proof` worktree and is not committed. RED captured acceptance
of an unbound aggregate score and provisional approval despite missing required
responsive evidence. The original GREEN skill passed three independent
current-revision scenarios at 6/6 each, schema promotion at 8/8, and final
acceptance at 18/18 after the mask schema was repaired to preserve simultaneous
invalidity reasons. Quick validation, 91 tests, the 344-check jar audit, the
changed-path allowlist, nine protected gate inputs, change-surface scan, and
diff check passed. SF-038 is `forged` at `3/3`. The exact next action is human
approval of the exact local commit message. Do not commit, merge, or push
without that approval.
