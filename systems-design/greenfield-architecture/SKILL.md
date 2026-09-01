---
name: greenfield-architecture
description: "Use when starting a new software product, service, or major subsystem before meaningful implementation exists and the project needs an explicit architecture that coding agents can safely build inside. Starts from requirements plus a domain/data model, separates derived invariants from architecture choices, sizes the system, resolves load-bearing decisions, emits an approved architecture constitution and minimal skeleton, then hands the bootstrap repository to guardrail-forge. NOT for established-repo discovery, ordinary feature design, or refactoring."
---

# Greenfield Architecture

Turn a product idea and domain/data model into an explicit architecture that coding agents can safely build inside.

The data model is the seed, not the whole architecture. It can strongly imply ownership, tenancy, lifecycle, integrity, and access invariants. It cannot by itself decide module boundaries, dependency direction, runtime topology, consistency, integration seams, failure handling, or operational ownership.

**Output:** an approved architecture constitution, ADRs, a minimal executable skeleton, and a Guardrail Forge handoff packet. Stop before substantial product implementation.

## Operating contract

1. **Model first, never model-only.** Extract entities, relationships, ownership, lifecycle, invariants, trust/tenant roots, state transitions, and read/write shape. Label every architecture statement `derived`, `assumed`, or `chosen`.
2. **Requirements earn architecture.** Every major component, datastore, queue, cache, service split, region, or framework abstraction names the requirement or failure mode it satisfies.
3. **Simplest viable topology wins.** Prefer a modular monolith and one relational system of record unless named scale, isolation, latency, consistency, compliance, or organizational constraints force more.
4. **Human direction is authority.** The agent may derive invariants and recommend architecture, but load-bearing choices become authoritative only after explicit human acceptance.
5. **No fake Guardrail authority.** Do not write blocking Guardrail rules directly from suggestions. Create approved decisions and a real skeleton first, then hand the repository to `guardrail-forge` for independent discovery and validator creation.
6. **Skeleton before product.** Build only enough source, configuration, schema, interfaces, and tests to make the architecture real and inspectable.
7. **Uncertainty stays visible.** Missing traffic, retention, consistency, compliance, or failure requirements become explicit assumptions with confidence.
8. **Rejected directions are evidence.** Record load-bearing rejection reasons so future agents do not re-propose them without changed conditions.

## When to use

- Empty or bootstrap-only repository.
- New product/service/subsystem needs architecture before implementation.
- User has a domain/data model and wants a safe system shape around it.
- Autonomous coding agents will do substantial implementation.
- Project should enter Guardrail Forge almost from day one.

## When NOT to use

- Established repo whose architecture must be discovered/enforced: use [guardrail-forge](../../development/guardrail-forge/SKILL.md).
- Feature/component design: use [design-panel](../../development/design-panel/SKILL.md).
- Existing architecture refactor: use [improve-architecture](../../development/improve-architecture/SKILL.md).
- System sizing/topology only: use [design-system](../design-system/SKILL.md).
- One unresolved load-bearing choice: use [architecture-decision-loop](../architecture-decision-loop/SKILL.md).

## Process

### 1. Frame the product contract

Capture product goal, user journeys, non-goals, team/agent development model, latency/availability/durability targets, traffic, retention, privacy/compliance, cost envelope, integrations, deployment constraints, and compatibility requirements.

If numbers are missing, use conservative assumptions and label them. Use [design-system](../design-system/SKILL.md) for SLO/capacity reasoning rather than inventing distributed infrastructure from intuition.

### 2. Build the domain contract

For each important concept record:

```text
Name
Meaning/responsibility
Owner or tenant root
Identity
Relationships/cardinality
Lifecycle/deletion
Invariants
State transitions
Security/privacy classification
Source of truth
Read/write shape
External identifiers/integrations
```

Then derive only obligations that truly follow from accepted domain facts, for example:

```text
DERIVED-001: Every Lead belongs to exactly one Dealer.
DERIVED-002: Appointment and Lead resolve to the same tenant.
DERIVED-003: Deleting a tenant cannot silently orphan tenant-owned data.
```

Do not infer code architecture from entity count. Ten entities do not imply ten services. A foreign key does not imply a module seam. An ORM class is not automatically the domain model.

### 3. Separate derived, assumed, chosen

| State | Meaning | Example |
|---|---|---|
| `derived` | Follows from accepted domain facts | Lead is tenant-owned |
| `assumed` | Needed to proceed but not confirmed | Peak is 20 req/s |
| `chosen` | Architecture judgment | Routes call application modules, not persistence directly |

Never launder an agent preference into a requirement.

### 4. Choose topology from requirements

