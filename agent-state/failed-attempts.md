# Failed Attempts -- jar-audit

> What was tried and did NOT work, so the loop does not loop on the same wall.
> Never delete rows here. Enrich from references/state-templates.md.

| ID | Task | What Failed | Lesson |
|----|------|-------------|--------|
| FA-2026-06-10-SD-ENG-1 | Add engineering-direction templates to systems-design skills | `git diff --check` found trailing whitespace in `systems-design/production-readiness/references/readiness-playbook.md` after the first template pass. | Use explicit placeholder text instead of blank bullet lines, then rerun `git diff --check` before committing. |
| FA-2026-06-10-DEV-SP-1 | Check development skills for Superpowers hard prerequisites | An ad hoc description-length check used Unix heredoc syntax (`python - <<'PY'`) in PowerShell and failed before running. | Use `python -c` or a PowerShell here-string for one-off Python checks on this Windows workspace. |
