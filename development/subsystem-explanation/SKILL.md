---
name: subsystem-explanation
description: "Use when explaining how one bounded repository subsystem, request path, job lifecycle, or implementation flow actually works. Produces a read-only, evidence-bound account of composition, control and data flow, state and effects, variants, failures, contradictions, and proof limits. NOT for impact analysis, incident diagnosis, runtime-instance forensics, architecture redesign, implementation work, or generic documentation rewriting."
---

# Subsystem Explanation

Explain one bounded subsystem from evidence a maintainer can follow. Distinguish
what is declared, what source can execute, what composition selects, what tests
exercise, and what supplied runtime observations establish. Never turn a likely
path into a proven path by smoothing over a missing edge.

## When not to use

- For downstream change impact, use
  [change-impact-proof](../change-impact-proof/SKILL.md).
- For incident root-cause work, use [diagnose-loop](../diagnose-loop/SKILL.md).
- For reconstructing the instance that handled one operation, use
  [runtime-path-forensics](../runtime-path-forensics/SKILL.md).
- For architecture redesign, use the appropriate design or architecture skill.
- For implementation, editing, or general documentation cleanup, use the normal
  workflow for that task.

## Read-only operating boundary

This skill inspects and explains; it does not change the repository or any
external system. Do not edit code or documentation, stage files, switch or
rewrite Git state, install dependencies, start services, run migrations, write
to a database or queue, send network requests, or query hosted telemetry,
services, databases, or control planes.

Runtime material is supplied-only for this invocation. Analyze runtime evidence
the user already supplied or explicitly placed in scope, but do not collect new
runtime evidence. Represent a useful future read as a bounded Discriminator and
stop. A command is not read-only merely because its usual purpose is inspection;
classify it by semantic effect before proposing it.

## 1. Bind the question and proof target

Record the exact question, audience, canonical repository root, Git revision,
worktree, subsystem slice, environment, requested truth boundary, and current
RFC 3339 UTC time. Make the scope name the entrypoint or lifecycle under review,
its requested outcome, and explicitly excluded neighboring systems.

If the scope is vague, use repository-local discovery to identify plausible
entrypoints and choose only the smallest slice justified by the request. Do not
silently substitute the current directory, default branch, newest file, or a
familiar environment. If choosing one bounded question or evidence boundary
requires an owner decision, retain `unknown` and use
`blocked-by-scope-conflict`.

The root `evidence_boundary` is one of `declared`, `source`, `wired`, `test`,
`runtime`, or `unknown` only when it cannot be bound. Interpret requests as
follows:

- documentation or contract truth requires `declared`;
- reachable implementation behavior requires `source`;
- the configured or selected implementation requires at least `wired`;
- explicitly exercised test behavior requires `test`; and
- deployed, active, production, or observed behavior requires `runtime`.

Never default a production question to local source or a selection question to
implementation presence.

## 2. Establish sources and identities

Discover the applicable repository instructions before tracing behavior. Find
narrowly relevant design notes, comments, types, source, registration output,
tests, fixtures, and supplied runtime observations. Bind file evidence to a
SHA-256 content identity and source evidence to the requested Git revision.

Treat documentation, comments, and types as declarations. They can establish a
stated contract but not executable behavior, active wiring, or runtime truth.
Preserve disagreement between declared design and current source rather than
choosing the account that reads most cleanly.

## 3. Start at composition, not abstraction

Find the composition root and actual construction or registration path before
describing an interface implementation as active. Trace entrypoint registration,
dispatch, dependency construction, lifecycle, effective configuration, feature
gates, and implementation selection.

Inventory every material alternative: real, no-op, fallback, plugin-provided,
generated, reflective, test-double, environment-specific, conditional, or
unknown. Source presence proves that code could execute if invoked; it does not
prove selection. Generated or reflective selection stays conditional or unknown
until its current output and selector inputs are identity-bound.

## 4. Trace one concrete path

