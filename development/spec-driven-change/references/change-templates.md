# Change templates

Copy-paste starting points for a [spec-driven-change](../SKILL.md) change folder.
Grammar and merge rules: [spec-format.md](spec-format.md). Adapt `<placeholders>`.

A change is a folder under `openspec/changes/<change-name>/`. `<change-name>` is a
short kebab-case verb-phrase: `add-2fa`, `rate-limit-search`, `drop-legacy-theme`.

## proposal.md

```md
# <Change Name>

## Why
<the problem / motivation in 2–4 sentences; link the issue or the design if one exists>

## What changes
- <bullet: the observable change, in requirement terms>
- <bullet: …>

## Scope
- **In:** <what this change covers>
- **Out:** <what it deliberately does not — prevents scope creep>
- **Capabilities touched:** <auth, billing, …> (one delta file each)
```

## tasks.md

The implementation checklist. This IS the intake for the executor
(autonomous-advisor / sprint-ticket-runner) — keep tasks small and verifiable.

```md
# Tasks — <Change Name>

- [ ] <task: exact files + concrete change>
- [ ] <task: …>
- [ ] Update the delta spec(s) under specs/<capability>/spec.md
- [ ] Validate: `python scripts/validate-spec.py openspec/changes/<name>/specs`
- [ ] On ship: merge + archive (see SKILL.md close-out)
```

## design.md (optional — include when the "how" is non-trivial)

```md
# Design — <Change Name>

## Approach
<the technical shape; if design-panel produced a chosen design, paste/point to it here>

## Decisions & trade-offs
- <decision>: <why, and what was rejected>

## Risks
- <risk> → <mitigation>
```

## specs/<capability>/spec.md — the DELTA

One file per capability the change touches. Only the four delta headers are legal
(see [spec-format.md](spec-format.md)). Include only the sections you need.

```md
## ADDED Requirements
### Requirement: <New Requirement>
The system MUST <normative statement>.

#### Scenario: <name>
- GIVEN <precondition>
- WHEN <action>
- THEN <observable outcome>

## MODIFIED Requirements
### Requirement: <Existing Requirement>
The system MUST <the full replacement text>.

#### Scenario: <name>
- GIVEN … / WHEN … / THEN …

## REMOVED Requirements
### Requirement: <Existing Requirement>

## RENAMED Requirements
- FROM: `<Old Name>`
- TO: `<New Name>`
```

## openspec/specs/<capability>/spec.md — the LIVING spec

What the change's delta merges INTO on archive. Starts from a change's first
`ADDED` requirements (or from the brownfield onboard path in SKILL.md).

```md
# <Capability>

### Requirement: <Name>
The system MUST <normative statement>.

#### Scenario: <name>
- GIVEN <precondition>
- WHEN <action>
- THEN <observable outcome>
```

## Archive naming

On ship, after the delta merges into the living specs, move the change folder to:

```
openspec/changes/archive/YYYY-MM-DD-<change-name>/
```

Use the ship date. The archived folder is the immutable record of *why* the living
spec looks the way it does; the living spec is the *what*.
