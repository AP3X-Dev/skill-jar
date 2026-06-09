# marketing (reserved category)

This is a **skill category** — a folder whose skills install as their own
Claude Code plugin (`skill-jar-marketing`), so a user can grab just the
marketing skills without the rest of the jar.

It has no skills yet. To add one:

1. Create `marketing/<skill-name>/SKILL.md` (a normal Agent Skill).
2. Run `python scripts/gen-plugins.py` and `python scripts/gen-index.py`.

The generators read the directory layout — **the folder a skill lives in is its
category** — and produce the `skill-jar-marketing` plugin entry, its
`plugin.json`, the bundle, and `skills.json` automatically. The audit gate
(`scripts/audit-jar.py`) then fails if any of them drift. Until a skill lands
here, no `skill-jar-marketing` plugin is generated — empty categories ship
nothing.
