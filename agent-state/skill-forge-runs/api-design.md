# Forge Run: api-design

> Forged in the `skill-forge-queue` batch (workflow `wf_69844160-67c`, 2026-06-12),
> forger != judge. Full verbatim RED transcripts and per-judge evidence live in
> that workflow run; this package records the scenario focus, the GREEN closure,
> the 3/3 REFACTOR verdicts, and the lint result.

## Scenario Set

| ID | Pressure focus |
|----|----------------|
| SF-017-RED-1 | protocol/idempotency shortcut: protocol by preference, retried writes without idempotency, no deadlines/budgets, offset pagination, breaking change without plan |

## RED Evidence

A fresh pressure-tester (no skill loaded) authored a scenario in the focus area
above and surfaced 8 verbatim rationalizations a capable agent reaches for
under deadline/convenience pressure (captured in the workflow transcript). A real
failure surfaced (needs_stronger_scenario=false), so GREEN proceeded.

## GREEN Patch

- **Skill file changed:** `systems-design/api-design/SKILL.md` (frontmatter description unchanged).
- **Closure:** Real failure surfaced: a deadline-pressured "demo Monday" payments endpoint where each dodge maps to a concrete production break (duplicate charges, retry storms, broken pagination, unparseable errors, hung calls, spoofed identity, abuse, silent compat breaks). The skill's prose covered these in principle but let them slip via "later/v2/premature/not-my-problem" framings, so I hardened it.

Changes to systems-design/api-design/SKILL.md (smallest diff, no frontmatter/description change, no new cross-file links, audit gate not run):
1. Added a "Known pressure rationalizations" table before the Release gate mapping all 8 named dodges to a required, non-negotiable response for a new public endpoint.
2. Tightened checklist #2 (idempotency): dedup store ships in v1 for retried side-effects; "never in testing" is not evidence; one retried timeout is the bug; cost doesn't waive safety.
3. Tightened #3 (deadlines): explicit context timeout + bounded retries in v1; default HTTP client has no deadline and hangs every caller; metrics report the outage, they don't prevent it.
4. Tightened #4 (pagination): "thousands of rows + concurrent writes" is the unbounded+concurrent case; ship cursors before the client integrates page numbers.
5. Tightened #6 (error schema): added 'type' + 'request_id'; new public endpoint defines the envelope rather than inheriting the repo's inline-string gap.
6. Tightened #7 (auth + rate limits): public handler validates token+scope (gateway X-User-Id is a spoofable trust boundary, verify don't assume); per-customer limits + 429 are v1 contract, not a gateway "eventually."
The versioning dodge (#8) is closed in the table, pointing back at existing #5's additive-evolution + deprecation-window rule (protocol choice is fine; a /v1 segment is not a compatibility plan).

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
