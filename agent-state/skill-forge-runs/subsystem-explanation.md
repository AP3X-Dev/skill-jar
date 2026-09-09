# Skill Forge Run: subsystem-explanation

## Scope and custody

- Forge item: SF-037
- Skill: `development/subsystem-explanation/SKILL.md`
- Worktree: `C:\Users\Guerr\Desktop\skill-jar-subsystem-explanation`
- Branch: `feat/subsystem-explanation`
- Base: `cec23b5`
- Mode: full clean-room; no external source was available to the maker or shipped artifacts.

## RED evidence

The production-selection response respected the broad proof boundary but returned
only prose. It had no bound revision, stable claim IDs, evidence locators, typed
variants, trace/effect records, or machine-checkable promotion relationship.

The outbox response explicitly admitted that relay, acknowledgement, retry, and
idempotency nodes were assumptions, yet drew them as continuing flow. A prose
caveat did not remove the diagram's factual implication.

These observed failures are the reasons for the typed explanation package,
composition-first selection proof, and diagram gap rule. No other RED behavior
is attributed to the pressure testers.

## GREEN and hostile review

The first two protected-design reviews rejected underspecified claims,
selection, diagrams, identities, proof promotion, verdicts, references,
contradictions, discriminators, effectless paths, optional tables, and boundary
semantics. A third review passed after those contracts were made exact.

The first GREEN schema audit then rejected missing worktree identity, an enum
mismatch, untyped contradiction subjects, loose identity/time encodings,
underpowered contradiction resolution, and unknown foundational bindings. The
maker repaired those exact defects before certification.

## Current-revision REFACTOR evidence

| Run | Pressure | Result | Bound response SHA-256 |
|---|---|---|---|
| 1 | documentation, conditional wiring, mock, and missing production identity | 5/5 COMPLY | `cee43bb0b56f53f3134edb0648c7bba6b7a6b3fc4d1a5ba0fb3af203530db2e6` |
| 2 | transaction, outbox publisher, retry, idempotency, failures, and diagram gaps | 5/5 COMPLY | `86a167fa32b1d19690786c0de7cd4422f0d853625671f508fcfc6180c41ebd05` |
| 3 | effectless result path and unavailable generated registration | 5/5 COMPLY | `b790925ba3825d6a111d793626fbc4fd0949e12a43612b0ddd3def5a07c669a9` |

The maker was not a judge. Each judge reread the current skill and revised
identity-bound scenario, made no edits, and returned no new loophole.

## Schema and acceptance

- Schema/promotion: 6/6 COMPLY; response SHA-256
  `728db6545994ba99ed848c546c77cd093764db4de41f52e9dea574ff8055aea4`.
- Final acceptance: 16/16 PASS; response SHA-256
  `e5fea0921fcef397c3232fbfdc269649b53a6b064fc4264c9a2c6b1d4c1abfcc`.
- Protected design SHA-256:
  `cc42e88687164f215c500f52487fbbfe42f4bc83d50070f245a3b342c65b1f3d`.
- RED response SHA-256 values:
  `1321641c42c1bdea0f9b637a238d37413f7145dceb6db86e50f95f064c2b5c69`,
  `1faea5e71718b215a908119f5d9443a446b3d585859e7c60aef9afe66cd6859b`.
- Current scenario SHA-256 values:
  `3c181706be5a581015e5f23a305e69ccbd466329b314b4130b416cd93f7bc76b`,
  `fb0313d99bee827d09f46cdcab3a149a0bb662a983bcf884bc7b90358ba0dcfc`,
  `9c51d078d48035df6c42de213d46ea71f131aec0b60f8399784f51e65b17bf8f`.
- Shipped skill SHA-256:
  `e6fbed52434683d32eb088ba8ed9e680bdd1294f7f13381fabdd42c6d94f64d9`.

## Runnable gates

- Global skill quick validator: PASS.
- `python -m unittest discover -s tests`: 91 passed.
- `python scripts/audit-jar.py`: final state closeout passed 339 checks, 0 failed.
- `git diff --check`: exit 0; line-ending warnings only.
- Changed-path allowlist: PASS for the eleven task paths.
- Nine protected gate inputs: unchanged from base and SHA-256 captured.
- Change-surface contamination scan: PASS, zero prohibited identifier matches.

Certification is `forged` at 3/3; the final state audit exited 0.
