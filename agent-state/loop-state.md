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
fix/validate ONE pending bug if any. skill-forge(1) captured RED evidence for
SF-001 `arch-drift-watch` under
`agent-state/skill-forge-runs/arch-drift-watch.md`: ad hoc scanning, inferred
zones, silent baseline reset, immediate auto-fix, audit-gate overconfidence, and
loose triage routing. Next skill-forge cycle: run GREEN for SF-001 only, patch
`development/arch-drift-watch/SKILL.md` only as needed to close those named
rationalizations, run `python scripts/audit-jar.py`, commit state and code
together, and stop.
