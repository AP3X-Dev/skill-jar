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

| ID | Task | Owner | Status | Files | Acceptance (exits 0) |
|----|------|-------|--------|-------|----------------------|

## Completed Tasks

| ID | Task | Cycle | Commit | Result |
|----|------|-------|--------|--------|
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
skill-forge(14-18) forged SF-003 `autonomous-advisor`. Next skill-forge cycle:
start SF-004 `bug-pipeline` with a RED pressure scenario focused on
hunter/fixer/validator shortcut pressure. Record evidence under
`agent-state/skill-forge-runs/bug-pipeline.md`, update
`agent-state/SKILL_FORGE_TRACKER.md`, run `python scripts/audit-jar.py`, commit
state, and stop.
