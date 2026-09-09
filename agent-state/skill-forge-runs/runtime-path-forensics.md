# Skill Forge Run: runtime-path-forensics

## RED evidence

The no-skill evaluator reached the correct bounded conclusion. Its response did
not provide stable record or hop IDs, typed correlation edges, interval timeline
records, explicit strength on each evidence item/edge/hop/conclusion, alternatives
for each hop, or operator-ready discriminator owner, access, and cost fields.

Those observed omissions are the captured RED behavior. No additional failure or
unseen rationale is attributed to the evaluator.

## GREEN behavior

`development/runtime-path-forensics/SKILL.md` defines a read-only forensic
workflow for one bound operation. It keeps desired deployment state separate
from historical process and loaded-artifact identity, preserves retry/delivery/
execution nodes, constructs qualified correlation edges and partial-order clock
intervals, and treats missing events as conditional negative evidence.

The canonical report requires stable referenced IDs, the ten ordered tables,
exact enums, explicit per-record strength, weakest-link promotion, per-hop gaps
and alternatives, causal limits, and safe discriminator records with exact
query, scope, permission, cost, timeout, signals, privacy, side effects,
limitations, and owner.

## Independent evaluation

- Independent clean runs: `3/3`.
- Split-brain identity judge: `JUDGE VERDICT: COMPLY`.
- Retry and clock-ordering judge: `JUDGE VERDICT: COMPLY`.
- Missing-log negative-evidence judge: `JUDGE VERDICT: COMPLY`.
- Schema promotion check: `JUDGE VERDICT: COMPLY`.
- Final acceptance: `ACCEPTANCE VERDICT: PASS`.

The implementer was not a judge.

### Raw response custody

| Response | SHA-256 |
|---|---|
| `clean-room/evaluator-responses/red.md` | `5d966a99bdd553243e1a9b313c12cc3f535d6444ffb34e37566955a63e3f935a` |
| `clean-room/evaluator-responses/split-brain.md` | `55a58a165941647728eb995a3da86216beca5b89a16c098222928a8eb92334b4` |
| `clean-room/evaluator-responses/retry-clock.md` | `c05d6674901c202d583f3a6549f9169a82059167f2749f91acf5def6e2b6e797` |
| `clean-room/evaluator-responses/missing-log.md` | `65e4e6a7fe83cbee9e79a3077fd1489f2d08707ed42243b1017fc8071962e7c2` |
| `clean-room/evaluator-responses/schema-promotion.md` | `4fd8f2734d77eb829c6aee13b7a6619acefb7fb53a9311d66ba3b3ec6656da1e` |
| `clean-room/evaluator-responses/acceptance.md` | `c78dfda4f37f1c37741c3bd32b1c387b78458d2ff22e8e0616886e954a916ea9` |

## Local gates

- Global skill quick-validator: PASS (`Skill is valid!`).
- Unit suite: PASS (91 tests).
- Jar audit: PASS (329 checks, 0 failed).
- Diff check: PASS (exit 0; line-ending warnings only).
- Allowlist: PASS (11 changed paths, 0 violations).
- Added-content contamination scan: PASS (0 prohibited identifier matches).
- Protected-input verification: PASS (9 files matched the anchored manifest).

## Certification state

- Status: `forged`.
- Clean runs: `3/3`.
- RED evidence, all three current-revision scenario judges, schema promotion,
  final acceptance, and every local gate are complete.
