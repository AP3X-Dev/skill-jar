---
name: data-store-selection
description: "Choose and shape the data layer from access patterns, not brand loyalty: write the dominant read/write patterns first, name the required consistency model, then pick relational (joins, transactions, multi-row invariants — the default), document, key-value/wide-column (keyed access at scale), or Spanner-class global SQL — plus the cache layer (cache-aside vs write-through, explicit invalidation, stampede protection) and queue/stream choice (Kafka-style log vs RabbitMQ-style broker) with outbox wiring. Hard release gates: reject any design whose partition/shard key isn't justified against the dominant query path, or whose consistency expectations are unnamed. Use when choosing a database, designing a schema/partition strategy, adding a cache, picking a queue, or debugging hot partitions and invalidation. NOT for system topology (use design-system) or API contracts (use api-design)."
---

# Data Store Selection

Databases don't fail because the brand was wrong — they fail because the **access pattern was never written down**. A shard key that fights the dominant query, a cache with no invalidation rule, an unnamed consistency expectation: these decide production behavior long before vendor differences do. This skill works access-pattern-first: patterns → consistency → store family → keys → cache → movement (queues/streams), with two hard gates at the end.

**Output:** a data design — store choice(s) with rationale, schema/partition-key plan justified against the dominant query path, named consistency model per data class, cache policy (per cached object: owner, source of truth, invalidation, TTL, staleness budget), queue/stream choice with delivery semantics, and backfill/migration notes.

## Operating Contract

- Fill the access-pattern and consistency matrices before naming products. A database recommendation without read/write shape, rate, latency, cardinality, and invariants is incomplete.
- For every stateful component, declare the contract: owner, source of truth, schema/key model, consistency guarantee, retention/deletion behavior, failure mode, and recovery path.
- Treat caches and queues as contracts, not add-ons. A cache needs invalidation and staleness rules; a queue needs delivery semantics, idempotency, retry/DLQ ownership, and backlog freshness.
- End with a pass/fail data-layer verdict. Fail designs with unnamed consistency, unjustified partition keys, unowned DLQs, or cache entries with no source-of-truth path.

## When to Use

- Choosing a primary store, adding a second one, or reviewing a schema/shard-key design.
- Adding a cache layer or debugging stale data / stampedes / hot partitions.
- Picking between a log (Kafka-style) and a broker (RabbitMQ-style); wiring events off transactional writes.

## When NOT to Use

- Whole-system shape → [design-system](../design-system/SKILL.md). API surface → [api-design](../api-design/SKILL.md).
- Tuning one slow query — that's diagnosis ([diagnose-loop](../../development/diagnose-loop/SKILL.md)), not selection.

## The selection order

Full tables, key-design rules, and patterns: [references/data-playbook.md](references/data-playbook.md).

1. **Write the access patterns down.** Every dominant read and write: shape, rate, latency budget, cardinality. A design that can't list these isn't ready to pick a store.
2. **Name the consistency model per data class.** Strong/transactional? Read-your-writes? Eventual with conflict resolution? *Unnamed consistency is the gate-rejection that prevents the worst surprises.*
3. **Pick the store family:**

| Dominant requirement | Default | Avoid when | Key warning |
|---|---|---|---|
| Multi-row invariants, joins, transactions | **Relational** (the default) | Primary access is simple key reads at extreme horizontal scale | Every secondary index taxes writes |
| Aggregate-centric flexible documents | Document store | Cross-document joins / strong cross-aggregate consistency are central | Poor shard keys hurt at scale |
| Very high throughput keyed access | Key-value / wide-column | Ad-hoc querying dominates | Hot partitions are the real bottleneck |
| Global SQL, external consistency | Spanner-class | Latency/cost don't justify global consensus | Operational + financial weight |

   Relational first; NoSQL when the pattern is **known, partitionable, and better matched** to its model than to joins. Start normalized; denormalize only for *measured* hot paths.
