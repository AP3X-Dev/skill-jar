---
name: production-readiness
description: "The launch gate that turns a design into an operable service: define SLIs/SLOs and an error-budget policy, build golden-signal dashboards and symptom-based alerts (bounded cardinality, no PII labels), wire liveness/readiness/startup probes correctly, write runbooks for the five standard failures (dependency outage, database failover, cache failure, queue backlog, bad deploy), set the progressive-delivery path (canary, health gates, rollback command), define incident response (roles, safest-reversible-mitigation-first, blameless postmortem), and check cost as a first-class property. No launch without dashboard URLs, alert routes, a rollback command, and one tested failure drill. Use when preparing a service for production, writing SLOs or runbooks, designing alerts/observability, setting up canary deploys, or asking 'is this ready to launch?'. NOT for designing the system itself (use design-system) or diagnosing a live incident's root cause (use diagnose-loop)."
---

# Production Readiness

A service is production-ready when **operators can run it at 3am without its authors** — not when its tests pass. Readiness is a set of artifacts with a runnable gate at the end: reliability targets that govern decisions (SLOs + error budgets), telemetry that answers the three questions (healthy now? what happened? where did it propagate?), rehearsed paths from symptom to action (runbooks, rollback, incident roles), and a release process that exposes a small blast radius before a large one.

**Output:** the readiness package — SLOs + error-budget policy, dashboards + alert routes, probe configuration, the five standard runbooks, canary + rollback plan, incident-response card, postmortem template, cost notes — and a **pass/fail verdict** against the launch gate.

## Operating Contract

- Build a runnable readiness package, not a checklist summary. Every item is either a concrete artifact (URL, command, route, owner, file path, drill result) or a named blocker.
- Page only on symptoms tied to SLO burn or golden signals. Metrics that do not drive an action belong on dashboards or tickets, not paging routes.
- Prove reversibility. A rollback command that has not been executed in a drill is an unverified assumption, not a launch control.
- End with `ready`, `ready after fixes`, or `not ready`; include the smallest fix list that would move the verdict.

## When to Use

- A new service (or a major change) is heading to production.
- Writing SLOs, alerts, runbooks, or deployment safety for an existing service.
- Auditing "is this actually ready?" — the gate works as a review checklist too.

## When NOT to Use

