#!/usr/bin/env python3
"""Scaffold the skeleton of an agent loop into a target repo (loop-engineer skill).

Layer 1 tool. You (the human scaffolding the loop now) run this once to lay
down the loop's spine: the REQUIRED file-based state (``agent-state/``), the
host agent directories, ``AGENTS.md`` safety rules, and a placeholder driver
prompt. The Layer-2 text the future loop-agent will run -- enriched state
files, subagents, role-skills, the real driver prompt -- is authored AFTER
this from the loop-engineer skill's ``references/``; the starter files written here
are deliberately MINIMAL (headers + empty table skeletons) so they cannot
drift from those annotated references.

Properties:
- Stdlib only. No pip dependencies. Python 3.8+.
- Cross-platform. Uses pathlib; no shell-isms, no os.system, no symlinks.
- Idempotent. Never overwrites an existing file; prints "skip (exists)" vs
  "create" per path so re-running is safe.

State files are the REQUIRED restart mechanism. MemBerry is an OPTIONAL
adapter layered on top -- this scaffolder never touches it; steps labelled
"(MemBerry)" live in the references, not here.

Usage:
    python scripts/scaffold-loop.py --loop-name daily-triage --repo .
    python scripts/scaffold-loop.py --loop-name release-bot --host codex --level 2
"""

import argparse
import sys
from pathlib import Path

# --- where the full, annotated Layer-2 templates live (relative to the skill) ---
REF_STATE = "references/state-templates.md"
REF_SUBAGENTS = "references/subagent-templates.md"
REF_AUTOMATION = "references/automation-templates.md"
REF_ROLE_SKILLS = "references/role-skills/"
REF_SAFETY = "references/safety-and-gates.md"


# ---------------------------------------------------------------------------
# Minimal inlined templates.
#
# Kept intentionally bare: headers + table skeletons only. The reader enriches
# them from the references above. Do NOT grow these into full annotated
# versions -- that is what the references/ are for, and duplicating them here
# guarantees drift.
# ---------------------------------------------------------------------------

def loop_state_md(loop_name, level):
    level_notes = {
        1: "1 (triage-only) -- discovery + planning only; the loop writes NO code this level.",
        2: "2 (isolated implementation) -- maker writes code in a worktree; checker gates it.",
        3: "3 (connector integration) -- the loop may use external connectors (issues, CI, PRs).",
        4: "4 (semi-autonomous) -- scheduled/unattended; human reviews only at the merge gate.",
    }
    return f"""# Loop State -- {loop_name}

> The REQUIRED restart spine. A restarted loop-agent reads THIS file to learn
> what is done, what verifies the work, and what to do next. Enrich from
> {REF_STATE} (full annotated version). Keep this file host-neutral.
>
> Autonomy level: {level_notes.get(level, level_notes[1])}
> Raise the level only by evidence -- record the bar to clear in Next Run Instructions.

## Current Objective
<One narrow sentence. e.g. "Each run, triage new CI failures and open bugs into the inbox."
NOT "improve the codebase.">

## Verification Commands
<The runnable gate(s). Each MUST exit 0 on pass, non-zero on fail. No "looks good".
List the exact commands confirmed to run in THIS repo, e.g.:>
- ` ` (test suite)
- ` ` (lint)
- ` ` (typecheck)
- ` ` (build)

## Open Tasks
| ID | Task | Owner | Status | Files | Acceptance (exits 0) |
|----|------|-------|--------|-------|----------------------|

## Completed Tasks
| ID | Task | Cycle | Commit | Result |
|----|------|-------|--------|--------|

## Failed Attempts
| ID | Task | What Failed | Lesson |
|----|------|-------------|--------|

## Current Rules
<Loop-specific rules layered on top of AGENTS.md. e.g. scope limits, files off-limits,
which connectors are allowed at this autonomy level.>

## Next Run Instructions
<What the next cycle starts with: the next Open Task #, or "discovery only", or a
blocked-needs-human note. The single most important line for a cold restart.>
"""


def triage_inbox_md(loop_name):
    return f"""# Triage Inbox -- {loop_name}

> Discovery appends findings here; planning promotes one into loop-state.md Open
> Tasks. One finding = one heading block (NOT a table). Every finding needs a
> runnable Verification command. Enrich from {REF_STATE}.

## Findings

<!-- One block per finding; delete this comment once real findings land:
### F-1 -- <Title: one concrete sentence>
- **Source:** <CI run | issue #N | commit <sha> | TODO at file:line | test <name> | branch <name>>
- **Priority:** High | Medium | Low
- **Risk:** low | medium | high
- **Suggested owner:** explorer | implementer | verifier | security-reviewer
- **Verification command:** `<exact command that exits 0 when the task is done>`
-->
"""


def completed_md(loop_name):
    return f"""# Completed -- {loop_name}

> Durable record of finished work so a restart never re-does it. Enrich from {REF_STATE}.

| ID | Task | Cycle | Commit | Result |
|----|------|-------|--------|--------|
"""


