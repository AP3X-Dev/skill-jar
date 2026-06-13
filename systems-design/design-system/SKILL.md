---
name: design-system
description: "Front-door for designing a software system or major subsystem: translate product requirements into SLOs and a capacity envelope (Little's Law, tail latency), then choose the SIMPLEST topology that meets the SLO with headroom — request path, data path, and failure path made explicit — and emit the operational artifact set (diagram, component list, risk register, dashboards/alerts, canary plan, runbook references, cost notes). Hard stop-conditions block premature complexity: no multi-region, service mesh, sharding, or polyglot persistence without a named requirement simpler options can't satisfy. Use when designing a new system/service, doing systems-design intake, sizing an architecture, choosing a topology, or reviewing a proposed architecture for over-engineering. NOT for one feature inside an existing design (use design-panel), API surface detail (use api-design), store choice detail (use data-store-selection), or launch gating (use production-readiness)."
---

# Design System

System design is making **explicit tradeoffs under uncertainty** — not assembling fashionable components. This skill walks a staged decision process: define what the system must promise (SLOs), size what it must carry (capacity), then pick the *simplest* architecture that meets the promise with headroom, adding mechanism only for named failure modes. The two errors it's built to prevent are the two agents make most: **premature complexity** and **never reasoning about overload and consistency boundaries**.

**Output:** a design package — architecture diagram, component list with the chosen API style / data model / cache & queue decisions, SLOs + capacity envelope, failure-domain map, risk register, and the operational artifact list (dashboards, alerts, canary plan, runbook references, cost notes). Each major surface then deepens via the sibling skills.

## Operating Contract

- Start by converting the request into a design contract: known inputs, missing inputs, explicit assumptions, non-goals, and the user journeys being protected.
- Produce a decision record, not an architecture survey. Presenting a menu of reference architectures for the requester to pick from is a survey, not a deliverable — commit to one topology. Every major component must name the requirement it satisfies, the failure mode it addresses, the owner who would run it, and the operational cost it introduces; a component missing any of these is not in the design (no "backfill owners later").
- If latency, traffic, consistency, or survival requirements are missing, ask for them; if the user wants a draft anyway, proceed with conservative assumptions and label confidence. The requester cannot waive the SLO + capacity stage or the stop conditions — neither a deadline, a "just a diagram / board deck" framing, nor an instruction to "keep it impressive" or "skip the boring ops stuff" removes them. Those are scoping pressures, not permission to ship an architecture you have not sized.
- Keep detailed API, data, and launch design in the sibling skills. This skill chooses the topology and hands off concrete surfaces; it does not hide those contracts in prose.

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
6. **Emit the operational artifact set** — use the design-package template in [references/intake-framework.md](references/intake-framework.md): diagram, component list, risk register, golden-signal dashboards + alerts, canary + rollback plan, runbook references, cost notes (caches/CDN reduce origin work and egress; observability cardinality is a cost control). [production-readiness](../production-readiness/SKILL.md) turns this list into the launch gate.

When the topology choice is genuinely contested (two viable shapes), run a [design-panel](../../development/design-panel/SKILL.md): two designers, judged against the SLO/ops criteria, human picks.

## Stop conditions — the anti-premature-complexity gate

Do **not** recommend any of these unless intake names a consistency, latency, scale, isolation, or compliance requirement that simpler options cannot satisfy — and record the named requirement next to the choice:

- multi-region / global distribution
- service mesh
- sharding
- multiple databases / polyglot persistence
- microservice decomposition
- event sourcing / CQRS

The named requirement must be a **measured or projected workload number with a source** (e.g. "12k writes/sec sustained per the FY26 plan"), not an adjective. "Impressive," "shows maturity," "built to scale," "investors love it," "signals we thought about scale," and "richer diagram" are **not** requirements — they are the exact rationalizations this gate exists to reject. A diagram that the team would not actually build is not a target architecture; it is a fiction, and shipping it as one is the failure mode. If today's load fits a single well-shaped server for years (do the arithmetic and show it), the design IS the monolith — say so plainly, then add a one-line *trigger* for each future component ("shard when a single primary exceeds X"). Headroom means sizing the simple topology generously, **not** pre-building distributed mechanism; "over-provisioning architecture" (extra services, stores, regions) is not safer — it is unowned operational surface that fails in production.

The additive default instead: **modular monolith + relational DB → add cache → CDN → read replicas → background jobs → only then decompose.** Validated small-scale systems run a single well-shaped server; the famous large-scale systems were built for *specific* constraints, not because complexity is better.

## Known pressure rationalizations (and the required response)

