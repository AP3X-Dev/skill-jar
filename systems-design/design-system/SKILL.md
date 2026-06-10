---
name: design-system
description: "Front-door for designing a software system or major subsystem: translate product requirements into SLOs and a capacity envelope (Little's Law, tail latency), then choose the SIMPLEST topology that meets the SLO with headroom — request path, data path, and failure path made explicit — and emit the operational artifact set (diagram, component list, risk register, dashboards/alerts, canary plan, runbook references, cost notes). Hard stop-conditions block premature complexity: no multi-region, service mesh, sharding, or polyglot persistence without a named requirement simpler options can't satisfy. Use when designing a new system/service, doing systems-design intake, sizing an architecture, choosing a topology, or reviewing a proposed architecture for over-engineering. NOT for one feature inside an existing design (use design-panel), API surface detail (use api-design), store choice detail (use data-store-selection), or launch gating (use production-readiness)."
---

# Design System

System design is making **explicit tradeoffs under uncertainty** — not assembling fashionable components. This skill walks a staged decision process: define what the system must promise (SLOs), size what it must carry (capacity), then pick the *simplest* architecture that meets the promise with headroom, adding mechanism only for named failure modes. The two errors it's built to prevent are the two agents make most: **premature complexity** and **never reasoning about overload and consistency boundaries**.

**Output:** a design package — architecture diagram, component list with the chosen API style / data model / cache & queue decisions, SLOs + capacity envelope, failure-domain map, risk register, and the operational artifact list (dashboards, alerts, canary plan, runbook references, cost notes). Each major surface then deepens via the sibling skills.

## When to Use

- A new system, service, or major subsystem needs an architecture.
- "How should we build this?" at the topology level — workload shape, data path, scaling model.
- Reviewing a proposed architecture for over-engineering or missing failure reasoning.

## When NOT to Use

- One feature inside an established architecture — [design-panel](../../development/design-panel/SKILL.md) (this skill *uses* its judged-alternatives panel for contested topology calls).
- The API contract itself → [api-design](../api-design/SKILL.md); the store choice → [data-store-selection](../data-store-selection/SKILL.md); the launch gate → [production-readiness](../production-readiness/SKILL.md).
- Reimplementing an existing system — **clean-room**.

## The staged process

Run the stages in order; each produces a recorded artifact. Full worksheets in [references/intake-framework.md](references/intake-framework.md).

1. **Intake** — gather: product goal, primary user journeys, target latency & availability, expected traffic profile (steady + peak), data retention, compliance constraints, budget envelope, team size, change cadence. **State every assumption explicitly** — hidden assumptions are the main source of bad designs.
2. **Classify the workload shape** — public API, internal RPC, batch, stream, user-facing read path, write-heavy transactional path, event pipeline (usually a mix; name each path).
3. **Define SLOs + capacity envelope** — SLIs/SLOs per user-visible journey; throughput/concurrency from Little's Law (`L = λ × W`); design to **p95/p99 budgets, not means** — tail latency dominates fan-out systems. Size steady-state from measured/estimated peak with headroom so queues don't explode under burst.
4. **Choose the simplest topology that meets the SLO** — the five questions, in order: *user-visible SLO & acceptable consistency model? dominant read/write patterns? steady + peak load? which failures must it survive? what operational complexity can the team actually sustain?* If a component doesn't improve one of those five, it's premature. Defaults-by-scale tables: [references/defaults-and-cases.md](references/defaults-and-cases.md).
5. **Design the three paths** — for each: **request path** (API style, LB layer, cache position), **data path** (store, replication, partitioning, consistency zone), **failure path** (what breaks first; timeouts + retry budgets + circuit breakers + load shedding + degraded modes; failure domains and blast radius).
6. **Emit the operational artifact set** — diagram, component list, risk register, golden-signal dashboards + alerts, canary + rollback plan, runbook references, cost notes (caches/CDN reduce origin work and egress; observability cardinality is a cost control). [production-readiness](../production-readiness/SKILL.md) turns this list into the launch gate.

When the topology choice is genuinely contested (two viable shapes), run a [design-panel](../../development/design-panel/SKILL.md): two designers, judged against the SLO/ops criteria, human picks.

## Stop conditions — the anti-premature-complexity gate

Do **not** recommend any of these unless intake names a consistency, latency, scale, isolation, or compliance requirement that simpler options cannot satisfy — and record the named requirement next to the choice:

- multi-region / global distribution
- service mesh
- sharding
- multiple databases / polyglot persistence
- microservice decomposition
- event sourcing / CQRS

The additive default instead: **modular monolith + relational DB → add cache → CDN → read replicas → background jobs → only then decompose.** Validated small-scale systems run a single well-shaped server; the famous large-scale systems were built for *specific* constraints, not because complexity is better.

## Recommended defaults (override only with a named reason)

Modular monolith · HTTP + OpenAPI for public APIs (gRPC only for internal hot paths) · PostgreSQL as system of record · Redis for cache and short-lived coordination · CDN for static/cacheable responses · a simple queue for background jobs · declarative infrastructure · progressive delivery · OpenTelemetry + Prometheus-style metrics · SLOs from day one · runbooks before launch.

## Optional: MemBerry

If a MemBerry-style memory MCP is present, `berry_load` prior architecture decisions for the project at intake (don't re-litigate settled choices) and `berry_store` the chosen topology + the named requirements behind every stop-condition exception. The design doc and ADRs stay authoritative.

## Common Mistakes

- **Designing from components instead of SLOs.** "We'll use Kafka and a mesh" before a single latency or availability number exists. SLOs first; mechanism earns its way in.
- **Mean-latency thinking.** A fan-out of ten p99-slow calls makes the *user's* p50 slow. Budget the tail.
- **No failure path.** A design that only describes the happy path isn't a design. Name what breaks first, and what sheds, degrades, or breaks the circuit.
- **Utilization-cliff blindness.** Sizing to 95% utilization means queues explode at the first burst. Headroom is part of the design, not waste.
- **Skipping the team question.** The fifth question — operational complexity the team can sustain — kills more architectures than scale does. A mesh nobody can operate is an outage generator.

---

*The category's front door: hands its API surface to [api-design](../api-design/SKILL.md), its data layer to [data-store-selection](../data-store-selection/SKILL.md), its launch to [production-readiness](../production-readiness/SKILL.md). Pairs with the development category's [design-panel](../../development/design-panel/SKILL.md) for judged alternatives and feeds **writing-plans** / a PRP for execution.*
