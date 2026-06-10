---
name: data-store-selection
description: "Choose and shape the data layer from access patterns, not brand loyalty: write the dominant read/write patterns first, name the required consistency model, then pick relational (joins, transactions, multi-row invariants — the default), document, key-value/wide-column (keyed access at scale), or Spanner-class global SQL — plus the cache layer (cache-aside vs write-through, explicit invalidation, stampede protection) and queue/stream choice (Kafka-style log vs RabbitMQ-style broker) with outbox wiring. Hard release gates: reject any design whose partition/shard key isn't justified against the dominant query path, or whose consistency expectations are unnamed. Use when choosing a database, designing a schema/partition strategy, adding a cache, picking a queue, or debugging hot partitions and invalidation. NOT for system topology (use design-system) or API contracts (use api-design)."
---

# Data Store Selection

Databases don't fail because the brand was wrong — they fail because the **access pattern was never written down**. A shard key that fights the dominant query, a cache with no invalidation rule, an unnamed consistency expectation: these decide production behavior long before vendor differences do. This skill works access-pattern-first: patterns → consistency → store family → keys → cache → movement (queues/streams), with two hard gates at the end.

**Output:** a data design — store choice(s) with rationale, schema/partition-key plan justified against the dominant query path, named consistency model per data class, cache policy (per cached object: owner, source of truth, invalidation, TTL, staleness budget), queue/stream choice with delivery semantics, and backfill/migration notes.

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

- **Reject** if the partition/shard key cannot be justified against the dominant query path.
- **Reject** if consistency expectations are not explicitly named (per data class, including what readers may see mid-flight).
- No queue/topic is production-ready without delivery semantics, replay policy, idempotency contract, and DLQ ownership.
- No cached object without owner, source of truth, invalidation mechanism, TTL, and acceptable staleness.

## Common Mistakes

- **Brand-first selection.** "We're a Mongo shop" is not an access pattern. Patterns → model → product.
- **Monotonic shard keys.** Time-ordered keys funnel every write into one hot partition. Bucket or hash.
- **Caches as database fixes.** A cache hiding an unindexed query becomes load-bearing and then fails loudly. Fix the path, then cache the truly hot reads.
- **Index maximalism.** Each secondary index accelerates a read and taxes every write; add them against measured queries.
- **"Exactly once" faith.** It's a workflow property — broker guarantees + idempotent consumers + dedup — never a checkbox.
- **Events without an outbox.** Publishing after commit (or before) eventually diverges from the data. Outbox or CDC, always.

---

*Deepens the data path [design-system](../design-system/SKILL.md) sketched; event contracts pair with [api-design](../api-design/SKILL.md); the operational metrics land in [production-readiness](../production-readiness/SKILL.md)'s gate.*