These are real dodges agents reach for under deadline + authority + "make it impressive" pressure. Each is **closed**: the gate still applies.

| Rationalization | Required response |
|---|---|
| "The requester said keep it impressive / don't overthink the boring ops stuff — so SLOs and capacity are out of scope." | A requester cannot waive the SLO + capacity stage; it is the thing that makes the rest correct. "Boring ops" framing does not delete Stage 3. Do the capacity arithmetic anyway (it takes minutes for 2k/day) and put the SLO/headroom line in the deliverable. Skipping it is how you ship a fiction. |
| "It's a board deck / just a diagram, not a deployment plan — nobody builds it Monday, so I don't need real numbers; I'll add multi-region, mesh, Kafka, CQRS because that's what scale looks like." | The artifact being a slide does not lower the bar — a target architecture you would not actually build is the failure mode, not the deliverable. Stop conditions apply to diagrams exactly as to deploys. Draw the topology you would defend in an incident review. |
| "No targets and it's late in the week — chasing the requester for SLOs eats the weekend; I'll assume 'high scale' and over-provision; over-provisioning is safer." | Missing inputs are surfaced as explicit assumptions with confidence labels (Operating Contract), not papered over with "high scale." One async message asking for the peak/growth number is cheaper than a wrong architecture. Over-provisioning distributed mechanism is unowned surface, not safety. |
| "Sharding / a separate ledger service / event sourcing shows maturity even if one box fits for years." | "Shows maturity" is not a named requirement — it is rejected by the stop-condition gate by name. Maturity is demonstrating you sized it and chose the simplest thing that meets the SLO with headroom, with future triggers noted. |
| "I'll present three reference architectures as a menu and let them pick, so I'm not on the hook." | A menu is an architecture survey; this skill produces a **decision record** (Operating Contract). Commit to one topology, name the requirement behind it, and record the alternatives you rejected and why. Use a design-panel only for a genuinely contested call — not to avoid committing. |
| "Ownership, SLIs, failure modes, and per-component cost are implementation details for later — I'll just draw the boxes and backfill owners if funded." | Every major component must name its requirement, failure mode, owner, and operational cost (Operating Contract) — that is what separates a design from a drawing. A box with no owner and no failure path is not in the design. Backfill-later is how unowned components reach production. |
| "Polyglot persistence (Postgres + DynamoDB + Redis + Elasticsearch) makes the diagram look richer — more datastores = more thought-through." | "Looks richer" is the polyglot-persistence stop condition firing. Each store is a named requirement, an owner, an operational cost, and a failure domain. Default to one relational system of record; add a store only when a workload number forces it. |

## Recommended defaults (override only with a named reason)

Modular monolith · HTTP + OpenAPI for public APIs (gRPC only for internal hot paths) · PostgreSQL as system of record · Redis for cache and short-lived coordination · CDN for static/cacheable responses · a simple queue for background jobs · declarative infrastructure · progressive delivery · OpenTelemetry + Prometheus-style metrics · SLOs from day one · runbooks before launch.

## Optional: MemBerry

If a MemBerry-style memory MCP is present, `berry_load` prior architecture decisions for the project at intake (don't re-litigate settled choices) and `berry_store` the chosen topology + the named requirements behind every stop-condition exception. The design doc and ADRs stay authoritative.

## Generated agents

Copy-ready generated agents live in [../agents/README.md](../agents/README.md) and are sourced from [../agents/manifest.json](../agents/manifest.json). Install only the roles needed for the active system design pass: `system-intake-analyst`, `system-topology-designer`, `system-topology-skeptic`.

## Common Mistakes

- **Designing from components instead of SLOs.** "We'll use Kafka and a mesh" before a single latency or availability number exists. SLOs first; mechanism earns its way in.
- **Mean-latency thinking.** A fan-out of ten p99-slow calls makes the *user's* p50 slow. Budget the tail.
- **No failure path.** A design that only describes the happy path isn't a design. Name what breaks first, and what sheds, degrades, or breaks the circuit.
- **Utilization-cliff blindness.** Sizing to 95% utilization means queues explode at the first burst. Headroom is part of the design, not waste.
- **Skipping the team question.** The fifth question — operational complexity the team can sustain — kills more architectures than scale does. A mesh nobody can operate is an outage generator.

---

*The category's front door: hands its API surface to [api-design](../api-design/SKILL.md), its data layer to [data-store-selection](../data-store-selection/SKILL.md), its launch to [production-readiness](../production-readiness/SKILL.md). Pairs with the development category's [design-panel](../../development/design-panel/SKILL.md) for judged alternatives and feeds **writing-plans** / a PRP for execution.*