Use `design-system` for SLOs, capacity, request/data/failure paths, and simplest viable topology.

Default direction unless evidence forces otherwise:

```text
client
  -> HTTP/API boundary
  -> application modules
  -> domain rules
  -> repositories/integration adapters
  -> PostgreSQL + external systems
```

Queues, caches, replicas, search, microservices, event sourcing, sharding, multi-region, and service meshes require named reasons.

### 5. Resolve load-bearing choices

A choice is load-bearing when it changes module ownership/dependency direction, public API, schema/format, tenancy/auth/trust, transaction/consistency boundary, sync/async behavior, datastore ownership, integration seam, deployment topology, failure domain, major recurring cost, or vendor lock-in.

Run [architecture-decision-loop](../architecture-decision-loop/SKILL.md) for each genuinely contested load-bearing choice. Do not use the heavy loop for cosmetic folders, naming, or easily reversible local details.

### 6. Write the architecture constitution

Recommended authority package:

```text
docs/architecture/
  00-context.md
  01-domain-model.md
  02-system-topology.md
  03-module-map.md
  04-dependency-rules.md
  05-data-trust-tenancy.md
  06-runtime-failure-paths.md
  07-guardrail-candidates.md
  decisions/
    ADR-0001-....md

.architecture-seed/
  architecture-seed.yaml
```

The machine-readable seed contains accepted facts, assumptions, decision references, and Guardrail candidates. It is a handoff aid, not enforcement authority.

Every Guardrail candidate should name a decision/invariant, statement, scope hint, evidence, enforcement hint, and remediation hint.

### 7. Build the minimal executable skeleton

Create only enough structure to prove the chosen architecture:

- package/module roots
- composition root
- core seams/interfaces
- initial accepted schema/migrations
- tenant/auth context seam when applicable
- repository/integration adapter interfaces
- test layout
- lint/type/build configuration
- one thin walking-skeleton path when useful

Run build/test/type/lint. If FUGAZI is available, run read-only boundary/cycle/health checks. FUGAZI supplies structural evidence, not architecture authority.

### 8. Pre-Guardrail gate

Verify:

- every proposed rule points to an accepted decision or derived invariant
- assumptions are still marked assumptions
- no component exists only because it is fashionable
- skeleton matches constitution
- project gates pass
- public/data/security boundaries have owners
- Guardrail candidates are proposals, not falsely marked enforced

### 9. Hand off to Guardrail Forge

The project now contains real source, executable wiring, tests/configuration, approved decisions, and architecture documentation. Run [guardrail-forge](../../development/guardrail-forge/SKILL.md) against this bootstrap repository.

Forge still starts at Level 1 read-only discovery. The constitution is evidence, not automatic validator authority. Conflicts between source, decisions, and docs become decision items. Only Guardrail Forge Level 2 may install and pressure-test blocking rules.

## Known pressure rationalizations

| Rationalization | Required response |
|---|---|
| "We have the ERD, so architecture is basically done." | ERDs do not define dependencies, topology, consistency, integration seams, or failure handling. Continue. |
| "Twelve entities means twelve services." | Entity count is not service decomposition. Require a named process-boundary reason. |
| "Claude can pick architecture and Guardrail will make it safe." | Guardrail can faithfully enforce a bad decision. Human acceptance comes first. |
| "Generate Guardrail policy from the docs and skip Forge." | Docs are evidence. Build the skeleton and let Forge independently scope/test enforcement. |
| "Adding Kafka/Redis/search now is cheaper than later." | Future convenience is not a current requirement. Record a future trigger instead. |
| "The ORM schema is the domain model." | Persistence shape does not capture ownership, lifecycle, invariants, or authorization. |
| "The skeleton runs, so start features before review." | Wiring proof is not architecture approval. Load-bearing decisions must be accepted first. |
| "tenant_id defines authorization." | Tenant identity supports isolation but does not define allowed actions. Authorization is separate. |
| "Microservices make coding agents safer because services are smaller." | Distributed boundaries add contracts, failure modes, deployment state, and coordination. Agent navigability alone is insufficient. |

## Optional MemBerry

When available, load prior product/domain/architecture decisions at intake and store accepted decisions plus rejected alternatives with their reasons and committed ADR provenance. Repository ADRs/source remain authority on conflict.

## Exit condition

Complete only when the domain contract exists, assumptions/SLOs are explicit, load-bearing choices are accepted and recorded, architecture constitution exists, minimal skeleton represents it, project gates pass, Guardrail candidates exist, and the repository is ready for Guardrail Forge Level 1.

Do not claim architecture is enforced until Guardrail Forge Level 2 verification passes.
