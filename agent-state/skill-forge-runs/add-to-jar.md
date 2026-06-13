# Forge Run: add-to-jar

> Forged in the `skill-forge-queue` batch (workflow `wf_69844160-67c`, 2026-06-12),
> forger != judge. Full verbatim RED transcripts and per-judge evidence live in
> that workflow run; this package records the scenario focus, the GREEN closure,
> the 3/3 REFACTOR verdicts, and the lint result.

## Scenario Set

| ID | Pressure focus |
|----|----------------|
| SF-022-RED-1 | drop-in skill: adding without sync/gen/audit, editing generated files by hand, importing many at once, committing without inspecting diffs, skipping the forge row |

## RED Evidence

A fresh pressure-tester (no skill loaded) authored a scenario in the focus area
above and surfaced 8 verbatim rationalizations a capable agent reaches for
under deadline/convenience pressure (captured in the workflow transcript). A real
failure surfaced (needs_stronger_scenario=false), so GREEN proceeded.

## GREEN Patch

- **Skill file changed:** `development/add-to-jar/SKILL.md` (frontmatter description unchanged).
- **Closure:** Patched development/add-to-jar/SKILL.md to close all eight named pressure rationalizations. Grounded the fixes in the actual toolchain: audit-jar.py checks 6-8 run gen-index/gen-plugins/gen-agent-packs with --check, and gen-index.py does a byte-for-byte string equality comparison (INDEX.read_text() != expected) on a list sorted by (category, name) with optional tags/core fields. So the dodges "hand-paste reaches identical end state" and "audit just checks entries exist / valid JSON" are factually refuted, not just discouraged. Changes: (1) tightened workflow step 5 to make sync-jar.py the only sanctioned writer of all generated/state files; (2) rewrote step 6 to require reading the FULL diff and flagged that a brand-new category (first systems-design skill) needs a new per-category plugin.json that must never be assumed to exist; (3) made step 7 state the tracker/usage queue is part of adding a skill, not a backfill-later forge concern; (4) made step 8 a mandatory exit-0 gate that applies under deadline and explained what the generator --check comparisons actually catch; (5) made step 10 require the audit to be green before commit, rebutting 'reversible in the morning'; (6) added a 'Known pressure rationalizations' dodge->required-response table covering all eight; (7) added a batch-import rule (one sync+audit pass but verify each skill individually) since the scenario imports four at once against a skill that says 'exactly one'; (8) tightened the Drop-In hand-edit rule from 'before running sync' to 'at any point -- sync-jar.py is the only writer'. Constraints honored: frontmatter description unchanged, no new cross-file Markdown links (filenames are in inline code only), edited only this skill's SKILL.md, did not run the audit gate, smallest diff that closes the named dodges.

## REFACTOR Verdicts

| Run | Verdict | Notes |
|-----|---------|-------|
| 1 | COMPLY | independent judge; named dodges refused by concrete rules + the pressure table |
| 2 | COMPLY | independent judge |
| 3 | COMPLY | independent judge |

3/3 clean -> forged.

## Lint Evidence

- **Command:** `python scripts/audit-jar.py`
- **Result:** GREEN over the full batch: 208 checks, 0 failed.
