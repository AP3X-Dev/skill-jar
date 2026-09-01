---
name: architecture-decision-loop
description: "Use when a load-bearing software architecture choice is unresolved and could affect module ownership, public APIs, schemas, tenancy/auth, consistency, datastore ownership, integration seams, runtime topology, failure domains, recurring cost, or vendor lock-in. Runs problem framing -> research -> genuinely different alternatives -> tradeoff analysis -> independent adversarial critique -> human choice -> ADR/provenance -> optional MemBerry indexing -> Guardrail candidate handoff. NOT for trivial implementation choices or autonomous architecture approval."
---

# Architecture Decision Loop

Turn an important architecture question into a researched, adversarially tested, human-owned decision that future coding agents can retrieve and Guardrail can enforce when the consequence is deterministic.

```text
Problem
  -> Research
  -> Architecture alternatives
  -> Tradeoff analysis
  -> Adversarial critique
  -> Human choice
  -> Decision record
  -> MemBerry index
  -> Guardrail candidate
```

**Output:** a decision packet and ADR. If the accepted choice implies deterministic architecture constraints, emit Guardrail handoff candidates. Do not turn every ADR into a blocking rule.

## Operating contract

1. **One load-bearing question at a time.** Split independent choices rather than hiding them in one ADR.
2. **Research precedes preference.** Gather constraints/evidence before proposing a winner.
3. **At least two genuinely different architectures when contested.** Different libraries inside one shape are not different architectures.
4. **Criteria before scoring.** Define hard constraints and judging criteria before comparing options.
5. **Maker != checker.** Designers do not certify their own alternative. Use fresh/isolated designer, judge, and skeptic roles when the host supports them. If isolation is unavailable, disclose reduced assurance.
6. **Human owns direction.** Recommendation is not acceptance. "Use your recommendation" counts only after the human has seen the alternatives/tradeoffs.
7. **Evidence != authority.** MemBerry, FUGAZI, source, benchmarks, docs, and research support a decision but do not approve it.
8. **Rejected alternatives matter.** Record why they lost and what would have to change for them to become viable.
9. **Guardrail receives only enforceable consequences.** Preferences stay in ADRs. Deterministic boundaries can become candidates.
10. **Changing direction requires supersession.** Never rewrite history to make the new choice look permanent.

## When to use

Use for choices involving domain/module boundaries, dependency direction, public APIs, schemas/formats, tenancy/auth/trust, transactions/consistency, sync vs async, datastore ownership, queues/eventing, integration seams, monolith vs services, deployment regions/topology, failure domains, major vendor lock-in, or meaningful recurring cost.

## When NOT to use

- Trivial/local/reversible implementation detail.
- General feature brainstorming: use [design-panel](../../development/design-panel/SKILL.md).
- Whole-system greenfield intake: use [greenfield-architecture](../greenfield-architecture/SKILL.md).
- System sizing/topology intake: use [design-system](../design-system/SKILL.md).
- Existing-code refactor discovery: use [improve-architecture](../../development/improve-architecture/SKILL.md).
- Enforcing approved architecture: use [guardrail-forge](../../development/guardrail-forge/SKILL.md).

## Loop

### 1. Problem

Write a singular decision frame:

```text
Decision:
Why now:
Current state:
Hard constraints:
Non-goals:
What breaks if chosen badly:
Reversibility: easy | moderate | hard
Blast radius:
Decision owner:
```

`hard` includes public/data migrations, trust boundaries, distributed topology, or major operational lock-in. Hard decisions always get the full packet.

### 2. Research

Evidence order:

1. explicit product/SLO/security/compliance constraints
2. accepted domain model and ADRs
3. current source/runtime/test evidence when a repo exists
4. measured workload/cost/incident evidence
5. primary vendor/framework/database docs
6. high-quality engineering literature and documented production experience
7. community opinion as supporting context only

Optional:

- MemBerry for decisions, rejected approaches, failures, provenance, blast radius
- FUGAZI for dependencies, cycles, boundary violations, duplication, complexity
- repo history and PRs
- external research/search

Record facts, assumptions, conflicts, previous attempts, failure model, and what evidence could change the decision. Do not average conflicting evidence away.

### 3. Architecture alternatives

For contested decisions, produce at least two complete, materially different shapes. Prefer reusing [design-panel](../../development/design-panel/SKILL.md) for isolated designers/judge/skeptic.

Each option names:

```text
Shape/ownership
Interfaces/seams
Data flow
Failure model
Migration path
Operational burden
Security implications
Testability
Cost profile
Vendor lock-in
Optimizes for
Deliberately sacrifices
```

If only the library/algorithm changes while boundaries, data flow, and ownership stay the same, it is one architecture.

### 4. Tradeoff analysis

Set criteria before scoring. Typical criteria:

