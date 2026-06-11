# Skill Forge Run Packages

Each file in this directory records one skill's forge evidence. The tracker is
`agent-state/SKILL_FORGE_TRACKER.md`; the driver is
`docs/prompts/skill-forge-driver.md`.

Use this shape for each `<skill-name>.md` package:

```md
# Forge Run: <skill-name>

## Scenario Set
| ID | Pressure | Shortcut tempted |
|----|----------|------------------|

## RED Evidence
| Scenario | Fresh-agent result | Verbatim rationalization |
|----------|--------------------|--------------------------|

## GREEN Patch
- **Skill files changed:** <paths>
- **Loopholes closed:** <named rationalizations>
- **Rules added/tightened:** <sections>

## REFACTOR Verdicts
| Run | Scenario | Verdict | Evidence |
|-----|----------|---------|----------|

## Lint Evidence
- **Command/check:** `python scripts/audit-jar.py`
- **Result:** <exit/result>
```