Follow the requested path from input to outcome without collapsing layers. At
each supported transition capture:

- input contract, normalization, and validation;
- call, event, dispatch, or async handoff;
- data transformation and output;
- state reads, writes, commits, and externally visible effects;
- transaction boundaries and commit timing;
- locks, concurrency, queue ordering, and acknowledgement behavior;
- timeout, retry ownership, backoff, and terminal failure;
- idempotency key ownership, enforcement point, and uniqueness boundary;
- error propagation, fallback, compensation, and partial success; and
- returned or emitted result plus observability.

The mandatory path contains the requested entrypoint, every supported transition
to the requested outcome, active selection points, and every material state or
external effect and failure boundary along those transitions. Trace sequence is
a positive integer ordering. Do not skip an unsupported transition; terminate
at an Unknown.

## 5. Keep proof classes separate

Use exactly these Evidence classes:

- `declared`: documentation, comments, types, or contract declarations;
- `wired`: construction, registration, selectors, effective configuration, or
  generated composition output;
- `source_executable`: reachable implementation source at the bound revision;
- `test_exercised`: an identified setup and assertion that actually ran; and
- `runtime_observed`: supplied observations bound to a runtime identity and
  window.

Tests establish only their identified setup and assertions. A mock or fake
establishes caller behavior against that double, not the real adapter or active
composition. Runtime evidence establishes only its bound deployment/runtime,
environment, configuration, observed inputs, and time window.

## 6. Reconcile variants and contradictions

Represent each selection point as a Variant with its selectors and all material
alternative Components. Use `selected` only when complete current wiring proof
binds revision, environment, effective configuration, and generated output when
applicable. Otherwise retain `conditional`, `excluded`, or `unknown` as the
evidence permits.

When docs, interfaces, implementation, registration, tests, or runtime evidence
disagree, create a Contradictions row. A material disagreement cannot disappear
through narrative interpretation. It is resolved only by current evidence in
`resolution_evidence_ids`; otherwise keep it unresolved, route it to a human
decision, or record that no safe discriminator exists.

## 7. Write the canonical package

Begin with exactly these YAML fields. Angle-bracket text is template notation;
an actual record uses a bound value or literal `unknown`, never a placeholder.

```yaml
---
schema_version: subsystem-explanation/v1
question: <bound-question-or-unknown>
audience: <bound-audience-or-unknown>
repository_root: <canonical-absolute-path-or-unknown>
revision: <git-object-or-unknown>
worktree: <canonical-absolute-path-or-unknown>
scope: <bounded-slice-or-unknown>
environment: <bound-environment-or-unknown>
evidence_boundary: <declared-or-source-or-wired-or-test-or-runtime-or-unknown>
generated_at: <RFC-3339-UTC>
verdict: <explained-or-explained-with-unknowns-or-blocked-by-missing-evidence-or-blocked-by-scope-conflict>
---
```

Then emit the following ten sections in exactly this order.

## Explanation

Give a concise narrative calibrated to the named audience. Every material
sentence ends with a compact JSON array of supporting Claim IDs, such as
`["CLM-1","CLM-2"]`. If a diagram is useful, place it within this section and
apply the diagram rules below.

## Claims

| id | statement | subject_ids | evidence_ids | boundary | confidence | freshness | limits |
|---|---|---|---|---|---|---|---|

## Components

| id | name | role | kind | locator | selected_by_ids | lifecycle | evidence_ids | confidence |
|---|---|---|---|---|---|---|---|---|

## Trace

| id | sequence | from_id | to_id | trigger | input | transformation | output | state_effect_ids | failure_behavior | boundary | evidence_ids | confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|

## StateAndEffects

| id | owner_id | state_or_effect | operation | transaction_boundary | lock_or_concurrency | retry_or_idempotency | ordering | externality | evidence_ids | confidence |
|---|---|---|---|---|---|---|---|---|---|---|

## Variants

| id | decision_point | selector_ids | alternative_component_ids | active_status | environment_scope | evidence_ids | confidence |
|---|---|---|---|---|---|---|---|

