# Guardrail Forge Handoff

Updated: 2026-08-31 America/Phoenix

## Release direction -- supersedes the certification NEXT ACTION

On 2026-08-31, the human directed this completed local implementation to be
committed, merged, and pushed without continuing the optional three-judge
certification loop. Ship it as built and integrated while retaining the honest
`reopened` / `0/3` forge label; do not claim that it is `forged`.

## Objective

Add the public, generic `development/guardrail-forge` skill to Skill Jar. It
discovers an unfamiliar repository read-only, separates observed/documented/
verified/approved/enforced architecture states, installs deterministic policy,
validators, fixtures, hooks, and CI only after human approval, and hands ongoing
detection to `arch-drift-watch`. MemBerry is optional discovery/provenance input;
the generated enforcement pack works without it. No proprietary Web Prodigies
source or rules are included.

## Git and safety state

- Repository: `C:\Users\Guerr\Desktop\skill jar`
- Branch: `feat/guardrail-forge`
- Commit: pending final feature-branch commit
- Push/merge: explicitly authorized on 2026-08-31 after commit-message approval
- Worktree: complete local skill addition awaiting commit
- Required final gate: `python scripts/audit-jar.py`
- Maker/checker rule: final status requires three fresh independent clean judges
- Current forge count: `0/3`; do not mark forged yet

## Current implementation

The working tree contains:

- `development/guardrail-forge/SKILL.md`
- discovery, policy-schema, project-pack, and validator-contract references
- `inspect-project.py`, `validate-policy.py`, and conflict-safe scaffolding
- a generated pack with policy/baseline/exceptions/decision/verification state,
  one canonical verifier, hooks, CI, host agents, loop state, and driver prompt
- generated Claude/Codex explorer, policy-maker, breaker, and verifier roles
- a runnable generated-pack adapter at
  `development/arch-drift-watch/scripts/watch-guardrail-pack.py`
- focused integration tests in `tests/test_guardrail_forge_scripts.py`
- synchronized jar/plugin/agent manifests and append-only forge state

The implementation closes the recorded path, symlink/junction, zero-rule,
approval, exact-waiver, duplicate-fingerprint, validator authority,
runtime/entrypoint, Git custody, cursor, rollback, ignored/tracked byte,
discovery-cycle, template-encoding, attached/composite argv, and scaffold-race
bypasses. The intentionally malicious already-approved validator/runtime case
remains explicitly documented as an OS/container sandbox boundary rather than a
portable enforcement claim.

## Current restart point

Fifteen fresh judge rounds after the reboot found real loopholes and reset the
count to `0/3`; their counterexamples and GREEN fixes are append-only in the two
forge run packages. The current fifty-sixth GREEN includes:

- an actual working-tree byte snapshot independent of Git index visibility hints;
- recursive authority discovery for standalone, assigned, response-file, and
  compact validator argv paths;
- symlink/junction-pruned read-only discovery;
- JSON/prose-safe project names, including POSIX surrogateescape values; and
- race-resistant exclusive scaffold writes using held Windows directory handles
  or POSIX no-follow directory descriptors;
- fail-closed terminal argv grammar for missing, response, encoded, and compound
  validator values;
- binding each protected scaffold write to the preflighted repository identity;
- a dated current loop-state section superseding the historical closed queue;
- single-pass first-delimiter argv parsing;
- hook/CI wrapper bytes bound into watcher authority;
- lexical symlink/junction checks before argv canonicalization;
- non-deleting late-write recovery that records earlier paths as unverified and
  blocks possibly partial files for review;
- Git-verified exact worktree-root validation;
- exact one-character compact-option parsing;
- explicit manual review for a possibly partial current destination;
- Git authority isolated from inherited `GIT_*` variables;
- one root identity bound across Git validation, preflight, and writes;
- missing punctuation-free `-I` paths rejected;
- bare `-I` and punctuation-free lexical link aliases rejected;
- generic compact-option link aliases and empty long-option values rejected;
- complete long-option names validated before delimiter consumption;
- a flushed apply-intent marker established before any destination write, plus
  a digest-bound completion record after all writes; and
- strict recovery path/content-hash schema with marker identity revalidated or
  safely restored across every destination and failure path; and
- descendant directory entries included in validator implementation authority;
- detected recovery custody loss persisted as a separate fail-closed record;
- per-destination containment failures routed through intent restoration;
- duplicate-key recovery JSON rejected;
- NTFS named streams bound into implementation and fixture authority;
- full-operation Windows root holding plus POSIX descriptor/ctime custody;
- watcher Git authority isolated from inherited `GIT_*` and bound to the exact
  sanitized worktree root; and
- working authority compared directly to raw HEAD blobs without clean filters,
  with exact raw hook/workflow bytes; and
- effective and committed watcher authority revalidated after cursor update,
  with rollback on any change.

Each new behavior has a focused executable regression. The full fifty-sixth
GREEN gate set passed. Three fresh judges are still required; treat every older
judge verdict as evidence for a previous revision.

## NEXT ACTION

1. Run, in order:

```text
python -m unittest tests.test_guardrail_forge_scripts -v
python -m unittest discover -s tests
python scripts/audit-jar.py
python C:\Users\Guerr\.codex\skills\.system\skill-creator\scripts\quick_validate.py development\guardrail-forge
git diff --check
```

2. Launch three fresh read-only judges against the exact post-gate diff. Any
   loophole resets the count to `0/3`; do not reuse an earlier clean verdict.
3. Only after 3/3 clean verdicts, update SF-029 `guardrail-forge` and SF-001
   `arch-drift-watch` to forged, add final judge/gate evidence and a completion
   row to loop state, rerun the jar audit, and remove generated `__pycache__`
   directories. Do not push. Do not commit unless the user explicitly requests
   it; if committing, code and state must be one local commit.

## Current fifty-sixth-GREEN gates

- Focused tests: 49/49 passed
- Full suite: 90/90 passed
- Jar audit: 299/299 passed
- Skill quick validator: passed
- `git diff --check`: passed

These results cover the current argv, pre-write recovery, and held-root fixes. The
earlier incomplete and failed focused attempts remain excluded.

## Disk recovery performed

The test/judge runs filled C:. Cleanup was limited to regenerable artifacts:

- disposable named test/probe directories under `%TEMP%`
- generated repository `__pycache__` directories
- pip cache (about 1 MB)
- npm cache at `C:\Users\Guerr\AppData\Local\npm-cache` (about 1.90 GB)

The npm and pip caches are recoverable by normal package downloads. No projects,
dependencies, personal files, commits, or remote state were deleted. After the
recovery agent stopped and cleanup settled, C: reported about 9.9 GB free.

## Important files

- `development/guardrail-forge/SKILL.md`
- `development/guardrail-forge/scripts/validate-policy.py`
- `development/guardrail-forge/assets/guardrail-pack/scripts/architecture/verify.py`
- `development/arch-drift-watch/scripts/watch-guardrail-pack.py`
- `tests/test_guardrail_forge_scripts.py`
- `agent-state/skill-forge-runs/guardrail-forge.md`
- `agent-state/skill-forge-runs/arch-drift-watch.md`
- `agent-state/SKILL_FORGE_TRACKER.md`
- `agent-state/failed-attempts.md`

## Skills and boundaries

The work followed `skill-creator`, `loop-engineer`, and, only for the disk-space
incident, `cleaner-safe-cleanup`. The Cleaner repo expected by that skill was not
present, so cleanup used explicit verified cache/test targets only. The final
public skill remains generic; the proprietary starter kit was inspected only to
extract high-level design lessons.
