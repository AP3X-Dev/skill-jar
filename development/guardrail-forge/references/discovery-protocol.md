# Discovery protocol

Use this protocol for the Level 1 read-only pass. Its output is a candidate
architecture report, not installed policy.

## Evidence order and limits

Collect each claim with a type, locator, commit, note, and confidence:

1. Current runtime wiring and executable behavior.
2. Current tests, compiler/linter configuration, and build/CI behavior.
3. Current source and dependency edges.
4. Approved ADRs or explicit architecture-owner decisions.
5. Scoped `AGENTS.md`, `CLAUDE.md`, and architecture documentation.
6. Git history, issue/PR discussion, and blame context.
7. Optional MemBerry/FUGAZI/other indexed evidence.

This order is about proving what exists, not who owns architecture. A scoped
instruction may be binding for agent conduct while still conflicting with the
implemented product design. Source prevalence may expose a seam or accumulated
debt. Neither becomes policy without resolving the conflict.

## Survey lanes

Run lanes independently where possible and merge their evidence afterward:

- Toolchain and package/workspace topology.
- Runtime entry points and composition roots.
- Request, command, data, and event flows.
- Persistence models, migrations, tenancy, and transaction boundaries.
- Authentication, authorization, and trust boundaries.
- Public APIs, serialization/on-disk formats, and integration seams.
- Dependency direction, cycles, central registries, and adapter boundaries.
- Existing tests, lint/typecheck/build, hooks, and CI.
- Instructions, ADRs, architecture docs, relevant history, and exceptions.
- Architecture seed, when present: `.architecture-seed/architecture-seed.yaml`
  and `docs/architecture/07-guardrail-candidates.md` (emitted by
  greenfield-architecture / architecture-decision-loop). Import each candidate
  as `documented` or, with a matching ADR decision ID, `approved`; confirm its
  scope against the actual skeleton before it can reach `verified`.

`scripts/inspect-project.py` inventories likely files and commands. Its results
are hints. Read the actual files on each claimed path and verify dynamic,
generated, reflected, aliased, or string-dispatched edges before concluding a
dependency is absent.

## Candidate rule record

For each candidate, capture:

- Proposed stable ID and one-sentence statement.
- Exact include/exclude scope.
- Current state: observed, documented, or verified.
- Supporting and contradicting evidence.
- Known legacy violations and possible exact fingerprints.
- Coverage gaps in the proposed extraction/validator approach.
- Blast radius and likely owners.
- Proposed severity and remediation.
- Decision required before approval.

Do not collapse contradictory evidence into an average. File a decision packet:

```text
BLOCKED-004
Question: May routers access the ORM directly?
Evidence for service-only: <instruction/ADR/source>
Evidence for router access: <source/runtime/tests>
Options: <two or three concrete policies with blast radius>
Recommendation: <smallest reversible choice, clearly marked as recommendation>
Owner needed: <team/role or unknown>
```

## Optional MemBerry adapter

When available, retrieve code symbols, dependency relationships, registered
architecture aspects, impact/blast-radius results, drift, prior decisions,
exceptions, failed approaches, PR impact, and provenance. Verify drift-prone
facts against the current checkout. Store accepted rules and decisions only
after human approval, with manifest path and source commit.

The adapter must never:

- Approve a rule or exception.
- Create or advance a baseline.
- Replace committed state or deterministic validators.
- Turn stale memory into confirmed-current architecture.

If MemBerry is unavailable, record that fact and continue with repository
evidence. The Level 1 deliverable remains complete without it.
