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
2. **Safety & idempotency per endpoint** — reads safe; side-effecting endpoints get **idempotency keys** so retries can't duplicate effects. *Any endpoint that will be auto-retried must be idempotent — non-negotiable.* If a client retries (mobile/flaky network) and the effect is money or other non-reversible state, the dedup store ships in v1 — it is the contract, not a v2 optimization. "Double-charges basically never happen in testing" is not evidence; a single retried timeout is the bug.
3. **Deadlines + retry budgets** — every call carries an explicit deadline (context timeout); retries use exponential backoff + jitter under a budget. The default HTTP client has no deadline — shipping it means one slow upstream hangs every caller. Bounded deadline + retry budget on every outbound call is part of v1, not "premature tuning"; metrics tell you it already broke. Watch layered retries (client + gateway + mesh) — they multiply into retry storms.
4. **Pagination** — cursor-based for anything unbounded; offset pagination breaks under concurrent writes and degrades on deep pages. "Thousands of rows" and "writes happen while paging" is exactly the unbounded+concurrent case — `OFFSET/LIMIT` is trivial to write and wrong here; ship cursors. The mobile team integrating against page numbers now is the reason to fix the contract before launch, not after.
5. **Versioning = additive evolution** — add optional fields; never repurpose or remove without a deprecation window. Breaking changes are a new major surface.
6. **Error schema** — one machine-readable shape (code, type, message, request/correlation id, retryability) across all endpoints. A *new public* endpoint defines the envelope even if existing services lack one — "consistency" with hand-rolled inline strings means clients parse prose forever; the new surface sets the standard, it doesn't inherit the gap.
7. **Auth + rate limits + abuse review** — TLS, OAuth-class authn/z, object- and property-level access checks, per-principal limits. A public endpoint validates the caller's token and scope at the handler; reading a gateway-set header (`X-User-Id`) as trusted identity is a spoofable trust boundary — verify it, don't assume it. Per-customer rate limits + `429` semantics are part of the contract from v1, not a gateway "eventually" — a public/mobile endpoint is reachable abuse surface, and the limit defines client retry behavior. Baseline: OWASP API Security Top 10.
8. **Cacheability** — which responses are cacheable, the key dimensions, TTL/staleness budget (feeds CDN policy).
9. **Ownership + observability** — every endpoint maps to an owner, an SLI, and a dashboard.
10. **Multi-service writes** — transactional outbox or saga, never ad-hoc distributed transactions.

## Known pressure rationalizations

Deadline pressure ("demo Monday") manufactures reasons to drop the exact promises that make a public, retried, money-moving API survive. Each below is a real failure dressed as pragmatism. The required response is non-negotiable for a new public endpoint.

| Rationalization (the dodge) | Required response |
|---|---|
| "Idempotency keys are a v2 concern; double-charges basically never happen in testing." | A side-effecting endpoint a client will retry is unsafe without an idempotency key + dedup store **in v1**. "Never in testing" isn't evidence; one retried timeout duplicates the charge. |
| "Mobile retries but the provider usually succeeds; a dedup table is a whole extra day." | The named retrier (flaky-network mobile) is precisely the trigger. The dedup store is the contract, not optional scope — cost doesn't waive the safety promise. |
| "Offset/limit is what every example uses; cursor pagination is over-engineering." | Thousands of rows + concurrent writes = unbounded+concurrent. `OFFSET/LIMIT` skips/duplicates rows and degrades deep. Ship cursors before the client integrates against page numbers. |
| "Match the repo's inline error strings; an envelope is nice-to-have since other services lack one." | A new public endpoint defines the machine-readable error envelope (code/type/message/request_id/retryability). Inheriting the gap forces clients to parse prose. |
| "No deadlines/retry budget; default `http.Client` is fine — premature tuning." | Every outbound call gets an explicit deadline + bounded retries in v1. The default client has no timeout; one slow upstream (200ms–2s, occasional timeout) hangs every caller. Metrics report the outage, they don't prevent it. |
| "Auth is handled — the gateway sets `X-User-Id` and we trust it." | A gateway-set header is spoofable if reachable directly. The public handler validates the token + scope itself; trust boundaries are verified, not assumed. |
| "Rate limiting belongs at the gateway eventually; abuse isn't realistic before the demo." | A public/mobile endpoint is abuse surface from day one. Per-customer limits + `429` are part of the v1 contract — the limit also defines correct client retry/backoff. |
| "REST-over-JSON because that's what mobile expects; `/v1` in the path is enough of a compatibility story." | Protocol choice (HTTP+JSON for a public/mobile API) is fine — but a version segment is not a compatibility plan. State the additive-evolution + deprecation policy: optional-field-only changes, no field repurposing, a deprecation window before any break. |

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