- correctness/invariant strength
- simplicity/locality
- blast radius/testability
- failure isolation
- latency/throughput/headroom
- consistency
- migration cost
- operational burden/observability
- security
- recurring cost
- lock-in
- reversibility
- agent navigability

Hard constraints are pass/fail and cannot be outweighed.

Use a compact matrix:

```text
Criterion | Weight | Option A | Option B | Evidence/uncertainty
```

Do not manufacture numerical precision from qualitative evidence. Strong/medium/weak can be more honest than decimals.

### 5. Adversarial critique

Run a fresh skeptic against the leading option before human choice.

Attack:

- what breaks first?
- which assumption carries the design?
- what happens at 10x load?
- what happens in partial failure?
- where can tenant/auth boundaries leak?
- what migration strands data/callers?
- what is hard to roll back?
- what hidden coupling appears later?
- what operational responsibility was created?
- what cost grows nonlinearly?
- what would make the runner-up better?
- how could a coding agent accidentally violate this architecture?

Each finding gets `resolved`, `accepted-risk`, `refuted`, or `blocked`. An unresolved `blocked` finding prevents acceptance.

### 6. Human choice

Present:

```text
Question
Recommendation and why
Option A
Option B
Tradeoff matrix
Skeptic findings
Known unknowns
Revisit triggers
```

The human accepts/modifies an option, asks for another, defers, or rejects all. Never infer acceptance from silence or deadline pressure.

### 7. Record the decision

Use the repo's ADR convention, or:

```text
ADR-NNNN: <title>
Status: proposed | accepted | rejected | superseded
Decision owner:
Approved by:
Date:
Supersedes / Superseded by:

Decision
Context
Hard constraints
Evidence
Assumptions
Alternatives considered
Tradeoff result
Adversarial findings + dispositions
Consequences
Migration implications
Deterministic architecture consequences
Revisit triggers
Rejected alternatives and why
```

Accepted ADRs may have no unresolved `blocked` skeptic finding. Preserve old ADRs and supersede instead of rewriting history.

### 8. Index in MemBerry

If available, store a compact memory:

```text
type: architecture-decision
decision_id: ADR-00NN
status: accepted
decision: <one sentence>
reason: <load-bearing reason>
rejected: <alternatives + reason>
revisit_when: <triggers>
authority_path: <committed ADR path>
source_commit: <commit>
```

The committed ADR stays authoritative. Memory is queryable recall/provenance.

### 9. Emit Guardrail candidates

Ask whether the accepted consequence can be checked deterministically against source/config/schema/runtime evidence.

If no, stop at the ADR.

If yes, emit:

```yaml
candidate_id: ADR-0012-RULE-01
decision_id: ADR-0012
statement: HTTP route modules may not import persistence adapters directly.
authority:
  adr_path: docs/architecture/decisions/ADR-0012-application-boundary.md
scope_hint:
  include: [src/routes/**]
  exclude: []
enforcement_hint: import-boundary
remediation_hint: route through the approved application interface
```

A candidate is evidence for [guardrail-forge](../../development/guardrail-forge/SKILL.md), not installed policy. Forge owns exact scope, conflict handling, validator code, fixtures, breaker attacks, baselines/exceptions, and independent verification.

## Known pressure rationalizations

| Rationalization | Required response |
|---|---|
| "The answer is obvious; research would only confirm it." | Load-bearing choices get an evidence pass before preference. |
| "Option B can be a strawman because A is clearly better." | A strawman does not test A. Produce a viable different shape or justify why the choice is not contested. |
| "Pick criteria after seeing options." | That enables reverse-engineering values around a favorite. Criteria first. |
| "The designer should judge because it understands the design best." | Understanding is not independence. Maker != checker. |
| "The skeptic found an edge case; implementation can solve it later." | If it affects architecture, disposition it before acceptance. |
| "User said use my judgment, so skip human choice." | Show alternatives/tradeoffs, then the human may explicitly choose the recommendation. |
| "Store it in MemBerry and skip the ADR." | Memory is recall/provenance, not repository authority. |
| "Every ADR should become a Guardrail." | Only deterministic consequences belong in enforcement. |
| "We changed our mind; edit the old ADR." | Preserve history and write a superseding decision. |
| "FUGAZI shows this violation everywhere, so it must be allowed." | Prevalence is evidence of current structure, not intended architecture. |
| "Guardrail will catch bad consequences later." | Guardrail enforces the decision; it cannot rescue a bad decision. |

## Exit condition

Complete when the question is singular/framed, evidence and assumptions are recorded, viable alternatives exist when contested, tradeoffs use predeclared criteria, skeptic findings are dispositioned, the human explicitly chooses or defers, the ADR is written, MemBerry is updated when available, and deterministic consequences are handed to Guardrail as candidates rather than falsely marked enforced.