## Contradictions

| id | subject_ids | source_a_id | source_b_id | impact | material | resolution_status | resolution_evidence_ids |
|---|---|---|---|---|---|---|---|

## Evidence

| id | class | locator | symbol_or_range | content_identity | revision | captured_at | environment | configuration_identity | runtime_identity | observed_inputs | time_window | boundary | observation | proves | limits | freshness |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

## Discriminators

| id | question | exact_read_only_action | cwd | required_access | semantic_side_effect | cost_bound | timeout_ms | privacy_scope | distinguishing_signals | owner | safety_status |
|---|---|---|---|---|---|---|---|---|---|---|---|

## Unknowns

| id | question | why_unknown | impact | discriminator_id | owner |
|---|---|---|---|---|---|

Every emitted data row has every cell. Claims and Evidence each contain at least
one row for a non-blocked verdict. Components and Trace also contain at least
one row unless the boundary is `declared` and the explanation asserts no
executable behavior. StateAndEffects, Variants, Contradictions, Discriminators,
and Unknowns may have no data rows; do not add sentinel rows.

## IDs, references, and cell encoding

All rows share one globally unique ID namespace. IDs match
`[A-Z][A-Z0-9]*-[0-9]+`. Arrays are compact JSON. Every `*_ids` cell is an array;
a singular `*_id` is one typed ID, or `not_applicable` only where this contract
allows it. Use `unknown` for an unknown scalar rather than guessing.

References are exact:

- Claims `subject_ids` target Components, Trace, StateAndEffects, Variants, or
  Contradictions; `evidence_ids` target Evidence.
- Components `selected_by_ids` target Variants or Evidence; `evidence_ids`
  target Evidence.
- Trace `from_id` and `to_id` target Components; `state_effect_ids` target
  StateAndEffects; `evidence_ids` target Evidence.
- StateAndEffects `owner_id` targets Components and `evidence_ids` target
  Evidence.
- Variants `selector_ids` target Evidence or Components,
  `alternative_component_ids` target Components, and `evidence_ids` target
  Evidence.
- Contradictions `subject_ids` target Components, Trace, StateAndEffects, or
  Variants; `source_a_id` and `source_b_id` target Claims or Evidence;
  `resolution_evidence_ids` target Evidence.
- Unknowns `discriminator_id` targets Discriminators, or is `not_applicable`
  only when no safe discriminator exists.
- Evidence arrays never reference another table.

Missing cells, duplicate IDs, malformed arrays, dangling or wrongly typed
references, undeclared enum values, and unsupported promotion invalidate the
record. Reject them rather than repairing them by inference.

## Exact values and identities

Use only these closed values:

- Claim, Component, Trace, StateAndEffects, and Variant `confidence`:
  `reported|source_supported|wiring_supported|test_supported|runtime_supported`.
- Claim and Evidence `freshness`:
  `current|stale|unbound|conflicting|unknown`.
- Claim, Trace, and Evidence `boundary`:
  `in_process|process|queue|datastore|network|external_service|unknown`.
- Variant `active_status`:
  `selected|conditional|excluded|unknown`.
- Contradiction `material`: `yes|no`; `resolution_status`:
  `unresolved|resolved_by_evidence|human_decision_required|no_safe_discriminator`.
- Discriminator `semantic_side_effect`: `none|possible|unknown`; its
  `safety_status`: `safe|unsafe|blocked|unknown|none_available`.

Evidence `class` is exactly one of the five proof classes in section 5.
Content, configuration, runtime/deployment, and safe observed-input identities
use `sha256:<64-lowercase-hex>`. Git revisions match exactly
`git:sha1:<40-lowercase-hex>` or `git:sha256:<64-lowercase-hex>`; no other
length or character set is valid. Unknown identity is literal `unknown`.
`captured_at` uses RFC 3339 UTC or `unknown`. Evidence `time_window` is exactly
this compact JSON object, with RFC 3339 UTC values or literal `unknown`:

