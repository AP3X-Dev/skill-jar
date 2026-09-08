---
name: change-impact-proof
description: "Use when determining what a proposed or completed code change can affect beyond its edited lines, investigating downstream breakage, or proving a small diff safe with executable evidence. Produces traced impact paths, decisive assurances with explicit evidence states, and a bounded safety verdict. NOT for broad multi-lens review, root-cause repair, architecture design or enforcement, production readiness, continuous drift detection, or implementation."
---

# Change Impact Proof

Determine whether a specific change is safe at the boundary that matters. Trace
effects beyond the diff, turn the safety case into falsifiable assurances, and
acquire evidence aimed at those assurances. A green build is useful only for
the behavior it actually exercises.

## Operating contract

This is read-only analysis. Do not edit code or state, update generated files,
commit, push, deploy, message people, or mutate a hosted or production system.
Implementation requires a separate user request. Preserve unrelated dirty
worktree changes and distinguish fixture, local, hosted, live, and production
evidence throughout.

Before running a command, classify its expected side effects. Do not run it if
it may update tracked artifacts, snapshots, fixtures, lockfiles, schemas,
shared databases, external services, or production data without separate
authorization. Prefer read-only repository gates and checks through real
consumer paths.

## 1. Bind the question

Record:

- **Comparison base:** resolved commit, branch, release, or explicit current
  state. Do not silently assume the default branch or a clean worktree.
- **Target change:** resolved diff and changed files/symbols/contracts. For a
  proposed change without a diff, use the named files, symbols, contracts, and
  intended edits as prospective change units. If those units are not concrete
  enough to trace, return `blocked by missing evidence`.
- **Intended behavior:** what should change, what must remain invariant, the
  affected users/consumers, and the evidence boundary requested (for example,
  local or a named running environment).

Inspect both sides of the comparison safely. If a gate fails, compare against
the base where practical and label the failure `baseline`, `change-specific`,
or `unresolved`; never charge an existing failure to the change without that
comparison.

## 2. Trace complete reachable impact paths

Start at each changed or proposed unit and follow every relevant direct and
indirect path until it reaches an observable consumer or an evidence-backed
stop. Do not stop after the first obvious caller. For every path, record:

| Field | Required content |
|---|---|
| Origin | Changed file, symbol, configuration, schema, or contract |
| Ordered hops | Calls, imports, events, transforms, registrations, or generated steps in order |
| Boundary types | Code, data, persistence, schema, protocol, configuration, lifecycle, timing, dependency, or generated artifact |
| Observable consumer | User, service, job, client, stored record, emitted message, or operational effect |
| Reachability evidence | The source, registration, configuration, execution, or observation proving the path can run |
| Effect or stop | Observed effect, or the evidence-backed reason propagation stops |

Check only boundaries relevant to the change, but explicitly consider all of
these before ruling them out:

- callers, implementations, adapters, event consumers, background work, error
  paths, cleanup, startup/shutdown, caches, retries, timing, concurrency, and
  ordering;
- serialized data, persistence, migrations, schemas, protocol compatibility,
  configuration, secrets/permissions, feature flags, and non-default branches;
- dynamic dispatch, reflection, registries, plugins, generated bindings, and
  code generation. These require registration or runtime evidence appropriate
  to the path; a plain text search is insufficient;
- generated files in both directions: authoritative source -> generated output
  -> consumers. Do not treat a generated file as its own authority;
- third-party behavior against the pinned version and local patches. If the
  relevant implementation is not available, leave it unknown.

A negative search is evidence only within its recorded scope and method. It
may narrow a path; it cannot by itself prove that no consumer exists.

For authorization or isolation boundaries, happy-path execution is not enough.
Require the applicable denial, cross-scope, inactive-account, and unauthorized-
path evidence. For timing, concurrency, cleanup, cache, or retry changes,
exercise lifecycle and ordering when practical; otherwise keep those assurances
open.

## 3. Define decisive assurances before verification

Express the safety case as the smallest set of falsifiable claims whose truth
would justify the verdict. For each decisive assurance, declare:

- the claim and the impact paths it covers;
- what observation would falsify it;
- its minimum evidence state and why that state is necessary;
- the planned check and its environment;
- the acquired evidence, state, and limitations.

Assign each assurance exactly one state:

| State | Exact meaning |
|---|---|
| `unsupported` | No assurance-specific evidence exists. |
| `source-supported` | Current repository source or pinned dependency source establishes the assurance without execution. |
| `executed` | An assurance-specific command exercises the affected path. |
| `runtime-observed` | The effect is observed in a running environment. Name that environment. |

Behavioral safety requires `executed` by default. A claim about a named running
environment requires `runtime-observed` there. Use `source-supported` as the
minimum only when execution cannot materially strengthen that particular claim,
and state why. Evidence below the declared minimum is a decisive gap.

## 4. Acquire targeted evidence

Prefer existing repository gates, then add the cheapest read-only real-path
check that directly exercises each assurance. Re-run the relevant command in
the current analysis; do not accept a reported green suite as current proof.
Compilation, type checking, and unrelated passing tests establish only their
own limited properties.

For every command or observation, report:

- exact command or observation;
- environment and evidence boundary;
- assurance and impact path exercised;
- result and limitation;
- side-effect classification.

If the required runtime is unavailable, keep the assurance below
`runtime-observed`, name the exact live observation still required, and let its
declared minimum state determine the verdict. Never promote fixture or local
evidence to hosted, live, or production proof.

## 5. Derive the verdict

Use only these verdicts:

- `not supported`: a decisive assurance is falsified or the demonstrated risk
  is unacceptable.
- `blocked by missing evidence`: required decisive evidence is unavailable or
  an assurance remains below its declared minimum.
- `supported with gaps`: every decisive assurance meets its minimum, but
  non-decisive unknowns remain.
- `supported`: every decisive assurance is satisfied with complete evidence at
  the requested boundary and no relevant unknown remains.

Do not average assurances or let many weak checks compensate for one decisive
gap.

## Output contract

Lead with the verdict, then report:

1. scope: base, target, intended behavior, consumers, and requested boundary;
2. changed behavior;
3. impact paths using the six required path fields;
4. decisive assurances, minimums, evidence states, commands/observations, and
   limitations;
5. confirmed risks, cleared concerns, unverified hypotheses, and missing or
   unknown evidence;
6. the cheapest remaining high-signal check.

Each confirmed risk names its reachable mechanism, affected consumer,
likelihood, consequence, and evidence. Each cleared concern names the evidence
that refuted it. Keep unverified hypotheses separate from both. If requested,
hand findings to broad review, diagnosis/repair, architecture, readiness, or
continuous-drift workflows; do not perform those jobs here.

## Pressure defenses

| Deadline rationalization | Required response |
|---|---|
| "The suite was reported green, so rerunning a targeted check is redundant." | Reported success is not current assurance-specific evidence. Re-run the smallest authorized check that exercises the affected path, or leave the assurance below its minimum. |
| "The first obvious consumer is safe, so the small diff is safe." | Finish every relevant reachable path through indirect, dynamic, generated, configuration, dependency, and lifecycle boundaries before deriving the verdict. |