4. **Design the keys.** The partition/shard key is the scalability decision: high cardinality, even spread, aligned with the dominant query, never monotonic (timestamps/sequences create hot partitions — bucket them). A good shard key matters more than the database brand.
5. **Add the cache only for a named need** (latency target or origin cost the store can't meet): cache-aside default, write-through for warm-on-write, **explicit invalidation rule per object**, TTLs from business freshness, jittered; stampede protection (request coalescing, stale-on-error) on hot keys.
6. **Choose the movement layer when decoupling is needed:** Kafka-style log for ordered partitions, replay, stream processing; RabbitMQ-style broker for work queues, routing, per-message acks. Either way: idempotent consumers, DLQ with an owner, bounded retries, and a **transactional outbox** on the producer so events can't diverge from writes.

## Release gates (hard)

- **Reject** if the partition/shard key cannot be justified against the dominant query path. "It's the default / it's always unique" (e.g. Mongo `_id`/ObjectId) is not a justification — ObjectId is monotonically increasing and hot-spots the latest chunk on write-heavy data. "We can reshard later" is not allowed: the shard key is a load-bearing decision now, and resharding a live ledger is a migration, not a tweak.
- **Reject** if consistency expectations are not explicitly named (per data class, including what readers may see mid-flight). On money/ledger data you MUST name the concrete primitives, not the adjective: read concern / write concern (e.g. `majority` vs `local`), whether stale balance reads are acceptable and for how long. "Mongo gives us consistency" is a non-answer — name read/write concern or it fails.
- **Reject** if a stateful component has no owner, source of truth, retention/deletion rule, or recovery path.
- No queue/topic is production-ready without delivery semantics (at-least-once vs at-most-once, named), replay policy, idempotency contract, DLQ ownership, and a named owner of retries on a failed delivery. "It's just notifications, a dropped email is fine" still requires you to state that at-most-once is the chosen contract — silence is a fail, not a default.
- No cached object without owner, source of truth, invalidation mechanism, TTL, and acceptable staleness. "Invalidation will fall out naturally" / "we'll set a TTL later" is a fail: name *when* the entry is written and *what event busts it* (e.g. a balance write), or do not add the cache.
- **Reject** if the design defers any of the above to "later" / "post-demo" / "before real funds flow." Money is involved on the first commit; the gates apply to the design you ship Monday, not to a future hardening pass. Fake demo data does not lower the durability/consistency bar — the schema and keys you ship are the ones backend builds on.

## Known pressure rationalizations

Each row is a dodge a time-pressured agent will reach for. The skill rejects it at the named gate. If you catch yourself reasoning the left column, you are skipping a gate.

| Rationalization (dodge) | Required response |
|---|---|
| "Team already knows Mongo / it's in prod / one datastore is simpler to operate." | Operational familiarity is not an access pattern. Run the patterns → consistency → family steps; Mongo may win, but only after the matrix justifies it, not because it's incumbent. |
| "Picking what the team runs + the most popular tools (Redis, RabbitMQ) is the safe, defensible choice." | Popularity/incumbency defends nothing if the access pattern isn't written down. The defensible choice is the one justified against the dominant query path. Brand-first is the failure mode, not the safe path. |
| "Shard on `_id`/ObjectId — it's the default and always unique." | ObjectId is monotonic → hot-spots the latest chunk on a write-heavy ledger. Unique ≠ good shard key. Pick a high-cardinality, evenly-spread key aligned to the dominant query. |
| "We can reshard later if we have to." | Resharding a live money ledger is a migration with downtime/risk, not a later tweak. The shard key is decided now, against the write path, or the design fails. |
| "Redis cache-aside, invalidation will fall out naturally / we'll set a TTL later." | Name the write point and the bust event (balance change) now. An unspecified-invalidation cache on balances serves wrong money. No invalidation rule → no cache. |
| "A ledger needs to be consistent — Mongo gives us consistency, done." | Name the primitives: read concern / write concern (`majority`? `local`?) and whether stale balance reads are acceptable. The adjective "consistent" is not a consistency model. |
| "Drop in a queue for notifications — delivery semantics / DLQ / retry owner are 'just notifications', harden post-demo." | State the delivery contract explicitly (at-least-once vs at-most-once), who owns retries on a failed SMS, and the DLQ. Choosing at-most-once is fine; leaving it unnamed is a fail. |
| "PM said don't overthink it / we'll iterate — demanding access patterns makes me a blocker." | The matrices ARE the deliverable, and they take minutes, not a discovery sprint. Naming patterns + consistency before tools is decisiveness, not blocking. Ship the design *with* the gates filled. |
| "It's a Wednesday demo with fake data — correctness/durability can wait, leave a TODO." | Money is involved on the first commit. Fake data doesn't lower the bar; the schema, keys, and consistency you ship are what real funds run on. The gates apply to the Monday design. |

## Generated agents

Copy-ready generated agents live in [../agents/README.md](../agents/README.md) and are sourced from [../agents/manifest.json](../agents/manifest.json). Install only the roles needed for the active data-store selection: `data-access-analyst`, `data-store-designer`, `data-gate-reviewer`.

## Common Mistakes

- **Brand-first selection.** "We're a Mongo shop" is not an access pattern. Patterns → model → product.
- **Monotonic shard keys.** Time-ordered keys funnel every write into one hot partition. Bucket or hash.
- **Caches as database fixes.** A cache hiding an unindexed query becomes load-bearing and then fails loudly. Fix the path, then cache the truly hot reads.
- **Index maximalism.** Each secondary index accelerates a read and taxes every write; add them against measured queries.
- **"Exactly once" faith.** It's a workflow property — broker guarantees + idempotent consumers + dedup — never a checkbox.
- **Events without an outbox.** Publishing after commit (or before) eventually diverges from the data. Outbox or CDC, always.

---

*Deepens the data path [design-system](../design-system/SKILL.md) sketched; event contracts pair with [api-design](../api-design/SKILL.md); the operational metrics land in [production-readiness](../production-readiness/SKILL.md)'s gate.*
