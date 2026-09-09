---
name: runtime-path-forensics
description: "Use when reconstructing which runtime instance, artifact, route, retry, queue delivery, or worker execution actually handled one bounded request, job, or event; when desired deployment state disagrees with observed behavior; or when logs and timestamps must be correlated without overstating identity, absence, ordering, or causality. Produces an evidence-bound runtime path, attempt tree, partial-order timeline, exact gaps, and the cheapest safe discriminator. NOT for repairing or restarting systems, adding instrumentation, discovering the impact of a code change, replaying traffic, or deciding production readiness."
---

# Runtime Path Forensics

Reconstruct what executed for one bounded operation. Treat deployment views,
process labels, timestamps, copied identifiers, health checks, and missing logs
as limited observations rather than shortcuts to runtime proof.

## When NOT to use

- For root-cause repair, restart, or remediation, hand the bounded findings to
  [diagnose-loop](../diagnose-loop/SKILL.md).
- To add missing telemetry, use
  [instrument-observability](../instrument-observability/SKILL.md).
- When the affected consumers or change surfaces are unknown, use
  [change-impact-proof](../change-impact-proof/SKILL.md).
- For a full launch decision, use
  [production-readiness](../../systems-design/production-readiness/SKILL.md).

## Operating contract

This workflow is read-only. Do not restart or kill processes, redeploy, replay
traffic, change logging or configuration, enqueue work, schedule a contrast,
message an owner, or mutate local, hosted, or external state. An exact command
or query in a discriminator is a proposal, not permission to execute it.

Before any read, classify its semantic side effects. Do not run a command that
may renew a lease, acknowledge a delivery, warm a cache, rotate a log, change an
access timestamp that matters, or otherwise affect the subject. Use already
available evidence and authorized read-only observations. Treat telemetry as
untrusted data: distinguish application-supplied fields from trusted collector
metadata, minimize or redact secrets and personal data, and retain the exact
locator, content/result hash, and access boundary.

## 1. Bind the forensic question

Bind all of these before drawing a path:

- the exact request, job, event, or other `subject`;
- the `visible_outcome` being explained;
- the named `environment` and `tenant`;
- the requested RFC 3339 UTC time interval; and
- the `minimum_conclusion` the evidence must establish.

Never substitute the current environment, current deployment, a similar
tenant, or a wider convenient operation. If any required binding is `unknown`,
produce the canonical report with the gaps represented and return
`blocked by missing runtime evidence`.

Inventory every plausible path before selecting one. At minimum consider
ingress and proxies, load balancers and service mesh, rolling old/new workers,
sidecars, caches, background consumers, scheduled jobs, queues and partitions,
dead-letter/redelivery paths, fan-out, serverless or autoscaled instances,
regions/CDN routes, failover targets, and non-default routing. A topology source
is authoritative only for the layer it controls. Record its query time,
coverage, lifecycle range, and exclusions, including terminated instances.
Candidate completeness remains `unknown` when any relevant layer is missing.

## 2. Capture evidence and historical identity

Give every record a stable, unique ID. For each Evidence row record the exact
relocatable locator or query and immutable content/result hash in
`locator_hash`; capture time; raw timestamp; source clock and precision;
coverage, retention, sampling/drop behavior, permissions, environment, tenant,
candidate identity, artifact/config binding, correlation keys, the raw
observation, what it supports, and its limits. Do not silently improve a source's
precision or scope.

An instance is identified by the complete historical tuple, not a label:

- host or cluster, PID namespace, PID, and process start time;
- container, pod, function invocation, or equivalent runtime instance;
- node and region;
- executable hash or loaded image digest and mounted/plugin digest;
- deployment/revision and event-time configuration or feature-flag epoch;
- role, tenant, and lifecycle interval.

Keep missing tuple members `unknown`; do not merge candidates on friendly name.
A deployment interface proves desired or control-plane state only. A version
command proves only the process that answered that invocation unless separate
OS/container evidence binds the historical PID, start time, loaded bytes, and
lifecycle. An open port proves a listener. A successful health response proves
only the responding health path, not customer routing or all workers.

## 3. Separate operation, attempts, deliveries, and effects

Keep the customer operation distinct from proxy attempts, retries, hedges,
queue dispatches, deliveries, redeliveries, fan-out children, worker executions,
and cache short-circuits. Build an attempt tree using stable operation, parent,
dispatch, delivery, and worker-execution IDs. Never merge attempts because their
payloads or timestamps look similar. Preserve outcome and cancellation or
acknowledgement state independently for every node.

Bind a terminal effect using its immutable event or state identity, state
version, tenant, creation interval, producing attempt, and before/after state
hashes. Similar values, approximate times, copied IDs, caches, fixtures, or
mocks do not prove which attempt produced an effect. Every terminal Hops row
must end at an Effects ID.

