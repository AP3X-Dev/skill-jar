# Intake framework

Worksheets for [design-system](../SKILL.md): the intake SOP, the capacity math, the five questions, and the stop-condition register. Self-contained.

## Intake SOP

**Inputs required** (ask for what's missing; assume + label what's unanswerable):

| Input | Why it changes the design |
|---|---|
| Product goal + primary user journeys | Defines the SLIs worth promising |
| Target latency & availability | The SLO — everything else serves this |
| Traffic profile (steady, peak, growth) | Capacity envelope + headroom |
| Data retention / compliance | Storage, residency, deletion paths |
| Budget envelope | Cost is a first-class property, not an afterthought |
| Team size + change cadence | The operational-complexity ceiling |

**Agent actions:** state assumptions → identify read path, write path, background path → define SLIs/proposed SLOs → estimate throughput + concurrency → list stateful components → identify critical dependencies → choose the simplest topology that meets the SLO → describe failure domains → define observability/release/rollback artifacts.

**Required outputs:** architecture diagram · component list · API style · primary data model · cache + queue choices · scaling model · risk register · dashboards + alerts · canary plan · runbook references · cost notes.

## Capacity worksheet

- **Little's Law:** `concurrency L = arrival rate λ × service time W`. 500 RPS × 0.2s = 100 concurrent requests — size worker pools/connections from this, not vibes.
- **Tail latency:** design to p95/p99. In a fan-out, the slowest of N calls sets user latency: at 10 parallel calls each with 1% slow requests, ~10% of user requests hit a slow path. Mitigations where the budget demands them: tighter per-call deadlines, hedged requests, smaller fan-outs.
- **Headroom:** size steady-state from *peak* arrival, keep utilization low enough that bursts queue briefly instead of cascading. Utilization cliffs are a design risk, not just an autoscaling setting.
- **Overload plan:** beyond headroom — rate limits at the edge, load shedding with a defined degraded mode, backpressure on queues. "Reduce load and preserve correctness" beats "preserve all functionality under overload."

## The five questions (in order)

1. **What is the user-visible SLO and acceptable consistency model?**
2. **What are the dominant read and write patterns?**
3. **What are steady-state and peak loads?**
4. **What failures must the system survive?** (node, AZ, dependency, region? name them)
5. **What operational complexity can the team actually sustain?**

If a proposed component doesn't improve one of these five dimensions, it is premature — cut it.

## Stop-condition register

Copy into the design doc; every exception carries its named requirement:

```md
## Complexity exceptions
| Mechanism | Default | Used here? | Named requirement that simpler options can't satisfy |
|---|---|---|---|
| Multi-region        | NO | yes/no | <e.g. residency law / regional failover SLO> |
| Service mesh        | NO | yes/no | <e.g. mTLS+policy across 30+ services> |
| Sharding            | NO | yes/no | <e.g. write rate exceeds single-primary ceiling, measured> |
| Polyglot persistence| NO | yes/no | <e.g. search + OLTP genuinely distinct access patterns> |
| Microservices       | NO | yes/no | <e.g. independent scaling/deploy boundary proven> |
| Event sourcing/CQRS | NO | yes/no | <e.g. audit-grade history is a product requirement> |
```

## Failure-path checklist (per critical dependency)

- Timeout set (and shorter than the caller's budget)? Retry **budget** (not bare retries — layered retries amplify into storms)? Exponential backoff + jitter?
- Circuit breaker / outlier ejection where the dependency can brown-out?
- Degraded mode defined (serve stale, partial response, feature off)?
- Idempotency guaranteed wherever a retry can duplicate a side effect?
- Blast radius: which user journeys die when THIS dies — and which must not?

## Resilience vocabulary (use these terms exactly)

bulkheads · rate limits · retries with jitter · retry budgets · circuit breakers · backpressure · load shedding · hedged requests · degraded modes · failure domains · blast radius · graceful degradation