- Designing the architecture → [design-system](../design-system/SKILL.md) (its artifact list is this skill's input).
- Root-causing a live failure → [diagnose-loop](../../development/diagnose-loop/SKILL.md); this skill *writes* the runbook that incident follows.

## The readiness pillars

Templates and checklists for each: [references/readiness-playbook.md](references/readiness-playbook.md).

1. **SLOs + error budgets.** Pick SLIs per user journey; set SLOs the team can defend — 100% is neither realistic nor desirable; the gap is the **error budget** that governs launch velocity (budget healthy → ship; budget burning → stabilize). Reliability becomes a decision system, not a dashboard.
2. **Telemetry — three signals.** Metrics (healthy now?), logs (what happened?), traces (where did latency/errors propagate?). Defaults: OpenTelemetry instrumentation, Prometheus-style metrics, histogram buckets shaped around the SLO. **Cardinality is the cost and reliability control** — never user IDs, emails, or raw URLs as labels.
3. **Alerts — symptoms, not causes.** Page on SLO burn and golden-signal symptoms; everything else is a dashboard or ticket. Every page must be *actionable* — it names a runbook. Alert fatigue is a reliability failure.
4. **Probes.** Liveness ("restart me") ≠ readiness ("don't route to me yet") — conflating them turns a dependency blip into a restart storm. Startup probes for slow boots. Readiness reflects *dependency* readiness.
5. **Runbooks — the five standard failures.** Dependency outage · database failover · cache failure · queue backlog · bad deploy. Each: ownership, SLO impact, first checks, safe mitigations, rollback steps, escalation path, evidence capture.
6. **Progressive delivery.** Artifact immutability → small slice (canary) → health gates on SLO/golden signals → promote or **auto-rollback**. The rollback command is written, tested, and one step. Schema/state/traffic-policy changes always get a plan + rollback + canary.
7. **Incident response.** Roles named in advance (incident lead, comms lead) · freeze unrelated changes · **safest reversible mitigation first** (rollback, traffic shift, rate-limit, serve-stale, feature off — prefer mitigations that reduce load and preserve correctness over preserving all functionality under overload) · evidence capture · blameless postmortem with owned, dated actions.
8. **Cost.** Size to measured demand; caches/CDN reduce origin work and egress; observability retention/cardinality tiers are a budget decision. Cheapest-service shopping isn't the goal — value per spend is.

## The launch gate (runnable)

No production launch without **all** of:

- [ ] SLOs + error-budget policy written and agreed
- [ ] Dashboard URLs live (golden signals + capacity panels)
- [ ] Alert routes wired; every page is symptom/SLO-based and names a runbook (resource-utilization alerts do not satisfy this; they are dashboard panels)
- [ ] Liveness/readiness/startup probes configured and correct
- [ ] The five standard runbooks written — each with named first checks, named safe mitigations, and concrete rollback steps for *this* service (a stub with "investigate and roll back if needed" is not a runbook)
- [ ] Rollback command exists and was **executed against this service in a drill** (reuse of a "standard path" is an assumption until executed here)
- [ ] **At least one failure drill run** (kill a dependency, fail over the DB, or roll back a canary — for real, with the failure injected)
- [ ] A **named** owner and escalation route on file; postmortem template on file (`TBD`/`defaults to a channel` is an empty box, not a green one)

A box is green only when the named artifact exists and the named action was performed — not when the item was "thought about" or planned to follow. A red box is a blocker, not a footnote: "we'll add it week 1" leaves it red. The checklist is the contract, not a thinking aid; the green check you paste means *done*, and you sign it.

### Known pressure rationalizations

A near-launch deadline manufactures these dodges. Each leaves the corresponding box **red** — meet the gate or report `not ready`; do not self-certify green.

| Rationalization (the dodge) | Required response |
|---|---|
| "Staging ran clean for days with synthetic traffic — that *is* my failure test." | A clean soak is observation, not a drill. The gate requires an **injected** failure (kill the dependency, fail the DB, throttle the upstream) and an observed recovery. No injection → drill box stays red. |
| "Rollback is the same `rollout undo`/redeploy path every service uses — it obviously works, I don't need to run it." | "Standard path" is the most common untested rollback. Reversibility is *proven per service*, not inherited. Not executed against this service → red. |
| "Wire CPU>80% / mem>90% now; add SLO/burn-rate alerts week 1 — can't set a latency-burn threshold with no prod data." | Resource alerts are cause-based dashboard panels, not the paging gate. Ship with **symptom/SLO-burn** alerts using a defensible launch target (start conservative, tune on real traffic) — the absence of a baseline is not a reason to page on the wrong signal. SLO alert unwired → red. |
| "Put `customer_id`/email/`charge_id` in the alert labels so on-call can triage faster." | PII and high-cardinality identifiers as labels are forbidden regardless of triage convenience — they leak data and can take down the monitoring system. Put the *link to the dashboard/trace query* in the annotation; identifiers live behind that link, not on the alert. |
| "A stub runbook with `Owner: TBD` and 'investigate and roll back' beats a perfect one that blocks launch." | A stub is not a written runbook (gate item). Each of the five needs named first checks, named mitigations, and this service's concrete rollback steps. Stub → runbook box red. |
| "`Owner: TBD` is honest because the rotation isn't finalized." | Honest, and still a blocker. An unassigned owner means no one is accountable at 3am. Name an interim owner by person/role before launch, or the owner box is red. |
| "It's a one-way-door date the VP announced; cost of slipping outweighs an untested failure mode — ship and harden in-flight." | Deadline pressure does not flip a red box green. State the verdict (`not ready` / `ready after fixes`) plus the smallest fix list, and escalate the ship-with-known-gaps decision to the deadline owner. You surface the tradeoff; you do not silently absorb it by marking green. |
| "Green means 'we thought about each item' + a footnote that the drill and SLO alerts follow." | Green means the artifact exists and the action ran. "Considered it" is not done; a footnote deferring a gate item is a red box with extra words. Report the real verdict. |

## Generated agents

Copy-ready generated agents live in [../agents/README.md](../agents/README.md) and are sourced from [../agents/manifest.json](../agents/manifest.json). Install only the roles needed for the active readiness pass: `readiness-slo-operator`, `readiness-runbook-writer`, `readiness-launch-reviewer`.

## Common Mistakes

- **Targets without budgets.** An SLO nobody spends is a poster. The error budget must gate launch velocity, or reliability and delivery stay at war.
- **Cause-based alert sprawl.** Paging on every internal hiccup buries the one symptom that matters. Page on user-visible symptoms; investigate causes from dashboards.
- **Liveness checks that probe dependencies.** The DB blips, every pod restarts, the blip becomes an outage. Liveness is "am I wedged"; readiness owns dependencies.
- **Untested rollback.** A rollback command first run during an incident fails during the incident. Drill it.
- **Unbounded label cardinality.** One `user_id` label can take down the monitoring system that was supposed to save you.
- **Postmortems as paperwork.** Unowned, undated action items repeat the incident. Blameless ≠ consequence-free.

---

*Closes the loop the category opens: [design-system](../design-system/SKILL.md) names the artifacts, this skill builds and gates them. The incident runbooks hand live defects to [diagnose-loop](../../development/diagnose-loop/SKILL.md); continuous post-launch hardening is [optimization-loop](../../development/optimization-loop/SKILL.md)'s job.*
