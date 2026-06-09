# jar-audit -- Driver (one loop cycle)

You run ONE cycle of the skill jar's structural-audit loop, then stop. The jar
is a published collection of Agent Skills; your job is to keep it structurally
publish-ready. Operate only inside `agent-state/` and the files a chosen task
names. Never widen scope.

## 0. Preflight

- Run `git status`. If the tree is dirty from a crashed prior cycle, recover the
  in-flight task from `agent-state/loop-state.md`: finish it from the partial
  diff OR `git checkout .` back to the last good commit. Log the recovery either
  way. Do not start new work on a dirty tree.
- Read `agent-state/loop-state.md` (objective, rules, verification commands),
  `agent-state/failed-attempts.md`, and `agent-state/completed.md`.

## 1. Discovery -- run the gate

Discovery here is deterministic: run

```
python scripts/audit-jar.py
```

- **Exit 0 and `agent-state/triage-inbox.md` has no open findings:** this is a
  clean cycle -- a valid success. Skip to step 5 and record it. Never
  manufacture work.
- **Exit 1:** convert each NEW failure into an inbox finding (`### F-<id>`
  format per the inbox header) with Priority, and the failing audit line as the
  Verification command. Skip failures already in `completed.md` or matching a
  `failed-attempts.md` row.

## 2. Planning -- pick ONE finding

Choose the single highest-priority finding from `agent-state/triage-inbox.md`.
Restate it in `loop-state.md` Open Tasks (Status: IN PROGRESS) with its files
and acceptance command, so a crash mid-cycle is recoverable.

## 3. Execution (maker)

The **fixer** agent (`.claude/agents/fixer.md`) implements the smallest diff
that makes the failing check pass. No drive-by edits. A fix must not weaken the
audit script itself to turn the gate green -- fixing the gate is a
human-decision item, never a silent edit.

## 4. Verification (checker -- a SEPARATE agent)

The **validator** agent (`.claude/agents/validator.md`) re-runs
`python scripts/audit-jar.py` (must exit 0), inspects the diff for scope creep,
and decides PASS or REJECT with evidence. On REJECT: log to
`failed-attempts.md`, revert, and end the cycle.

## 5. State update + commit (code and state together)

- Move the finding to `completed.md`; clear the in-flight slot and set Next Run
  Instructions in `loop-state.md`. For a clean cycle, append a one-line note to
  Next Run Instructions instead.
- Commit everything as one unit:

  ```
  git add <changed files> agent-state/
  git commit -m "jar-audit(N): <finding title or 'clean cycle -- gate green'>"
  ```

- Do NOT push. Pushing is the human's call (Level 2).

## Stop conditions

Stop after one task (or a recorded clean cycle). Escalate to the human -- write
the item to `agent-state/decisions.md` under "Blocked -- Needs Human Decision"
and continue other work -- when a fix would: change a skill's public contract
(its name or description triggers), modify the audit script's checks, delete a
skill file, or rest on genuinely ambiguous intent.
