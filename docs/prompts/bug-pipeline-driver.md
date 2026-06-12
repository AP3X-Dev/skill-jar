# bug-pipeline -- Driver (one loop cycle)

> This is the jar's own instance of the portable **bug-pipeline** skill
> (`../../bug-pipeline/SKILL.md` -- the canonical contract: roles, tracker
> schema, cycle shape). Repo-specifics live here; the contract lives there.

You run ONE cycle of the skill jar's Hunter -> Fixer -> Validator pipeline,
then stop. The pipeline hunts real defects in the jar's content and scripts
(wrong instructions, broken examples, script bugs, cross-file contradictions),
fixes one per cycle, and independently validates the fix. Tracker:
`agent-state/BUG_TRACKER.md`. Operate only inside `agent-state/` and the files
the chosen bug names.

## Hook dispatch

After each stage updates `agent-state/BUG_TRACKER.md`, run the hook dispatcher:

- `python scripts/dispatch-agent-hooks.py --agent hunter --event after_task --skill bug-pipeline --note "<sweep summary>"`
- `python scripts/dispatch-agent-hooks.py --agent fixer --event after_task --skill bug-pipeline --note "<bug title / root cause / gate result>"`
- `python scripts/dispatch-agent-hooks.py --agent validator --event after_task --skill bug-pipeline --note "<verdict / evidence / next status>"`
- On a hunter failure, run `python scripts/dispatch-agent-hooks.py --agent hunter --event on_error --skill bug-pipeline --failure-task "<sweep focus>" --failure-what "<what failed>" --lesson "<lesson>"`
- On a fixer failure, run `python scripts/dispatch-agent-hooks.py --agent fixer --event on_error --skill bug-pipeline --failure-task "<bug title>" --failure-what "<what failed>" --lesson "<lesson>"`
- On a validator rejection, run `python scripts/dispatch-agent-hooks.py --agent validator --event on_reject --skill bug-pipeline --failure-task "<bug title>" --failure-what "<why rejected>" --lesson "<lesson>"`

## 0. Preflight

Same as jar-audit: `git status` clean-or-recover, then read
`agent-state/loop-state.md`, `failed-attempts.md`, and the tracker.

## 1. Discovery -- the hunter (skip if pending bugs remain)

If `BUG_TRACKER.md` already holds `pending` bugs, skip discovery -- work the
backlog first. Otherwise dispatch the **hunter** agent
(`.claude/agents/hunter.md`): one bounded sweep (focus area from `loop-state.md`
Next Run Instructions, rotating between scripts, skill docs, and cross-file
consistency), at most 3 high-confidence findings, each with file:line evidence
and a repro. The hunter follows the bug-hunter skill's tracker format and
writes only to the tracker.

## 2. Planning -- pick ONE bug

Choose the single highest-priority `pending` bug. Check `failed-attempts.md` --
if this bug's approach already failed, pick a different bug or a different
approach. Restate it in `loop-state.md` Open Tasks (IN PROGRESS).

## 3. Execution -- the fixer (maker)

The **fixer** agent (`.claude/agents/fixer.md`) fixes exactly that one bug:
smallest diff, runs `python scripts/audit-jar.py` (must exit 0 -- no structural
regression), marks the bug `fixed` in the tracker with fix notes. The fixer
never marks its own work `verified`.

## 4. Verification -- the validator (checker, SEPARATE agent)

The **validator** agent (`.claude/agents/validator.md`) independently verifies
the `fixed` bug: reproduces the original symptom is gone, re-runs the gate,
inspects the diff for scope creep. Verdict: promote to `verified`, or `reopen`
with rejection notes. On reopen: log to `failed-attempts.md`, revert the fix,
end the cycle.

## 5. State update + commit (code and state together)

- Tracker reflects the bug's final status; `loop-state.md` Open Tasks cleared,
  Completed Tasks appended, Next Run Instructions set (including the next
  hunter focus area).
- One commit:

  ```
  git add <changed files> agent-state/
  git commit -m "bug-pipeline(N): <bug title or 'clean sweep -- no defects found'>"
  ```

- Do NOT push (Level 2 -- the human pushes).

## Stop conditions

One bug per cycle. A hunter sweep that files nothing is a valid, successful
cycle -- record it and stop. Escalate to `decisions.md` ("Blocked -- Needs
Human Decision") when a fix would change a skill's public contract, span
multiple cycles, or the "bug" might be deliberate design (check the skill's
own rationale first -- suppressions and unusual-but-working choices are
deliberate until proven otherwise).
