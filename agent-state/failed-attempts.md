# Failed Attempts -- jar-audit

> What was tried and did NOT work, so the loop does not loop on the same wall.
> Never delete rows here. Enrich from references/state-templates.md.

| ID | Task | What Failed | Lesson |
|----|------|-------------|--------|
| FA-2026-06-10-SD-ENG-1 | Add engineering-direction templates to systems-design skills | `git diff --check` found trailing whitespace in `systems-design/production-readiness/references/readiness-playbook.md` after the first template pass. | Use explicit placeholder text instead of blank bullet lines, then rerun `git diff --check` before committing. |
| FA-2026-06-10-DEV-SP-1 | Check development skills for Superpowers hard prerequisites | An ad hoc description-length check used Unix heredoc syntax (`python - <<'PY'`) in PowerShell and failed before running. | Use `python -c` or a PowerShell here-string for one-off Python checks on this Windows workspace. |
| FA-2026-06-10-DEV-ABS-1 | Check development skills for concrete output contracts | A PowerShell category scan assumed every directory under `development/` had a `SKILL.md`; support folders `.claude-plugin` and `agents` made `Get-Content` fail. | Filter directories with `Test-Path <dir>/SKILL.md` before scanning skill metadata. |
| FA-2026-06-10-PREP-1 | Run prep-for-GitHub audit before direct push | A PowerShell one-liner for checking editor/tool config status had a mismatched subexpression and failed before returning results. | Use a `foreach` block with separate `git check-ignore` and `git ls-files` calls for this audit on Windows. |
| FA-2026-06-10-PLAN-PRUNE-1 | Rename planning consolidation workflow | `git add ... <old path>` failed because the old directory path had already been moved. | Stage the renamed files through the new `development/plan-prune` path and rely on git's recorded rename. |
| FA-2026-06-10-SPRINT-1 | Initialize sprint-ticket-runner skill | `init_skill.py` created `development/sprint-ticket-runner/SKILL.md` but stopped because the supplied `short_description` was 78 characters, over the 64-character interface limit. | Keep optional UI `short_description` values between 25 and 64 characters when using the initializer. |
| FA-2026-06-10-SPRINT-2 | Check sprint-ticket-runner description length | A one-line Python regex command was quoted for `cmd`/bash style and PowerShell interpreted the `.*?` regex fragment as a command before Python ran. | Use native PowerShell matching or a PowerShell here-string for regex checks in this workspace. |
