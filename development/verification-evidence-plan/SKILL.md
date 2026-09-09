---
name: verification-evidence-plan
description: "Use when an exact engineering claim needs an ordered, runnable, falsifiable verification plan before anyone executes checks. Converts claim fragments and risks into traceable assurances, evidence floors, decisive checks, negative controls, stop rules, and exact verdicts while preserving unknowns. NOT for discovering unknown impact surfaces, implementing tests, broad review, launch approval, executing checks, editing code or CI, scheduling work, or mutating any local, hosted, or external system."
---

# Verification Evidence Plan

Turn one exact engineering claim into the smallest evidence plan that could
support or falsify it. A checklist of topics is not a plan: an operator must be
able to run each check without guessing and know exactly what passed, failed,
or remained unknown.

## Operating contract

This is a read-only planning workflow. During a planning request, inspect
existing read-only artifacts only as needed to resolve the claim and plan. Do
not execute proposed checks, edit code, tests, fixtures, CI, or configuration,
schedule work, deploy, call a mutating service, or change local, hosted, or
external state. Execution requires a separate explicit request and the required
authorization. Words such as "first", "next", and "ordered" describe a future
operator run, not permission to start it.

Reported prior results are planning inputs, never current execution evidence.
Keep proposed checks and existing evidence in separate sections.

## 1. Bind and decompose the claim

Record the following before designing checks:

- `CLM-###`: the exact claim, including what outcome is asserted and what is
  not asserted;
- target state: immutable revision or artifact identity, dirty-worktree state,
  relevant configuration and data state, and named environment when the claim
  includes one;
- evidence boundary: local fixture, integration environment, hosted system, or
  another explicit boundary;
- risk tolerance: mandatory assurance floors, acceptable limitations, and the
  owner of any authorization needed later;
- in-scope consumers, trust boundaries, compatibility seams, failure timing,
  and material side effects.

If the target, scope, named environment, or mandatory evidence boundary cannot
be resolved, the verdict is `blocked`. If the impact surfaces themselves are
unknown, route to `change-impact-proof` first and do not invent them here.

Decompose the claim into independently falsifiable `CF-###` fragments. A
fragment is material when its failure could change the claimed outcome,
violate a trust boundary, break a compatibility seam, duplicate or omit a side
effect, or exceed the stated risk tolerance. Map all material failure modes
before minimizing. Record every omitted candidate with the reason it is
immaterial or out of scope.

An unmapped claim fragment is blocking. Do not hide one inside prose or average
it away with stronger evidence for a different fragment.

## 2. Define decisive assurances

Create one or more `ASR-###` assurances for every claim fragment. Each assurance
record contains:

| Field | Required content |
|---|---|
| Claim mapping | One or more `CF-###` IDs |
| Invariant | The claim fragment that must remain true |
| Falsifier | Stable `FAL-###` ID and a concrete observable result that disproves the invariant |
| Evidence floor | Minimum evidence state and why weaker evidence cannot answer this assurance |
| Freshness | Validity window and the events that invalidate evidence |
| Decisive checks | One or more `CHK-###` IDs that can meet the floor |
| Failure meaning | What a failure establishes and what it does not establish |
| Limitations | Residual ambiguity after the planned checks |

Every assurance must map to at least one decisive check. Prerequisite,
diagnostic, and optional checks never satisfy an assurance floor.

Use only these evidence states:

| State | Meaning |
|---|---|
| `unplanned` | No runnable assurance-specific check has been specified. |
| `specified` | A complete future check exists, but it has not been run for the bound target. |
| `executed` | The decisive check ran against the bound immutable target in the stated non-live environment. |
| `environment-observed` | The decisive behavior was observed in the exact named mutable environment. |

Behavioral safety normally requires `executed`. A claim about a real named
environment requires `environment-observed` there. A proposed check created by
this planning workflow can be only `unplanned` or `specified`; describing its
future run never promotes it. Pre-existing evidence may retain `executed` or
`environment-observed` only when its inspected record is fresh,
provenance-bound, and contains every field required below.

Label inherited or user-reported evidence `reported`. It meets no evidence
floor and cannot falsify the claim. Every existing-evidence record must include
source, timestamp, exact observation, target state, environment identity,
result, and `ASR-###` mapping. Stale, target-unbound, unverifiable, hearsay, or
unknown-freshness evidence remains `reported`.

Evidence is fresh only when it is bound to the exact immutable revision and is
inside the assurance's validity window. For a mutable environment, it must also
have been observed after the latest relevant deployment, configuration change,
or data change. If any of those times or bindings is unknown, the evidence is
unusable for the floor.

## 3. Specify checks an operator can actually run

Give each check a stable `CHK-###` ID and one type:

- `prerequisite`: establishes that a decisive check can run;
- `decisive`: can support or falsify an assurance at its declared floor;
- `diagnostic`: explains a failure but cannot satisfy an assurance;
- `optional`: adds confidence beyond the required floor.

Compilation, type-check, syntax, and lint success are prerequisite evidence
only. They cannot satisfy a behavioral assurance floor or substitute for an
executed decisive check, even when they pass on the bound target.

Every check record includes all of these fields:

1. type and mapped `ASR-###` and `FAL-###` IDs;
2. exact command or exact manual observation, with no placeholder command;
3. working directory, runtime or environment identity, and prerequisites;
4. fixtures or data, deterministic setup, and initial state;
5. expected passing signal or invariant;
6. expected failing result and how it realizes the falsifier;
7. timeout and what a timeout means;
8. cleanup, rollback, and side effects, including what persists on failure;
9. failure interpretation and known limitations;
10. for every decisive behavioral check, a controlled negative perturbation or
    directly observable path signal, plus why unrelated code cannot create the
    same passing signal.

