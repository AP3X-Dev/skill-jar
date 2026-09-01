---
name: guardrail-forge
description: "Use when an unfamiliar established repository needs a project-specific architecture enforcement pack: discover actual boundaries read-only, classify evidence without mistaking prevalence for intent, stop on conflicts, then after human approval generate and pressure-test deterministic validators, exact baselines/exceptions, hooks, CI, and a handoff to arch-drift-watch. MemBerry can enrich discovery but is never required for enforcement. NOT for deciding product architecture from scratch, a one-off architecture review (use improve-architecture), or continuing drift detection after installation (use arch-drift-watch)."
---

# Guardrail Forge

Turn evidence from an unfamiliar repository into a project-owned architecture
enforcement pack. The forge is finite: it discovers, drafts, waits for approval,
installs in an isolated worktree, pressure-tests, verifies a canary, and hands the
accepted policy to [arch-drift-watch](../arch-drift-watch/SKILL.md). The watcher
then detects future drift; it does not rerun this bootstrap.

## Operating contract

Run the forge in two gates, never as one uninterrupted mutation:

1. **Level 1 discovery is read-only.** Produce an evidence map, candidate rules,
   coverage gaps, and decision items. Do not create enforcement files in the
   target repository yet.
2. **Level 2 installation requires explicit human approval.** Only approved
   rules may become blocking validators. Install them on one task branch in an
   isolated worktree, then use a separate breaker and verifier.

Repeated code is `observed`, documentation is `documented`, and current source,
tests, or runtime evidence may make a rule `verified`. None of those states is
human approval. A rule becomes `approved` only through a recorded decision and
`enforced` only after its deterministic validator and adversarial fixtures pass.
Conflicting evidence becomes a decision item; never resolve it by majority vote.

Read [references/discovery-protocol.md](references/discovery-protocol.md) before
examining a target. Read [references/policy-schema.md](references/policy-schema.md)
before drafting the manifest. Read
[references/validator-contract.md](references/validator-contract.md) before
authoring or judging validators. Read
[references/project-pack.md](references/project-pack.md) when installing the pack,
wiring a host, or handing off to drift detection.

## The finite loop

### 1. Recover and bound the run

- Read every applicable `AGENTS.md`, `CLAUDE.md`, repository rule, and existing
  architecture state file before inspecting code.
- Record the base commit, target branch, allowed paths, existing gates, host, and
  autonomy level. Start at Level 1.
- Keep the target tree read-only during discovery. Use
  `python <skill>/scripts/inspect-project.py --root <repo>` as an inventory aid,
  not as an architecture oracle.
- If the target has uncommitted work or a prior in-flight forge packet, recover
  that packet before starting a new one.

### 2. Discover actual architecture

Use explorer agents read-only. Cover package topology, entry points, request/data/
event paths, persistence and tenancy, authn/authz, public APIs, integration seams,
dependency direction, existing tests/lint/typecheck/build/CI, scoped instructions,
ADRs, and relevant history. Prefer source, executable checks, and runtime wiring
over prose while keeping the evidence types distinct.

Optional sources:

- **MemBerry:** symbols, dependency edges, aspects, impact/blast radius, drift,
  decisions, exceptions, failed approaches, PR impact, and provenance.
- **FUGAZI or another configured structural analyzer:** boundaries, cycles,
  duplicates, complexity, and machine-readable dependency evidence.
- Existing production/runtime evidence.
- **A greenfield handoff:** `docs/architecture/` (constitution, ADRs,
  `07-guardrail-candidates.md`) and `.architecture-seed/architecture-seed.yaml`
  from [greenfield-architecture](../../systems-design/greenfield-architecture/SKILL.md),
  plus per-decision candidates from
  [architecture-decision-loop](../../systems-design/architecture-decision-loop/SKILL.md).
  These are documented/approved-state evidence with a decision ID, never
  pre-enforced rules; the skeleton source must still corroborate them.

These sources improve discovery; none may silently approve a rule, exception, or
baseline. The committed pack must validate when MemBerry and other optional
services are offline.

### 3. Classify and decide

Give each candidate exactly one current state:

| State | Meaning |
|---|---|
| `observed` | A pattern exists in current code. It may be debt. |
| `documented` | Instructions or architecture prose claim it. |
| `verified` | Current source/runtime/tests prove the behavior and intended seam strongly enough to propose policy. |
| `approved` | A human architecture owner accepted the exact statement and scope. |
| `enforced` | The approved rule has a deterministic validator, positive and negative fixtures, and independent verification. |

When evidence conflicts, append a stable `BLOCKED-NNN` item to the run's
`decisions.md` with the exact sources, options, blast radius, and recommended
smallest decision. Continue other read-only discovery; do not install the
conflicted rule.

### 4. Draft the candidate pack

Draft outside the target tree or on a discovery-only branch. Every rule needs a
stable ID, statement, exact scope, state, severity, typed evidence, provenance,
remediation, and—only when enforced—a command plus positive and negative
fixtures. Approval-bearing states require a decision ID, approver, and timestamp.

Validate the draft with:

```text
python <skill>/scripts/validate-policy.py --root <repo> --policy <policy> --baseline <baseline> --exceptions <exceptions> --decisions <decisions> --verification <verification>
```

Validation proves schema integrity, not architectural truth. Present the
candidate report and decision packet to the human. Stop at Level 1 until the
human approves exact rules and scope.

### 5. Install approved rules

After approval, create one worktree/branch for the installation packet. Preview
the generic skeleton, then apply it:

```text
python <skill>/scripts/scaffold-guardrail.py --repo <worktree> --host both
python <skill>/scripts/scaffold-guardrail.py --repo <worktree> --host both --apply
```

The scaffolder is conflict-safe and never overwrites. Adapt only dedicated pack
files unless the human approves a managed edit to existing agent settings or
instructions. Use one canonical command everywhere:

```text
python scripts/architecture/verify.py
```

Local hooks, agent hooks, and CI may wrap this command but may not implement a
different or weaker policy. Preserve all existing repo gates.

### 6. Pressure-test each validator

The policy maker never approves its own rule. Use four isolated roles:

| Role | Responsibility |
|---|---|
| Explorer | Read-only evidence and conflict map. |
| Policy maker | Converts approved decisions into the smallest candidate validator. |
| Breaker | Attempts realistic bypasses and gate tampering. |
| Verifier | Re-runs fixtures, canary, hooks, CI-equivalent command, scope gate, and existing repo gates; may reject. |

Every enforced rule needs at least one valid fixture and one violating fixture.
The breaker must also try re-export laundering, renamed imports, alternate entry
points, file relocation into excluded paths, suppression comments, wildcard or
directory exceptions, copied baseline fingerprints, skipped checks, validator or
workflow deletion, and changing application code and its validator together.

Capture RED with the validator frozen, then GREEN against the same bytes and
configuration. A canary that edits both the violating application path and the
validator is not proof. Validator/policy changes require their own checker and
negative-control run. Every validator declares a dedicated implementation root; the
verification record binds those bytes and all fixture bytes. A later edit makes
the pack invalid until a separate breaker/verifier run refreshes the record.

### 7. Baseline and exceptions

- A baseline records exact approved legacy violation fingerprints. It does not
  authorize a pattern. No wildcards, directory exemptions, counts, or silent
  regeneration.
- The canonical verifier is read-only and exposes no baseline-write mode.
  Baseline changes are a separate human-approved task with diff review.
- An exception names one rule and exact path/symbol, plus owner, reason,
  decision ID, approval time, and expiry or removal condition.
- New, changed, copied, expired, stale, malformed, or incompletely scanned items
  fail closed according to the validator contract.

### 8. Verify, record, and hand off

The separate verifier must run the canonical verifier, positive/negative
fixtures, a realistic canary, target repo gates, and a diff scope check. Empty,
missing, or erroring suites fail. Record command output and hashes in the
verification ledger. Update state before any local commit; commit policy,
validators, fixtures, workflow, hook, and state together. Never push or merge.

On a clean Level 2 close, hand `.architecture/policy.yaml`, baseline, exceptions,
decisions, verification, authority digest, and the canonical verifier to
`arch-drift-watch`. Initialize the generated adapter only with the approved
handoff decision after every authority-bearing file is tracked and unchanged
from `HEAD`, then schedule `python scripts/architecture/watch_guardrail.py`.
The watcher returns every active finding while using an operational cursor only
to label new, persisting, and resolved findings; cursor edits can never make an
active violation pass. It never treats that cursor as a second policy baseline,
advances the approved baseline silently, or redesigns policy.

## Known pressure rationalizations

| Rationalization | Required response |
|---|---|
| "All rules should be blocking in v1; warning states only add ambiguity." | Discovery is not approval. Keep observed/documented/verified candidates non-blocking until a human decision is recorded. |
| "Evidence paths are enough provenance for an enforced rule." | Evidence supports a proposal. Enforced rules also require approval identity, decision reference, exact scope, fixtures, and independent verdict. |
| "A `--write-baseline` mode is safe after extraction succeeds." | Successful extraction proves mechanics, not acceptance. The canonical verifier is read-only; baseline updates are separate approved changes. |
| "The legacy directory can be baselined so CI starts green." | Baseline exact fingerprints only. Directory or wildcard baselines launder future violations. |
| "The validator and violating code can change together; the final green diff is the canary." | Freeze validator bytes for RED→GREEN or use independent fixtures/negative control. A self-validating combined diff is not proof. |
| "The hook can be faster than CI by checking less." | One canonical verifier defines policy. Performance modes may change scheduling, never semantic coverage or pass criteria. |
| "MemBerry already knows the architecture, so approval can be inferred." | Memory is discovery evidence and provenance, never authority. Deterministic files and human decisions remain required. |

## When to stop

Stop and record a decision instead of guessing when architecture evidence
conflicts, ownership is unknown, extractor coverage is incomplete, an exception
or baseline lacks approval, a validator cannot fail on its negative fixture, the
same maker is the only checker, an existing gate would need weakening, or the
change would alter a public API, schema, on-disk format, security boundary, or
cost boundary.

## When NOT to use

- Designing greenfield product architecture; use
  [greenfield-architecture](../../systems-design/greenfield-architecture/SKILL.md),
  which hands its bootstrap repo back here for Level 1 discovery.
- A one-shot architecture assessment or refactor decision; use
  [improve-architecture](../improve-architecture/SKILL.md).
- Continuing detection after a pack exists; use
  [arch-drift-watch](../arch-drift-watch/SKILL.md).
- General code hardening without an architecture-policy deliverable; use
  [optimization-loop](../optimization-loop/SKILL.md).

Generated jar roles live in [../agents/README.md](../agents/README.md) and are
sourced from [../agents/manifest.json](../agents/manifest.json). Install only
`guardrail-explorer`, `guardrail-policy-maker`, `guardrail-breaker`, and
`guardrail-verifier` for an active forge run.