def failed_attempts_md(loop_name):
    return f"""# Failed Attempts -- {loop_name}

> What was tried and did NOT work, so the loop does not loop on the same wall.
> Never delete rows here. Enrich from {REF_STATE}.

| ID | Task | What Failed | Lesson |
|----|------|-------------|--------|
"""


def decisions_md(loop_name):
    return f"""# Decisions -- {loop_name}

> Choices made and their rationale (the file-based fallback for what MemBerry
> would otherwise remember). Enrich from {REF_STATE}.

| Decision | Rationale | Cycle |
|----------|-----------|-------|
"""


def agents_md(loop_name):
    return f"""# AGENTS.md -- default safety rules for the {loop_name} loop

> Host-neutral safety rules every agent in this loop obeys, every cycle. These
> are the floor; per-loop additions go in agent-state/loop-state.md (Current
> Rules). Full annotated version + per-host gate wiring: {REF_SAFETY}.

## General
- Do exactly one narrow task per cycle. No scope creep beyond the planned task.
- The agent that wrote a change is NEVER the only agent that verifies it
  (maker != checker). The checker is separate and adversarial, and may reject.
- When a change is expensive to reverse (public API, schema, on-disk format,
  cross-module deletion) or intent is ambiguous: STOP and write a row to the
  blocked/decisions state, then continue other work. Do not guess.

## Code Changes
- Smallest diff that satisfies the task. No drive-by renames, reformatting, or
  restructuring of untouched code.
- Touch only files the task names. Changing unrelated files fails the gate.
- Work in an isolated worktree/branch -- one task per worktree per branch.
- Never add secrets, tokens, or credentials to the repo.

## Verification
- Every gate is a runnable command that exits 0 (pass) or non-zero (fail).
  "Looks good" is not a gate.
- Never weaken, skip, delete, or loosen an existing test to make the suite
  pass. A genuinely-wrong test is a logged, justified task -- not a silent edit.
- The verification suite must actually run and report a real result. An
  empty, missing, or erroring suite is a STOP-and-report, never a pass.

## State
- Update agent-state/ BEFORE committing. Commit code and state TOGETHER in one
  commit so a restart never sees committed-but-unrecorded work.
- Record every failed attempt in agent-state/failed-attempts.md. Do not delete
  rows from it.
- The human owns architecture, merge decisions, security boundaries, and cost.
  The loop discovers, drafts, tests, and summarizes; the human decides what ships.
"""


def driver_prompt_md(loop_name):
    return f"""# {loop_name} -- Driver Prompt (PLACEHOLDER)

> Layer 2. This is the per-cycle prompt the loop-agent runs each cycle -- write
> the body in the imperative addressed to that future agent, not to yourself.
> This file is a STUB: fill it in from {REF_AUTOMATION} (the driver-prompt +
> platform-primitive map). It must walk the six-part spine for ONE cycle and
> end by updating state.

## Identity
<One sentence: what this loop-agent is and which repo it drives.>

## Each cycle, walk the spine (fill from {REF_AUTOMATION})

1. Trigger      -- <how this cycle started; nothing to do but note the run id>.
2. Discovery    -- <find work (CI/issues/TODOs/commits); write rows to
                   agent-state/triage-inbox.md>.
3. Planning     -- <read the inbox + agent-state/loop-state.md; pick ONE small,
                   verifiable Open Task for this cycle>.
4. Execution    -- <the maker does the task in an isolated worktree>.
5. Verification -- <a SEPARATE checker runs the Verification Commands from
                   loop-state.md; it gates on exit code and may reject>.
6. State update -- <record the result in agent-state/ (completed/failed/
                   decisions + loop-state Next Run Instructions); commit code
                   and state together>.

## Stop conditions
<When to halt and ask the human (from AGENTS.md / loop-state Current Rules).>

<!-- Subagents and role-skills are authored separately; see the NEXT STEPS this
     scaffolder printed. Wire host triggers ({loop_name} schedule/event) per
     {REF_AUTOMATION}. -->
"""


# ---------------------------------------------------------------------------
# Filesystem helpers
# ---------------------------------------------------------------------------

def ensure_dir(path, results):
    """Create a directory (and parents) if absent. Record create vs skip."""
    if path.exists():
        results.append(("skip (exists)", path, True))
    else:
        path.mkdir(parents=True, exist_ok=True)
        results.append(("create", path, True))