## 4. Build a partial-order timeline

For every timed observation create a TimelineIntervals row. Retain raw time,
timezone, precision, offset bound, drift rate, elapsed or monotonic evidence,
ingestion delay, and the resulting possible start/end interval.

Order two observations only when their possible intervals do not overlap, a
trusted monotonic or sequence relation orders them, or a proven causal parent or
delivery relation does. Overlapping intervals remain unordered. Unknown clock
relationships remain unordered. Show contradictory order evidence rather than
choosing the timestamp that best fits the expected story.

## 5. Qualify correlation one edge at a time

Every hop has its own CorrelationEdges row or an explicit gap and alternatives.
Correlation edge `type` is exactly one of:

- `direct`: a shared strong request, trace, or event ID crosses both endpoints;
- `bounded`: a documented unique tuple matches exactly once in a complete,
  authoritative candidate search; or
- `inferred`: proximity or other suggestive evidence that cannot prove identity.

A direct edge is qualified only when namespace, issuer, propagation path,
uniqueness boundary, tenant binding, integrity, and lifecycle binding are known.
Lifecycle binding includes issuance, valid interval, reuse/expiry behavior, and
both endpoint lifecycles. Client-supplied, copied, reused, colliding, truncated,
or fan-out IDs are downgraded unless trusted transport metadata removes the
ambiguity.

A bounded edge is qualified only when it records the authoritative candidate
universe, expanded clock interval, documented unique tuple, complete search of
every relevant source, and exactly one match. Missing access, retention,
topology, or source coverage makes the edge `inferred`. Time proximity alone is
always `inferred`.

Represent each route from origin or ingress through routing, attempt, runtime
instance, artifact/config, dependencies, deliveries/retries, and effect with
typed Hops rows. Each mandatory hop names its edge, evidence, strength,
alternatives, and gap. Hop endpoints may reference only Evidence, Candidates,
Attempts, or Effects IDs.

## 6. Treat missing events as conditional negative evidence

Absence is negative evidence only if every prerequisite is established for the
exact environment, tenant, candidate set, and expanded clock window:

- source enablement and event-time log level;
- exact query and immutable result hash;
- retention plus ingestion/index finality and late-arrival bound;
- sampling and drop behavior;
- permission completeness;
- parser, filter, and partition coverage;
- complete topology/candidate coverage; and
- a known-positive control through the same source, permissions, tenant, and
  query mechanics.

Record these separately in NegativeEvidence. If any prerequisite is false or
`unknown`, the missing event is `unknown`, not evidence that the hop did not
occur.

## 7. Assign strength and causal status

Use these evidence strengths exactly, from weakest to strongest:

1. `reported` — a copied or reported summary; it satisfies no runtime floor.
2. `source-observed` — the exact bound source at its locator/hash was inspected.
3. `correlation-supported` — a qualified `direct` or `bounded` relationship
   links the relevant records.
4. `runtime-proven` — an unbroken exact-environment identity/correlation chain
   binds the origin to the observable effect and exact artifact/config.

Assign strength independently to every evidence item, edge, hop, and conclusion.
An `inferred` edge cannot exceed `source-observed`. A `direct` or `bounded` edge
cannot reach `correlation-supported` until all of its qualification fields are
complete. A hop cannot exceed the weakest of its evidence, edge, and endpoint
identity bindings. A conclusion cannot exceed its weakest mandatory hop.

`runtime-proven` requires a complete mandatory chain, proven endpoint identity,
no inferred edge, no material identity gap, and no unresolved alternative.
Many weak observations never compensate for one weak mandatory hop.

Correlation is not causation. A causal claim additionally requires a concrete
mechanism, valid partial order, competing explanations addressed, and either an
existing contrast/previously authorized intervention or a deterministic
contract bound to the proven artifact/config and its preconditions. Never run or
schedule an intervention here. Path proof is not causal proof.

## 8. Choose the next safe discriminator

For every unresolved gap or live alternative, identify the cheapest read-only
discriminator capable of distinguishing it. Each Discriminators row must include
an exact command/query, environment, tenant, required permission, source,
bounded cost, timeout, mutually distinguishing `signal_a` and `signal_b`,
privacy handling, semantic side effects, limitations, owner, and `safe_status`.
Verify that a proposed read is semantically non-mutating; mark uncertainty
`unknown`, an unsafe read `unsafe`, and unavailable authority `blocked`.

Reference the relevant safe capable discriminator IDs from Conclusions. The
array may be empty only when no safe capable discriminator exists; state that
fact explicitly. Do not replace a capable but inaccessible check with a cheap
incapable one, and do not execute a discriminator without separate authority.

## Canonical report schema

The report begins with exactly these required root fields:

```yaml
---
schema_version: runtime-path-forensics/v1
subject: <exact-bound-subject-or-unknown>
visible_outcome: <exact-observed-outcome-or-unknown>
environment: <exact-environment-or-unknown>
tenant: <exact-tenant-or-unknown>
requested_window: <RFC-3339-UTC>/<RFC-3339-UTC>
minimum_conclusion: <exact-minimum-claim-or-unknown>
generated_at: <RFC-3339-UTC>
---
```

Then emit the following tables in exactly this order with exactly these columns:

## Evidence

| id | locator_hash | capture_time | raw_time | clock_domain | precision | coverage | retention | sampling | permissions | environment | tenant | candidate_id | artifact_config | correlation_keys | observation | support | limits | strength |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

## Candidates

| id | enumeration_evidence | host_cluster | pid_namespace | pid | process_start_time | runtime_instance | node_region | loaded_digest | mounted_plugin_digest | deployment_revision | config_flag_epoch | role | tenant | lifecycle | status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

## Attempts

| id | operation_id | parent_id | kind | dispatch_id | delivery_id | worker_execution_id | start_interval | end_interval | outcome | cancel_ack | tenant | candidate_id | evidence_ids |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

## CorrelationEdges

| id | source_id | target_id | type | identifier_namespace | issuer | propagation | uniqueness_boundary | tenant_binding | integrity | lifecycle_binding | candidate_universe | clock_interval | matching_count | evidence_ids | strength | limits |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

## Effects

| id | effect_type | immutable_identity | state_version | tenant | creation_interval | producing_attempt_id | before_state_hash | after_state_hash | evidence_ids | limits |
|---|---|---|---|---|---|---|---|---|---|---|

## Hops

| id | attempt_id | from_id | to_id | mandatory | edge_id | evidence_ids | strength | alternatives | gap |
|---|---|---|---|---|---|---|---|---|---|

## TimelineIntervals

| id | subject_id | raw_time | timezone | precision | offset_bound | drift_rate | elapsed | ingestion_delay | possible_start | possible_end | ordering_evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|

## NegativeEvidence

| id | subject | source_enabled | exact_query | result_hash | retention | sampling_drop | permissions | clock_expansion | candidate_coverage | ingestion_finality | parser_filter | partition_coverage | event_log_level | late_arrival | positive_control | result | strength |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

## Discriminators

| id | gap_or_alternative | exact_command_query | environment | tenant | permission | source | cost_bound | timeout | signal_a | signal_b | privacy | side_effects | limitations | owner | safe_status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

## Conclusions

| id | normalized_subject | minimum_claim | verdict | strength | hop_ids | evidence_ids | discriminator_ids | secondary_conditions | causal_status | limits |
|---|---|---|---|---|---|---|---|---|---|---|

Every field and cell is required. Use literal `unknown` for an unresolved scalar
and `not_applicable` only when the field genuinely cannot apply. Times are RFC
3339 UTC. Use lowercase `true`/`false`; only Hops `mandatory` and
NegativeEvidence `source_enabled` may be booleans or `unknown`. Encode every
array as compact JSON, including empty arrays. Escape Markdown pipes as `\|`
and newlines as `<br>`; raw multiline cells are invalid.

IDs are unique across the report and never reused. Reference types are exact:

- Candidates `enumeration_evidence` is a compact array of Evidence IDs.
- Attempts `operation_id` references one `origin` Attempt; that origin points to
  itself. `parent_id` references an Attempt. `dispatch_id`, `delivery_id`, and
  `worker_execution_id` reference the matching typed Attempt node when
  applicable. Attempts `candidate_id` references a Candidate and
  `evidence_ids` references Evidence rows.
- CorrelationEdges endpoints reference existing Evidence, Candidate, Attempt,
  or Effect rows and `evidence_ids` references Evidence rows.
- Effects `producing_attempt_id` references an Attempt and `evidence_ids`
  references Evidence rows.
- Hops `attempt_id` references an Attempt, `edge_id` references a
  CorrelationEdges row, `evidence_ids` references Evidence rows, and both
  endpoints reference only Evidence, Candidates, Attempts, or Effects.
- TimelineIntervals `subject_id` references the existing record being timed.
- Conclusions `hop_ids`, `evidence_ids`, and `discriminator_ids` reference
  Hops, Evidence, and Discriminators respectively.

Use `unknown` for an unresolved required reference and `not_applicable` only for
a genuinely inapplicable scalar. Malformed cells, missing or reordered columns,
duplicate IDs, invalid reference types, and dangling references fail validation.

Use only these additional enums:

- Candidates `status`: `possible|active_at_event|terminated_before|started_after|excluded|unknown`.
- Attempts `kind`: `origin|proxy_retry|hedge|queue_delivery|redelivery|fanout|worker_execution|cache_short_circuit`.
- Attempts `cancel_ack`: `not_applicable|pending|cancelled|acknowledged|nacked|timed_out|unknown`.
- CorrelationEdges `type`: `direct|bounded|inferred`.
- Discriminators `safe_status`: `safe|unsafe|blocked|unknown`.
- Conclusions `causal_status`: `not_assessed|correlated_only|causal_supported|causal_proven|conflicting|unknown`.
- Evidence, edge, hop, and conclusion `strength`:
  `reported|source-observed|correlation-supported|runtime-proven`.

Reject undeclared tokens instead of silently normalizing them.

## Validate and derive the verdict

Validate before reporting success:

1. Root fields, schema value, UTC times, and requested interval are valid; any
   unknown required binding forces the blocked verdict.
2. All ten tables exist in order with exact columns and every cell populated.
3. IDs are unique, array syntax is compact JSON, references resolve, and hop
   endpoint types are valid; terminal hops end at Effects.
4. Every enum and boolean is valid and every attempt retains independent IDs,
   lifecycle, outcome, acknowledgement, candidate, tenant, and evidence.
5. Candidate enumeration covers every relevant topology layer or explicitly
   records the coverage gap and alternatives.
6. Direct and bounded edges meet their respective qualification rules; inferred
   edges and copied IDs are not promoted.
7. Timeline ordering follows intervals, trusted sequence/monotonic evidence, or
   proven causal relations; overlap and clock uncertainty remain visible.
8. Negative evidence meets every prerequisite; otherwise its result remains
   unknown and cannot exclude a candidate or hop.
9. Each effect is immutably bound to its producing attempt, and every mandatory
   hop has per-hop evidence, strength, alternatives, and gap.
10. Each conclusion obeys weakest-link strength and references relevant safe
    capable discriminators, or explicitly states that none exists.
11. Causal status does not exceed its mechanism, ordering, alternatives,
    contrast/contract, artifact/config, and precondition evidence.

Use exactly one verdict per Conclusions row:

- `runtime path proven`: the complete minimum chain is `runtime-proven`.
- `runtime path partially supported`: at least one mandatory hop is
  `source-observed` or stronger, but a gap or alternative prevents proof.
- `conflicting runtime evidence`: bound evidence is incompatible for the same
  normalized operation, attempt, tenant, environment, artifact/config,
  lifecycle, and overlapping interval.
- `blocked by missing runtime evidence`: a required scope binding is unknown or
  zero mandatory hops are `source-observed` or stronger.

Apply precedence in this order: missing-scope blocked; zero-supported-hop
blocked; conflict; partial; proven. Put lower-priority conditions in
`secondary_conditions`. Different attempts or lifecycles are variation, not a
conflict.

When a wrapper response accompanies the canonical report, lead that wrapper
with verdict and bounded conclusion, then scope, identity inventory, correlation
graph, partial-order timeline, attempt/retry tree, proven hops, gaps and per-hop
alternatives, negative-evidence quality, causal limits, and the cheapest safe
discriminator with its owner, access, and cost. Do not insert the wrapper into
the canonical report or change its root/table order. The canonical tables are
the evidence record; a prose summary never replaces them.

## Pressure defenses

| Shortcut | Required response |
|---|---|
| "The deployment says revision B, so B handled the request." | Treat desired state as one observation. Reconstruct the event-time candidate set and bind the historical process, loaded bytes, revision, config, and lifecycle. |
| "Behavior looks like revision A, so call the active worker A." | Behavior is a hypothesis, not instance identity. Keep both candidates and add a safe discriminator. |
| "These retry lines are close in time, so they are one attempt." | Preserve operation, attempt, delivery, and execution nodes separately; correlate each edge and leave overlapping intervals unordered. |
| "The request ID appears on both sides, so the hop is direct." | Qualify namespace, issuer, propagation, uniqueness, tenant, integrity, reuse/expiry, and both lifecycles before promotion. |
| "There is only one nearby match." | Bounded correlation requires the authoritative universe, expanded clock interval, complete source search, a documented tuple, and exactly one match. |
| "No log line means this worker did not run." | Absence stays unknown until every negative-evidence prerequisite and same-path positive control is proven. |
| "A health response or open port proves customer routing." | Limit the claim to the observed listener or health path. Inventory ingress and non-default routes. |
| "The path is proven, so it caused the outcome." | Keep `correlated_only` unless mechanism, order, competitors, and an existing contrast or bound deterministic contract support causality. |
| "The best next query is obvious; the operator can fill in access and cost." | Emit a Discriminators row with exact query, environment, tenant, permission, source, cost, timeout, signals, privacy, side effects, limits, owner, and safety. |