```json
{"start":"<RFC-3339-UTC-or-unknown>","end":"<RFC-3339-UTC-or-unknown>"}
```

Every `cost_bound` is compact JSON:
`{"value":<nonnegative-number-or-"unknown">,"unit":"seconds|requests|bytes|usd|unknown"}`.
`timeout_ms` is a nonnegative integer or `unknown`.

Supplied runtime evidence binds a non-unknown environment, configuration
identity, runtime/deployment identity, safe observed-input identity, and a time
window whose start and end are both known. If any required binding is absent,
its confidence cannot rise above `reported`.

## Proof rules

Confidence tokens name different proof bases; they are not a ladder and must not
substitute for one another. For each claim, determine the dimensions its subject
requires and apply exactly one of these rules:

- `reported`: one or more required proof dimensions are absent, stale, unbound,
  conflicting, or unknown.
- `source_supported`: a declared-contract claim has current immutable
  `declared` evidence, or a behavior claim has current immutable
  `source_executable` evidence at the bound revision.
- `wiring_supported`: a selection claim has source plus current immutable
  `wired` evidence bound to revision, environment, effective configuration, and
  generated registration identity when applicable.
- `test_supported`: a test-outcome claim has source plus current
  `test_exercised` evidence bound to revision, fixtures, dependency and
  configuration identity, exact setup, and assertions. Wiring is additionally
  required only if the claim covers the real composition path.
- `runtime_supported`: an observed-behavior claim has source plus supplied
  `runtime_observed` evidence bound to runtime/deployment identity, environment,
  configuration, observed inputs, and time window. Wiring is additionally
  required only if the claim identifies the selected implementation.

An interface proves a declaration, not selection. Implementation source proves
behavior when invoked, not active selection. Tests do not replace wiring or
runtime proof, and runtime evidence does not require test evidence. Missing,
stale, unbound, conflicting, or unknown required evidence forces `reported`.

## Verdict derivation

Use exactly one verdict and apply this precedence:

1. `blocked-by-scope-conflict`: one bounded question, scope, or requested
   evidence boundary cannot be selected without an owner choice.
2. `blocked-by-missing-evidence`: the question, canonical repository root,
   worktree, revision, scope, or an evidence identity required by the requested
   boundary is `unknown`.
3. `blocked-by-missing-evidence`: for a `declared` boundary, no current declared
   Claim and Evidence establish the requested contract fact without asserting
   executable behavior; for any other boundary, no current source-supported
   Trace reaches the first applicable material state/external effect, or reaches
   the requested outcome when the subsystem has no such effect.
4. `explained-with-unknowns`: the applicable minimum above exists, but a
   mandatory requested fact, path segment, selected implementation, material
   effect or failure boundary, or outcome remains conditional, contradictory,
   or unknown.
5. `explained`: the complete requested contract or mandatory path meets the root
   evidence boundary; any selection in scope is wiring-supported; material
   behavior is source-supported; every material contradiction is resolved by
   current evidence; and no material Unknown remains.

Boundary satisfaction is exact:

- `declared` requires current declared Claims and Evidence. Components and Trace
  may be empty only when no executable behavior is asserted.
- `source` requires current source-supported behavior across the mandatory
  Trace.
- `wired` requires source behavior plus wiring-supported selection.
- `test` requires source plus every relevant mandatory Claim at
  `test_supported` for the bound test setup; wiring is required only when the
  request includes real composition.
- `runtime` requires source plus every requested mandatory Claim at
  `runtime_supported`; wiring is required when selected implementation is in
  scope.

No proof dimension fills another. A material contradiction with status
`unresolved`, `human_decision_required`, or `no_safe_discriminator` prevents
`explained`. `resolved_by_evidence` requires non-empty current
`resolution_evidence_ids` whose `proves` value adjudicates the two sources for
the contradicted subject at the root evidence boundary. Declared or source
evidence cannot resolve a wired, test, or runtime contradiction. Prose is not
resolution.