def write_if_absent(path, content, results):
    """Write content to path only if it does not already exist (idempotent).

    Records ("skip (exists)", ...) when present, ("create", ...) when written.
    Parent directories are created as needed.
    """
    if path.exists():
        results.append(("skip (exists)", path, False))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    results.append(("create", path, False))


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def build(loop_name, repo, host, level):
    """Lay down the loop skeleton under `repo`. Returns the results log."""
    results = []

    state_dir = repo / "agent-state"
    prompts_dir = repo / "docs" / "prompts"
    triage_skill_dir = repo / "skills" / "triage"

    # Directories: state + prompts + role-skill home (always), then host dirs.
    ensure_dir(state_dir, results)
    ensure_dir(prompts_dir, results)
    ensure_dir(triage_skill_dir, results)
    # Keep the (otherwise empty) skills/triage/ dir in git until its SKILL.md lands.
    write_if_absent(triage_skill_dir / ".gitkeep", "", results)

    if host in ("claude", "both"):
        claude_agents = repo / ".claude" / "agents"
        ensure_dir(claude_agents, results)
        # Empty dirs aren't tracked by git; keep it until the role .md files land.
        write_if_absent(claude_agents / ".gitkeep", "", results)
    if host in ("codex", "both"):
        codex_agents = repo / ".codex" / "agents"
        ensure_dir(codex_agents, results)
        write_if_absent(codex_agents / ".gitkeep", "", results)
    # host == "generic" creates no host agent dir; subagents stay portable.

    # Starter state files (REQUIRED spine -- minimal, enrich from references).
    write_if_absent(state_dir / "loop-state.md", loop_state_md(loop_name, level), results)
    write_if_absent(state_dir / "triage-inbox.md", triage_inbox_md(loop_name), results)
    write_if_absent(state_dir / "completed.md", completed_md(loop_name), results)
    write_if_absent(state_dir / "failed-attempts.md", failed_attempts_md(loop_name), results)
    write_if_absent(state_dir / "decisions.md", decisions_md(loop_name), results)

    # Safety rules + placeholder driver prompt.
    write_if_absent(repo / "AGENTS.md", agents_md(loop_name), results)
    write_if_absent(prompts_dir / f"{loop_name}-driver.md", driver_prompt_md(loop_name), results)

    return results


def print_summary(results, loop_name, host):
    created = [p for (action, p, _is_dir) in results if action == "create"]
    skipped = [p for (action, p, _is_dir) in results if action != "create"]

    print()
    for action, path, _is_dir in results:
        print(f"  {action:<14} {path}")

    print()
    print(f"Summary: {len(created)} created, {len(skipped)} skipped (already existed).")

    print()
    print("NEXT STEPS (Layer 2 -- author the text the loop-agent will run):")
    print(f"  1. Enrich the state files from {REF_STATE}")
    print("     (loop-state.md, triage-inbox.md, completed.md, failed-attempts.md, decisions.md):")
    print("     set the Current Objective to ONE narrow sentence and fill the")
    print("     Verification Commands with commands confirmed to run in this repo.")
    print(f"  2. Add the maker!=checker subagents from {REF_SUBAGENTS}")
    print("     in your host's format:")
    if host in ("claude", "both"):
        print("       - Claude Code: .claude/agents/<role>.md")
    if host in ("codex", "both"):
        print("       - Codex:       .codex/agents/<role>.toml")
    if host == "generic":
        print("       - Generic host: keep the portable forms from the references; "
              "no host agent dir was created.")
    print("     Roles: explorer, implementer, verifier (and security-reviewer if")
    print("     auth/secrets/permissions are in scope). The verifier must be able to reject.")
    print(f"  3. Install the role-skills the loop uses from {REF_ROLE_SKILLS}")
    print("     into skills/ (triage is scaffolded as skills/triage/); adapt each to")
    print("     this repo's real commands and conventions.")
    print(f"  4. Author the driver prompt docs/prompts/{loop_name}-driver.md")
    print(f"     from {REF_AUTOMATION}, and wire the host trigger")
    print("     (Claude Code: /loop or a scheduled task; Codex: scheduled run;")
    print("      generic fallback: cron / CI workflow).")
    print("  5. Set the gate: confirm every Verification Command exits 0/1, and")
    print(f"     review AGENTS.md against {REF_SAFETY}.")
    print("  6. Dry-run ONE full cycle (trigger -> discovery -> planning ->")
    print("     execution -> verification -> state update) before handing off.")
    print()
    print("State files are the REQUIRED mechanism. MemBerry steps are OPTIONAL and")
    print("labelled \"(MemBerry)\" in the references -- skip them if MemBerry is absent.")


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="scaffold-loop.py",
        description="Scaffold an agent-loop skeleton into a repo "
                    "(idempotent; never overwrites existing files).",
    )
    parser.add_argument(
        "--loop-name",
        required=True,
        help='short kebab name for the loop, e.g. "daily-triage"',
    )
    parser.add_argument(
        "--repo",
        default=".",
        help="target repo root (default: current directory)",
    )
    parser.add_argument(
        "--host",
        choices=["claude", "codex", "both", "generic"],
        default="both",
        help="which agent directories to create (default: both)",
    )
    parser.add_argument(
        "--level",
        type=int,
        choices=[1, 2, 3, 4],
        default=1,
        help="autonomy level, noted in loop-state.md (default: 1, triage-only)",
    )

    args = parser.parse_args(argv)

    repo = Path(args.repo).expanduser().resolve()
    if repo.exists() and not repo.is_dir():
        parser.error(f"--repo is not a directory: {repo}")
    if not repo.exists():
        print(f"NOTE: --repo did not exist; creating {repo}")
        repo.mkdir(parents=True, exist_ok=True)

    print(f"Scaffolding loop '{args.loop_name}' into {repo}")
    print(f"  host={args.host}  level={args.level}")

    results = build(args.loop_name, repo, args.host, args.level)
    print_summary(results, args.loop_name, args.host)
    return 0


if __name__ == "__main__":
    sys.exit(main())
