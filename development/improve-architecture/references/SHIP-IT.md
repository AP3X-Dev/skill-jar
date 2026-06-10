# Shipping a deepening

How to take an approved deepening from a design the human signed off in the grilling loop (SKILL.md step 3) all the way to merged, without regressing behaviour. Assumes the vocabulary in [LANGUAGE.md](LANGUAGE.md) — **module**, **interface**, **seam**, **adapter**, **leverage**, **locality** — and the dependency/testing strategy in [DEEPENING.md](DEEPENING.md).

**Precondition.** The grilling loop has converged on a module shape the human approved. Do not start moving code before that sign-off.

## Deepening package

Before code moves, create or update the issue/doc with this concrete package:

```md
# Deepening Package: <module name>

## Approved Interface
- **Entry points:** <methods/functions/events>
- **Caller invariants:** <what callers must know>
- **Error modes:** <observable failures and handling>
- **Ordering/config:** <anything order- or config-sensitive>

## Hidden Implementation
<behaviour, duplicated rules, adapters, or data movement that becomes internal>

## Migration Steps
1. <small reversible step>
2. <small reversible step>

## Acceptance Gate
- **Characterization:** <test/command proving current behaviour>
- **Final gate:** <test/build/typecheck/manual check with expected result>

## Rollback Point
<last safe commit/step before deleting the old shallow surface>
```

## 1. Re-run the depth check

Before writing any code, confirm the change actually deepens. All of these should be "yes":

- Does the **interface** get simpler — fewer things a caller must know?
- Does the module hide more **implementation** behind that interface?
- Does the caller need to know less than before?
- Does related behaviour move into **one place** (locality up)?
- Does it remove duplication / collapse parallel implementations into one source of truth?
- Does it improve **leverage** — one interface paying back across N call sites and M tests?
- Is the result easier to test through its interface?

If the honest answer is "no" — the interface isn't shrinking, behaviour isn't concentrating — the change is only rearranging files between modules. Stop and rework the shape; don't ship a rename as a deepening.

## 2. Turn the design into an issue

Record the approved design as a tracked unit of work before migrating. Keep the vocabulary consistent with the glossary and the project's `CONTEXT.md` domain terms.

```md
# Deepen: <module name, in CONTEXT.md vocabulary>

## Problem
<the current architecture friction — shallow interface, duplicated logic,
leak across a seam, low locality. Name files.>

## Current shape
<where the behaviour lives now and why it's hard to change: the implicit
interface, the places behaviour can drift, the call sites affected.>

## Approved shape
- **Responsibility:** <the one thing this module owns>
- **Interface:** <entry points + invariants, ordering, error modes — what a
  caller must know>
- **Hidden behind the seam:** <what becomes implementation detail>
- **Dependency category:** <in-process | local-substitutable | ports & adapters
  | mock> (see DEEPENING.md)
- **Adapters:** <production + test adapters, if the category needs a seam>

## Migration plan
<the ordered steps from section 3, as a checklist>

## Acceptance criteria
<the deep-module checklist from section 4>

## Risks
<behavioural, compatibility, or migration risks; any ADR this touches>
```

If a `to-issues` / `triage` skill or the `gh` CLI is available, file the issue through it; otherwise save the markdown in the repo (e.g. `docs/refactors/`) or hand it to the user. The template is the deliverable either way — don't block on a tracker that isn't there.

## 3. Migrate in small, reversible steps

Each step is a safe commit point with the suite green. Order matters: prove behaviour first, swap the shape second, delete the old surface last.

1. **Characterize.** Add tests around the *current* behaviour at the affected call sites, so the migration has a behaviour-preserving baseline to check against.
2. **Create the new module** with the approved interface — empty or delegating at first.
3. **Move the core behaviour behind the seam.** Add adapters per the dependency category (in-memory for tests, real for production — [DEEPENING.md](DEEPENING.md)). One adapter is just indirection; introduce a seam only when production + test actually vary across it.
4. **Update call sites one at a time**, keeping the suite green between each. A broken intermediate state means the step was too big.
5. **Delete the shallow wrappers and their now-redundant unit tests — replace, don't layer.** Old tests on the shallow modules become waste once the deepened interface is tested ([DEEPENING.md](DEEPENING.md)). Leaving them is how a "deepening" silently adds surface instead of removing it.
6. **Write tests at the new interface.** The interface is the test surface; assert on observable outcomes through it, not on internal state, so the tests survive future internal refactors.
7. **Document the module's interface** — the invariants and ordering a caller must respect, not a restatement of the implementation.

If a `tdd` or plan-execution skill is available, run the migration through it; the steps above are the same either way.

## 4. Verify — the deep-module checklist

The acceptance gate. Ship only when every box is honestly checked:

```md
- [ ] The module has one clear responsibility.
- [ ] The interface is smaller than the implementation it hides.
- [ ] Callers do not need to understand internal details.
- [ ] Related behaviour lives in one place (locality up).
- [ ] Duplicated / parallel implementations have been removed.
- [ ] The seam is explicit; test adapters or mocks are easy to use.
- [ ] Tests sit at the interface and assert observable outcomes.
- [ ] Existing behaviour is preserved (characterization tests still pass).
- [ ] The change improves leverage and locality, not just file layout.
- [ ] Future changes in this area should touch fewer files.
```

A "no" on the interface-smaller, duplication-removed, or behaviour-preserved lines means the deepening isn't done — not that the checklist is wrong.