If an exact command, environment, fixture, timeout, cleanup action, expected
signal, or negative control cannot be resolved from available artifacts, keep
the check incomplete and return `blocked` when it is mandatory. Do not present
shell-shaped placeholders such as `<test-command>` as runnable checks.

A destructive future check may be specified only when it names the exact
target, all side effects, authorization owner, cleanup, rollback, and a stop
gate before execution. Missing mandatory authorization yields `blocked`.
Planning it never authorizes or schedules it.

### Biting-path rule

A passing behavioral result must prove the intended path ran. Prefer a
controlled perturbation that makes the check fail for the expected reason,
then restore it before the positive run. When perturbation is unsafe, require a
unique path signal such as a bound side-effect ledger, trace event, or exact
wire bytes. State why a mock-only success, unrelated handler, cached result, or
same-library round trip cannot emit the signal. A check that merely executes
code or returns success without this proof is not decisive.

## 4. Cover the material assurance family

The claim determines the assurance family. Apply the following minimums when
the named behavior is in scope; add claim-specific cases rather than treating
these as a universal test list.

### Retried external side effects

Map concurrent same-key requests, duplicates before and after response loss,
conflicting payload reuse, timeout before the side effect, timeout after the
side effect, and the crash window after the external effect succeeds but before
the local result commits. Also map downstream suppression, local atomicity,
retention or expiry, and replay after expiry.

Each retry case must observe the external side-effect count. For a charge-like
effect, the required invariant is exactly one externally observed charge in
every retry case, including the crash window. A local idempotency row, returned
status, or mocked call count alone cannot satisfy that assurance.

For each individual retry scenario, also declare exactly one allowed externally
visible response or result outcome. Specify the exact status, body, error,
replay behavior, or observation that represents that single outcome. An
unspecified outcome or multiple ambiguous allowed outcomes makes the check
incomplete and yields `blocked` when the scenario is mandatory.

### Authorization and scope

Require an allowed positive control plus unauthenticated, invalid or expired,
inactive, insufficient-capability, cross-scope, revoked, and escalation cases.
Every denial must prove that no protected side effect occurred, using a bound
ledger, before-and-after protected state, or another exclusive path signal.
A denied response code alone is not decisive.

### Cross-runtime compatibility

Use independent runtime paths. Produce versioned golden serialized wire bytes
in one runtime and consume those exact unchanged bytes in the other. Exercise
encoding and decoding, null versus omitted values, numeric precision, Unicode,
time representation, unknown and malformed fields, and supported backward and
forward versions. Re-created in-memory objects and same-library round trips do
not prove the boundary.

Route the quality of test implementation to `unit-test-quality`, broad review
to `review-panel`, and a full launch decision to `production-readiness`. This
workflow specifies the evidence needed; it does not take over those jobs.

## 5. Order the future run and define stops

Order checks by information gain relative to cost and destructiveness. Cheap
prerequisites may precede a costly decisive check, but they do not replace it,
and the plan must keep missing mandatory evidence visible.

Stop the future run on:

- a decisive falsifier;
- missing authorization or a destructive prerequisite not explicitly approved;
- an unavailable mandatory environment or evidence floor;
- a baseline inconsistency that prevents binding the check result to the target.

Record unrelated baseline failures and continue planning independent target
checks. A baseline inconsistency stops only the checks whose results cannot be
attributed because of it.

## 6. Assign the verdict

Use exactly one verdict:

- `plan complete`: every mandatory assurance and check is fully specified and
  no evidence-access limitation is known; future execution may still be pending;
- `plan complete with gaps`: the plan is fully specified, but named
  non-blocking limitations reduce confidence without violating a mandatory
  floor; pending execution alone is not a gap;
- `blocked`: the claim, target state, required scope, authorization, or a
  mandatory assurance or evidence floor cannot be specified or met;
- `claim falsified by existing evidence`: fresh, provenance-bound existing
  evidence meets a decisive floor and falsifies an assurance.

Do not use `claim falsified by existing evidence` for reported, stale,
unbound, or unverifiable results. Do not call a plan complete when its target,
scope, environment, traceability, or mandatory runnable fields are missing.

## Output contract

Lead with the verdict and exact `CLM-###` claim, then provide these sections in
order:

1. scope and target state;
2. assurance matrix;
3. ordered run plan;
4. stop rules;
5. existing evidence, clearly separated and labeled;
6. evidence gaps and limitations;
7. omitted candidates with reasons;
8. cheapest next decisive check.

Include a traceability table proving every `CF-### -> ASR-### -> FAL-### ->
CHK-###` link. The cheapest next decisive check is present only when one validly
exists. For a falsified claim write `next decisive check: none—stop on
falsifier`. For a blocked plan, name the next owner and exact action needed to
unblock instead of inventing a check.

Before returning, verify that every decisive check is runnable from its record,
every mandatory floor has a decisive check, every behavioral check bites the
intended path, and no proposed action was executed or scheduled.

## Pressure defenses

| Rationalization | Required response |
|---|---|
| "The checklist names the right scenarios, so the operator can fill in the commands later." | Missing commands, environments, fixtures, timeouts, cleanup, floors, signals, or mappings makes a mandatory check incomplete; return `blocked`. |
| "A reported green run is enough to plan around." | Label it `reported`; without exact provenance, freshness, target, environment, and assurance binding it meets no floor. |
| "The happy path proves authorization is wired." | Plan the complete denial and escalation matrix, and prove zero protected side effects for every denial. |
| "The object round-tripped, so the language boundary is compatible." | Require one runtime's exact versioned wire bytes to be consumed unchanged by the other runtime. |
| "The user asked what to run first, so start or schedule the cheap check." | Return an ordered future run only. Execution and scheduling require a separate explicit request and authorization. |