## Safe discriminators

Record, but never execute, the smallest future read that can distinguish the
material alternatives. A safe Discriminator has a fully resolved read-only
action and cwd, required access, `semantic_side_effect=none`, bounded cost and
timeout, a narrow privacy scope, explicit distinguishing signals, an owner, and
`safety_status=safe`.

Placeholder commands and paths are not safe discriminators. If the action is
mutating, access is missing, privacy cannot be bounded, or cost/timeout is not
bounded, mark it `unsafe`, `blocked`, or `unknown`. If no safe discriminator
exists, use `none_available`; the related Unknown uses
`discriminator_id=not_applicable` and names its owner.

## Diagram rules

Diagrams are optional and never a substitute for the tables.

- Every node cites an existing Component, Trace, or Variant ID.
- Every edge cites an existing Trace or Variant ID.
- A factual arrow requires a supported Trace row.
- A selector branch may cite a Variant, but it cannot imply that an alternative
  is selected beyond the Variant's supported `active_status`.
- An unsupported transition ends at a visibly distinct gap node backed by an
  existing Variant ID and may also show the related Unknown ID in its label.
  Its incoming edge cites that Variant and is visibly non-factual; do not draw
  an arrow from the gap to a guessed component or outcome.
- A `conditional` label does not authorize invented relay, acknowledgement,
  retry, idempotency, adapter, or persistence structure.

## Validate before returning

Reject the package rather than silently normalizing it when any check fails:

1. exact root keys, schema version, timestamp, evidence boundary, and verdict;
2. exact section order, table columns, required cells, and cardinalities;
3. global ID uniqueness, ID grammar, compact arrays, reference existence, and
   reference types;
4. identity forms, timestamps, enums, discriminator encodings, and exact cost
   and timeout forms;
5. composition-first selection, mandatory Trace continuity, positive sequence,
   state/effect and failure-boundary coverage, and Variant promotion;
6. proof-class separation, confidence basis, freshness, contradiction
   resolution, and verdict derivation;
7. Claim citations at the end of every material Explanation sentence;
8. diagram node/edge backing and visible termination at every unsupported
   transition; and
9. read-only compliance and absence of invented behavior.

Report the verdict, then the complete canonical package. Stop after the record.
Do not append recommendations, redesign ideas, implementation steps, or an
executed discriminator.

## Pressure defenses

| Shortcut | Required response |
|---|---|
| "The overview says it writes directly, so use that as the path." | Treat the overview as `declared` evidence. Trace current composition and source, record the contradiction, and do not promote the declaration over wiring. |
| "The real adapter exists and the interface points to it." | Presence and interface shape do not prove selection. Preserve every alternative and require complete wiring evidence before `selected`. |
| "The unit test injects a mock and passes, so the live integration works." | Limit the claim to the identified mock setup and assertions. It proves neither the real adapter, active composition, nor runtime behavior. |
| "This is production; infer the active implementation from source and config defaults." | Production requires supplied runtime evidence with deployment/runtime, environment, effective configuration, observed-input, and time-window identity. Without it, keep production behavior unknown and use the bounded verdict. |
| "Draw the expected relay and retry flow now, then label it conditional." | Do not turn an unsupported transition into visual structure. End the supported arrow at a distinct Unknown gap node and draw nothing beyond it. |
| "Collapse the route, queue, worker, and storage path into one backend call." | Keep each supported transition and every material state, transaction, async, retry, ordering, idempotency, and failure boundary explicit. |
| "Generated registration probably matches source." | Bind the generated output and selector inputs. Without them, the Variant remains conditional or unknown and may require a safe Discriminator. |
| "Use local tests to confirm the deployed behavior." | Keep test and runtime proof orthogonal. Local execution cannot satisfy a production or active-runtime boundary. |
| "While explaining, patch the stale documentation." | Stay read-only. Record the contradiction and stop; documentation repair requires a separate request. |
