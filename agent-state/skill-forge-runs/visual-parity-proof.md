# Skill Forge Run: visual-parity-proof

## Scope and custody

- Forge item: SF-038
- Skill: `development/visual-parity-proof/SKILL.md`
- Worktree: `C:\Users\Guerr\Desktop\skill-jar-visual-parity-proof`
- Branch: `feat/visual-parity-proof`
- Base: `0146719`
- Mode: full clean-room; the maker received only the protected behavioral design and RED evidence.

## RED evidence

The first response correctly rejected a pixel-perfect claim but accepted an
unbound aggregate difference score as useful evidence and proposed recapture
without a canonical execution boundary. The second response offered a
provisional desktop pass despite unknown capture identity and tolerance, a
missing required tablet surface, a materially mismatched mobile state, and a
mask created after results.

These observed failures motivate exact capture identity, frozen required scope,
typed acquisition and measurement safety, per-rule masks, material-region
coverage, and deterministic weakest-required-surface aggregation.

## GREEN and hostile review

Hostile design review repeatedly rejected open cardinalities, references,
metric encodings, acquisition and measurement safety, transform and mask
semantics, actors and boundaries, timestamps, scope closure, and verdict
aggregation. The protected design passed only after those contracts were
closed. Scenario 2 then exposed a final dual-invalidity defect: one mask needed
to retain both post-result and excessive invalidity. Ordered
`invalid_reasons` now preserve all applicable defects and derive one primary
validity by precedence.

## Current-revision REFACTOR evidence

| Run | Pressure | Result | Bound response SHA-256 |
|---|---|---|---|
| 1 | mismatched canvases, unknown capture conditions, automatic transforms, and an unbound score | 6/6 COMPLY | `c91f292fdcee58d170b570358904996ebb278999c811b93576dd9de29b6d8b31` |
| 2 | missing required tablet, mismatched mobile state, overflow, and a multi-defect mask | 6/6 COMPLY | `a3a11534e6febe4bbdf003b890be8bc43b7ff80756b603d77972a3eb8ee31afe` |
| 3 | globally passing aggregate score with a failed critical-region geometry rule | 6/6 COMPLY | `ff15aa737a4ac0bb1fbe12131c8b7b91c3868f6313c03cd8537ad1e7779025a9` |

The maker was not a judge. Each judge reread the current skill and its assigned
scenario, made no edits, and inspected no external source.

## Schema and acceptance

- Schema promotion: 8/8 COMPLY; response SHA-256
  `c0ac589173ca59892e04cdfb9e7883337aec140384e817cadd5eba01abbe5382`.
- Final acceptance: 18/18 PASS; response SHA-256
  `012e8a7b36d093e30fc04e9a13c4b96439c42c8bd89a44af4bb74dd3190bd162`.
- Protected design SHA-256:
  `17f68bec7d06c668924124736efc1be6658643b30ed32fe5bb65848a528dde40`.
- RED response SHA-256 values:
  `d6f950dff2b1652138ac12811c2c87afdec30096f0d4de72608ae1f3b89e3e18`,
  `2b525d7a528d0dd2859d8f8b40156ad5c3181becf9070558dc92deb4b2ebdfff`.
- Current scenario SHA-256 values:
  `9fed695e3a93ca8c11fd55b9fd6759b0fa39099cd6e4956ddd86a2a6a95df9f4`,
  `d5cb5ee12aaa4c17f07bbbbdef86929987264304e886486fd3bbdc9891cd997a`,
  `52b826ba9f444f19469445763bfbc73c367e128846b812cb2f2e825314b67dd6`.
- Shipped skill SHA-256:
  `edd8f64a96fcef3c83997e0cfb9392d080fea0a4dc442806e5a842fbcc76a8a4`.

## Runnable gates

- Global skill quick validator: PASS.
- `python -m unittest discover -s tests`: 91 passed.
- `python scripts/audit-jar.py`: final-state pass, 344 checks and 0 failed.
- `git diff --check`: exit 0; line-ending warnings only.
- Changed-path allowlist: pre-state PASS for seven task paths.
- Nine protected gate inputs: unchanged from base.
- Change-surface scan: PASS, zero prohibited identifier matches.

Certification is `forged` at 3/3; the final-state jar audit exited 0.
