# skill-forge -- Driver (one loop cycle)

> This is the jar's own instance of the portable **skill-forge** skill
> (`../../development/skill-forge/SKILL.md`). Repo-specific state lives in
> `agent-state/SKILL_FORGE_TRACKER.md`; per-skill evidence packages live under
> `agent-state/skill-forge-runs/`.

You run ONE cycle of the skill jar's forge loop, then stop. The loop advances
exactly one skill by exactly one forge stage. It never starts a second skill in
the same cycle.

## Hook dispatch

After each skill-forge stage updates its tracker row and run package, run the hook dispatcher so generated role hooks record usage, failures, and improvement evidence:

- `python scripts/dispatch-agent-hooks.py --agent skill-forge-pressure-tester --event after_task --skill <skill-name> --note "<scenario, shortcut, rationalization>"`
- `python scripts/dispatch-agent-hooks.py --agent skill-forge-forger --event after_task --skill <skill-name> --note "<loopholes closed / files changed / audit result>" --status <new-status> --clean-runs <count> --evidence "<audit result>" --next-action "<next step>"`
- `python scripts/dispatch-agent-hooks.py --agent skill-forge-judge --event after_task --skill <skill-name> --note "<judge verdict / evidence / clean-run count>" --status <new-status> --clean-runs <count> --evidence "<judge result>" --next-action "<next step>"`
- `python scripts/dispatch-agent-hooks.py --agent skill-forge-linter --event after_task --skill <skill-name> --note "<lint command / result / forged-or-reopened status>" --command "python scripts/audit-jar.py" --result "exit 0"`
- On stage failure, dispatch `--event on_error` or the role's specific failure event with `--failure-task`, `--failure-what`, and `--lesson`.

## 0. Preflight

- Run `git status`. If the tree is dirty from a crashed prior cycle, recover the
  in-flight skill from `agent-state/loop-state.md` and
  `agent-state/SKILL_FORGE_TRACKER.md`: finish that stage from the partial diff
  OR revert to the last gate-green commit. Log the recovery either way. Do not
  start new forge work on a dirty tree.
- Read `agent-state/loop-state.md`, `agent-state/SKILL_FORGE_TRACKER.md`,
  `agent-state/failed-attempts.md`, `agent-state/completed.md`, and
  `agent-state/decisions.md`.
- If the tracker is missing a skill that appears in `skills.json`, append a new
  row with `pending-red`. Never delete tracker rows automatically; mark removed
  skills as a human-decision item.

## 1. Planning -- pick ONE tracker row

Pick the highest-priority eligible row, in this order:

1. `reopened`
2. `red-captured`
3. `patched` or `refactor-clean-N`
4. `needs-stronger-scenario`
5. `pending-red`

Skip `forged` and `blocked`. Restate the chosen row in `loop-state.md` Open
Tasks with the skill path, current status, one-stage next action, and acceptance
command `python scripts/audit-jar.py`.

## 2. RED stage -- capture a real shortcut

Run only for `pending-red` or `needs-stronger-scenario` rows.

- Read the target `SKILL.md` to understand what behavior should hold, but do
  not give the skill text to the pressure tester.
- Create one realistic pressure scenario that tempts the shortcut named in the
  tracker row.
- Dispatch `skill-forge-pressure-tester` from the generated development agent
  pack. The pressure tester must not read the target skill during RED.
- Record the transcript, shortcut taken, and verbatim rationalizations in
  `agent-state/skill-forge-runs/<skill-name>.md`.
- If no realistic failure appears, mark the row `needs-stronger-scenario`,
  update the run package with the pressure improvements needed, run the gate,
  commit state, and stop.
- If a failure appears, mark the row `red-captured`, list the named
  rationalizations, run the gate, commit state, and stop.

## 3. GREEN stage -- patch only captured loopholes

Run only for `red-captured` or `reopened` rows.

- Dispatch `skill-forge-forger` with the target skill path and the run package.
- Patch only the target skill files needed to close the named RED
  rationalizations. Do not add imagined rules.
- Keep `SKILL.md` lean; move heavy material to a one-level `references/` file
  only when it removes real bulk.
- Do not change a skill name or routing description trigger silently. If the
  only viable fix changes the public skill contract, write a
  `decisions.md` blocked row and mark the tracker row `blocked`.
- Run `python scripts/audit-jar.py`. If it exits non-zero, log the failed
  approach in `failed-attempts.md`, mark the row `reopened`, and stop.
- On success, mark the row `patched`, reset clean runs to `0/3`, update the run
  package with files changed and loopholes closed, commit code and state, and
  stop.

## 4. REFACTOR stage -- judge with the skill loaded

Run only for `patched` or `refactor-clean-N` rows.

- Dispatch `skill-forge-judge` with the same scenario and the target skill
  loaded.
- If the judge finds a loophole, quote it in the run package, mark the row
  `red-captured`, reset clean runs to `0/3`, run the gate, commit state, and
  stop.
- If the judge returns `COMPLY`, increment the clean-run count by one.
- At `1/3` or `2/3`, mark the row `refactor-clean-N`, run the gate, commit
  state, and stop.
- At `3/3`, dispatch `skill-forge-linter` or run the lint directly with
  `python scripts/audit-jar.py`. If it exits 0, mark the row `forged`; if not,
  mark it `reopened` with the lint failure.

## 5. State update + commit

Every outcome updates all relevant state before commit:

- `agent-state/SKILL_FORGE_TRACKER.md` carries status, clean-run count, last
  evidence, and next action.
- `agent-state/skill-forge-runs/<skill-name>.md` carries the RED transcript,
  GREEN patch notes, REFACTOR verdicts, and lint evidence.
- `agent-state/loop-state.md` clears the in-flight task and sets Next Run
  Instructions.
- `agent-state/completed.md` records a completed forge stage, or
  `agent-state/failed-attempts.md` records the failed approach.

Commit code and state together:

```
git add <changed skill files> agent-state/
git commit -m "skill-forge(N): <skill-name> <stage result>"
```

Do NOT push. Pushing is the human's call.

## Stop conditions

Stop after one forge stage. Escalate to `agent-state/decisions.md` and mark the
tracker row `blocked` when the stage would require a public skill contract
change, deleting a skill, broad rewriting unrelated to captured RED evidence,
changing `scripts/audit-jar.py`, or guessing at ambiguous intent.
