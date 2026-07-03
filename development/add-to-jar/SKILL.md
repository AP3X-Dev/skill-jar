---
name: add-to-jar
description: "Use when adding, importing, or reconciling a Codex skill inside this skill jar, including when a user drops a SKILL.md folder into development/ or systems-design/ and expects generated indexes, plugin manifests, Skill Forge tracker, and hook evidence state to include it."
---

# Add to Jar

Use this skill to add exactly one skill to this repo and reconcile it with the jar ecosystem.

## When NOT to use

- **Authoring a skill from scratch.** This skill reconciles an *existing* `SKILL.md` folder into the jar. To design and pressure-test new skill *behavior*, use [skill-forge](../skill-forge/SKILL.md) (plus your host's skill-authoring skill, e.g. `write-a-skill`, if present) — then bring the finished folder here.
- **Editing or improving an already-installed skill.** Changing an existing skill's content is a direct edit or a [skill-forge](../skill-forge/SKILL.md) pass, not an intake reconcile.
- **Bulk-importing many skills in one pass.** Add skills one at a time so each gets its own reviewable `sync-jar.py` + `audit-jar.py` diff; a batch import is where missing fields and stale packs hide.
- **Any change that would weaken `scripts/audit-jar.py`, delete state/history, or alter a public contract** — stop and record a human decision instead.

## Workflow

1. Work in an isolated branch or worktree. Do not push.
2. Choose the category: `development/` for implementation workflows, `systems-design/` for architecture or design guidance.
3. Put the skill at `<category>/<skill-name>/SKILL.md`. The folder name and frontmatter `name` must match, using lowercase letters, digits, and hyphens.
4. Keep the skill body concise. Use `references/`, `scripts/`, or `assets/` only when the skill truly needs bundled material.
5. Run `python scripts/sync-jar.py`. This is the only sanctioned way to touch
   the generated indexes, plugin manifests, agent packs, tracker, and usage
   queue. It runs `gen-index.py`, `gen-plugins.py`, `gen-agent-packs.py`, and
   appends tracker/usage rows in one pass. Do not hand-write or hand-paste any
   of those outputs, even if you believe you know the exact schema.
6. Read the FULL generated and state diff before committing -- every changed
   line, not a glance that it "looks well-formed":
   - `skills.json`
   - `docs/core-skills.md`
   - `.claude-plugin/marketplace.json`
   - `<category>/.claude-plugin/plugin.json` (a brand-new category, e.g. the
     first `systems-design/` skill, needs a new per-category manifest -- never
     assume it already exists)
   - `agent-state/SKILL_FORGE_TRACKER.md`
   - `agent-state/skill-usage.md`, if created or changed
7. Confirm the new `agent-state/SKILL_FORGE_TRACKER.md` row is queued for Skill
   Forge rather than marked forged. The tracker/usage queue is part of adding a
   skill, not a separate forge-loop concern to backfill later.
8. Run `python scripts/audit-jar.py` and confirm it exits 0. This is mandatory,
   non-negotiable, and applies under deadline. The audit is not a lint re-check
   and not an "entries exist / valid JSON" check: checks 6-8 run each generator
   with `--check`, which compares the generated files byte-for-byte against the
   layout. Hand-edited entries that are mis-sorted, missing `tags`/`core`, or
   leave `docs/core-skills.md` or the agent packs stale FAIL the gate even
   though they are valid JSON. "I already linted it elsewhere" does not cover
   index/plugin/pack sync.
9. Fix only the new skill or its directly bundled resources if the audit fails.
10. Commit the skill, generated files, and state together locally only after
    the audit exits 0. A local commit that has not passed the gate is not
    "done" -- "reversible in the morning" is not a substitute for a green gate
    tonight.

## Known pressure rationalizations

Closing each of these is mandatory. If you catch yourself reasoning along any
row, the response column is the required action.

| Rationalization (dodge) | Required response |
|-------------------------|-------------------|
| "It's just a file-copy task; the sync/gen/audit ceremony is overkill." | Adding a skill is reconcile + gate, not a copy. Steps 5-10 are mandatory regardless of how small the change feels. |
| "skills.json says don't edit by hand, but I know the schema; pasting matching entries reaches the same end state, so running the generator is redundant." | The generator sorts by `(category, name)` and the audit compares byte-for-byte. Hand-paste does not reach an identical end state. Run `sync-jar.py`; never hand-edit generated files. |
| "The SKILL.md files were already linted in the other repo, so the audit just re-checks clean work." | The audit's frontmatter lint is one of eight checks. Checks 6-8 verify index/plugin/pack SYNC, which prior linting cannot have covered. Run it. |
| "The audit basically verifies entries EXIST and the JSON is valid; my entries are valid JSON, so it passes." | False. The audit runs each generator `--check` for byte-exact equality. Valid JSON in the wrong order or missing fields fails. |
| "The tracker and usage queue are the forge loop's concern; I'll backfill SF rows later." | `sync-jar.py` appends the tracker/usage rows as part of adding the skill. They ship in the same commit; there is no "later." |
| "systems-design surely already has a plugin manifest like development does; I'll just add to marketplace.json." | Never assume a category manifest exists. The first skill in a category needs a new per-category `plugin.json`. Only `gen-plugins.py` (via sync) creates it correctly. |
| "git add -A then commit is fine; I can see the folders and JSON changed, no need to diff machine output." | Read the full generated diff (step 6). Stage only the files this task produced; `git add -A` plus an unread diff hides mis-generation. |
| "Committing locally is harmless and reversible; the point is it's in tonight." | A commit that has not passed `audit-jar.py` (exit 0) is not complete. The deadline does not waive the gate; ship it green or report blocked. |

When importing several skills at once, still run one `sync-jar.py` + one
`audit-jar.py` pass, but verify EACH skill individually in the step-6 diff
(naming, `tags`/`core`, category, sort position). A batch import is where
missing fields and stale packs hide.

## Drop-In Rules

- If the user already dropped a folder into the jar, preserve its content unless it violates jar naming, frontmatter, link, or safety rules.
- Do not hand-edit generated indexes, plugin manifests, agent packs, tracker,
  or usage queue at any point -- not before sync, not instead of sync, not "to
  match what the generator would emit." `sync-jar.py` is the only writer.
- Do not delete stale tracker rows or history while adding the new skill.
- Do not add hooks to ordinary `SKILL.md` files. Hook wiring belongs in repo-local agents or generated agent manifests.
- Stop and record a human decision if adding the skill requires changing public contracts, weakening `scripts/audit-jar.py`, deleting state/history, or guessing the category against user intent.
