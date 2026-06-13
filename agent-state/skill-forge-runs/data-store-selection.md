# Forge Run: data-store-selection

> Forged in the `skill-forge-queue` batch (workflow `wf_69844160-67c`, 2026-06-12),
> forger != judge. Full verbatim RED transcripts and per-judge evidence live in
> that workflow run; this package records the scenario focus, the GREEN closure,
> the 3/3 REFACTOR verdicts, and the lint result.

## Scenario Set

| ID | Pressure focus |
|----|----------------|
| SF-018-RED-1 | brand-choice/shard-key: store by brand before patterns, unjustified/monotonic shard key, unnamed consistency, cache without invalidation, queue without DLQ owner |

## RED Evidence

A fresh pressure-tester (no skill loaded) authored a scenario in the focus area
above and surfaced 8 verbatim rationalizations a capable agent reaches for
under deadline/convenience pressure (captured in the workflow transcript). A real
failure surfaced (needs_stronger_scenario=false), so GREEN proceeded.

## GREEN Patch

- **Skill file changed:** `systems-design/data-store-selection/SKILL.md` (frontmatter description unchanged).
- **Closure:** Real failure surface confirmed: the skill held the right gates (shard-key justification, named consistency, queue/cache contracts) but did not defeat the time-pressure deferral and "it's just X / we'll harden later" dodges, so a fresh agent could pass them while technically gesturing at the gates. Patched systems-design/data-store-selection/SKILL.md with the smallest diff: (1) tightened the five existing hard gates so each named dodge becomes a hittable reject -- ObjectId/default-unique and "reshard later" rejected on the shard-key gate, "Mongo gives consistency" rejected unless read/write concern + stale-read tolerance are named, "invalidation falls out naturally / TTL later" rejected on the cache gate, "it's just notifications" requires an explicitly named at-most-once contract + retry owner + DLQ; (2) added a new hard gate rejecting any deferral to "later/post-demo/before real funds flow," stating money applies on the first commit and fake demo data doesn't lower the bar; (3) added a "Known pressure rationalizations" table (9 rows) mapping every named dodge to its required response, including the "don't overthink it = blocker" and "popular/incumbent = safe" pressure framings. Frontmatter description untouched (no skills.json desync); no new cross-file links; only this SKILL.md edited; audit gate not run per instructions.

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
