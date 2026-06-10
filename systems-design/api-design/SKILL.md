---
name: api-design
description: "Design an API surface that survives production: choose the protocol by consumer shape (HTTP+OpenAPI default for public/partner APIs, gRPC for latency-sensitive internal RPC, GraphQL only for governed graph-shaped client reads, async events when decoupling in time beats a synchronous answer), then pin the contract — safety and idempotency semantics, cursor pagination, deadlines and retry budgets, additive versioning, error schema, auth, rate limits, cacheability — and gate releases on backward compatibility. Use when designing or reviewing an API, choosing REST vs gRPC vs GraphQL vs events, making endpoints safe to retry, or planning schema evolution. NOT for the whole system topology (use design-system), store selection (use data-store-selection), or implementing handlers (just build them)."
---

# API Design

An API is a promise about semantics, not a list of routes. Most production API pain traces to promises never made explicit: what's safe to retry, what a deadline is, how the schema evolves, what an error looks like, who may call how often. This skill chooses the protocol by **consumer shape**, then forces every one of those promises into the contract *before implementation* — because retrofitting idempotency or versioning onto a public API is a breaking change.

**Output:** a contract package — protocol choice with rationale, the schema (OpenAPI / proto / GraphQL SDL), idempotency + retry semantics per endpoint, pagination/error/auth/rate-limit policy, cacheability notes, and the backward-compatibility release gate.

## Operating Contract

- Treat the API as a versioned interface contract. For each operation, write the caller, trust boundary, inputs, outputs, side effects, auth scope, rate limit, deadline, retry policy, and observability signal.
- Side-effecting operations must declare idempotency behavior before retries are allowed. If the effect cannot be safely replayed, the contract says no automatic retry.
- Prefer machine-checkable artifacts: OpenAPI/proto/SDL, schema examples, enum lists, error envelope, compatibility notes, and conformance tests. Avoid hand-wavy endpoint prose.
- End with a release verdict: `ship`, `ship after named fixes`, or `block`, with blockers tied to backward compatibility, safety, abuse, or operability.

## When to Use

- Designing a new API or reviewing one before it ships.
- Choosing between REST, gRPC, GraphQL, or async events.
- "How do we make this endpoint safe to retry?" / "How do we version this without breaking clients?"

## When NOT to Use

- Whole-system topology → [design-system](../design-system/SKILL.md). Store/queue internals → [data-store-selection](../data-store-selection/SKILL.md).
- Implementing the handlers — just build them against the contract.

## Protocol choice — by consumer shape, not fashion

| Consumer shape | Default | Why |
|---|---|---|
| Public / partner / broadly consumed | **HTTP + JSON + OpenAPI** | HTTP already standardizes method safety, idempotency, status codes, intermediaries, caching; tooling is universal |
| Internal latency-sensitive service-to-service | **gRPC** | Strong typing, codegen, deadlines, built-in LB/health/tracing hooks |
| Multiple clients needing flexible graph-shaped reads | **GraphQL** — only with schema governance, complexity limits, resolver discipline | Reduces over-fetching; pays for it in caching + resolver complexity |
| Decoupling in time beats a synchronous answer | **Queue/stream + outbox** | Loose coupling, retry/backlog absorption; pays in eventual consistency |

Decision tree + the full playbook: [references/api-playbook.md](references/api-playbook.md). When two styles genuinely compete, run a [design-panel](../../development/design-panel/SKILL.md) on the contested surface.

## The contract checklist (pin before implementation)

1. **Consumers + trust boundaries** — who calls, from where, with what auth.
2. **Safety & idempotency per endpoint** — reads safe; side-effecting endpoints get **idempotency keys** so retries can't duplicate effects. *Any endpoint that will be auto-retried must be idempotent — non-negotiable.*
3. **Deadlines + retry budgets** — every call carries a deadline; retries use exponential backoff + jitter under a budget. Watch layered retries (client + gateway + mesh) — they multiply into retry storms.
4. **Pagination** — cursor-based for anything unbounded; offset pagination breaks under concurrent writes.
5. **Versioning = additive evolution** — add optional fields; never repurpose or remove without a deprecation window. Breaking changes are a new major surface.
6. **Error schema** — one machine-readable shape (code, message, correlation id, retryability) across all endpoints.
7. **Auth + rate limits + abuse review** — TLS, OAuth-class authn/z, object- and property-level access checks, per-principal limits. Baseline: OWASP API Security Top 10.
8. **Cacheability** — which responses are cacheable, the key dimensions, TTL/staleness budget (feeds CDN policy).
9. **Ownership + observability** — every endpoint maps to an owner, an SLI, and a dashboard.
10. **Multi-service writes** — transactional outbox or saga, never ad-hoc distributed transactions.

## Release gate

No public API change ships without: backward-compatibility assessment · schema/OpenAPI updated · operation matrix completed · retry/idempotency review · abuse & resource-consumption review · conformance/eval cases for the changed contract. A gate failure is a redesign, not a footnote.

## Generated agents

Copy-ready generated agents live in [../agents/README.md](../agents/README.md) and are sourced from [../agents/manifest.json](../agents/manifest.json). Install only the roles needed for the active API design pass: `api-contract-designer`, `api-compatibility-reviewer`, `api-abuse-reviewer`.

## Common Mistakes

- **Auto-retrying non-idempotent writes.** The classic duplicate-charge bug. Idempotency keys first, retries second.
- **Choosing GraphQL for one client.** You inherit schema governance, query-complexity limits, and resolver N+1 management — worth it for many flexible clients, pure cost for one.
- **Offset pagination on live data.** Rows shift under the iterator; use cursors.
- **Per-endpoint error formats.** Clients end up parsing prose. One error schema, everywhere.
- **Versioning by mutation.** Repurposing a field's meaning breaks clients silently — the worst kind of break. Additive only.

---

*Deepens the API surface that [design-system](../design-system/SKILL.md) chose; event-style contracts hand their delivery semantics to [data-store-selection](../data-store-selection/SKILL.md)'s queue patterns; launch is gated by [production-readiness](../production-readiness/SKILL.md).*
