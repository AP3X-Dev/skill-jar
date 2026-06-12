---
name: add-to-jar
description: "Use when adding, importing, or reconciling a Codex skill inside this skill jar, including when a user drops a SKILL.md folder into development/ or systems-design/ and expects generated indexes, plugin manifests, Skill Forge tracker, and hook evidence state to include it."
---

# Add to Jar

Use this skill to add exactly one skill to this repo and reconcile it with the jar ecosystem.

## Workflow

1. Work in an isolated branch or worktree. Do not push.
2. Choose the category: `development/` for implementation workflows, `systems-design/` for architecture or design guidance.
3. Put the skill at `<category>/<skill-name>/SKILL.md`. The folder name and frontmatter `name` must match, using lowercase letters, digits, and hyphens.
4. Keep the skill body concise. Use `references/`, `scripts/`, or `assets/` only when the skill truly needs bundled material.
5. Run `python scripts/sync-jar.py`.
6. Inspect the generated and state diffs before committing:
   - `skills.json`
   - `docs/core-skills.md`
   - `.claude-plugin/marketplace.json`
   - `<category>/.claude-plugin/plugin.json`
   - `agent-state/SKILL_FORGE_TRACKER.md`
   - `agent-state/skill-usage.md`, if created or changed
7. Confirm the new `agent-state/SKILL_FORGE_TRACKER.md` row is queued for Skill Forge rather than marked forged.
8. Run `python scripts/audit-jar.py`.
9. Fix only the new skill or its directly bundled resources if the audit fails.
10. Commit the skill, generated files, and state together locally.

## Drop-In Rules

- If the user already dropped a folder into the jar, preserve its content unless it violates jar naming, frontmatter, link, or safety rules.
- Do not hand-edit generated indexes or plugin manifests before running sync.
- Do not delete stale tracker rows or history while adding the new skill.
- Do not add hooks to ordinary `SKILL.md` files. Hook wiring belongs in repo-local agents or generated agent manifests.
- Stop and record a human decision if adding the skill requires changing public contracts, weakening `scripts/audit-jar.py`, deleting state/history, or guessing the category against user intent.
