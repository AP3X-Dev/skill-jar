# Spec format — the grammar contract

The machine-checkable requirement/scenario grammar and the delta model for
[spec-driven-change](../SKILL.md). This file is the source of truth: the bundled
`scripts/validate-spec.py` and `scripts/archive-merge.py` enforce exactly what is
written here, and an agent with no Python runtime applies the same rules by hand.
Self-contained — no `openspec` CLI, no external tool.

## The tree (lives in the target repo)

```
openspec/
├── specs/                      # the LIVING requirements — always current
│   └── <capability>/spec.md    # one file per capability (auth, billing, search…)
├── changes/                    # in-flight changes
│   └── <change-name>/
│       ├── proposal.md         # why + what + scope
│       ├── design.md           # (optional) technical approach / trade-offs
│       ├── tasks.md            # implementation checklist == the executor's intake
│       └── specs/
│           └── <capability>/spec.md   # the DELTA against openspec/specs/<capability>
└── changes/archive/
    └── YYYY-MM-DD-<change-name>/       # shipped changes, moved here after merge
```

`openspec/` is a free namespace — it does not collide with a repo's own `specs/`,
`docs/`, or the jar's `agent-state/`.

## Requirement grammar (living specs)

A living spec (`openspec/specs/<capability>/spec.md`) is an optional `# Title`
followed by requirements. Each requirement:

```md
### Requirement: <Name>
The system MUST <normative statement>.

#### Scenario: <short name>
- GIVEN <precondition>
- WHEN <action>
- THEN <observable outcome>
```

Hard rules (errors — `validate-spec.py` exits 1):

- **Requirement header is exactly 3 hashes**: `### Requirement: <Name>`.
- **Scenario header is exactly 4 hashes**: `#### Scenario: <name>`. Three hashes,
  five hashes, or a `- Scenario:` bullet **fail silently** in every spec tool —
  they read as prose. This is the single most common broken spec; it is a hard error.
- **Every requirement has ≥ 1 scenario.** A requirement with no scenario is
  unverifiable intent.

Soft rules (warnings — do not fail the gate, but fix them):

- A requirement with no normative keyword (`MUST` / `SHALL` / `SHOULD` / `MAY`)
  is a wish, not a requirement. Use RFC-2119 language.
- A scenario should carry `GIVEN` / `WHEN` / `THEN` lines.

## Delta grammar (a change's spec)

A change never edits the living spec directly. It ships a **delta** per capability
at `openspec/changes/<name>/specs/<capability>/spec.md`, using these four section
headers (each `## <Op> Requirements`) and nothing else:

```md
## ADDED Requirements
### Requirement: <New Name>
The system MUST <…>.
#### Scenario: <…>
- GIVEN … / WHEN … / THEN …

## MODIFIED Requirements
### Requirement: <Existing Name>
The system MUST <the FULL new text — a modified requirement is replaced whole>.
#### Scenario: <…>
- GIVEN … / WHEN … / THEN …

## REMOVED Requirements
### Requirement: <Existing Name>
<!-- header only; no body needed -->

## RENAMED Requirements
- FROM: `<Existing Name>`
- TO: `<New Name>`
```

Rules:

- **Only those four `## … Requirements` headers are legal in a delta.** Any other
  (`## APPENDED …`, a typo) is a hard error — it silently drops the section.
- **ADDED / MODIFIED** contain full requirement blocks (with scenarios; the same
  hard rules apply).
- **REMOVED** lists requirement headers only.
- **RENAMED** is `FROM:` / `TO:` pairs (backticks optional).

## The merge (archive step) — order is not negotiable

On archive, each capability's delta folds into the living spec in this exact order:

**RENAMED → REMOVED → MODIFIED → ADDED**

Why the order matters: renames resolve first so a later `MODIFIED`/`REMOVED`
targets the new name; removes happen before adds so a remove-then-add of the same
name is a replace, not a conflict. Applying these out of order silently produces a
wrong spec — which is why `archive-merge.py` exists.

Conflict rules (hard errors — the merge aborts, it never guesses):

- `MODIFIED` / `REMOVED` / `RENAMED FROM` a requirement that isn't in the living
  spec → **error** (you're editing something that doesn't exist).
- `ADDED` a requirement that already exists → **error** (use `MODIFIED`).

### By hand (no Python)

For each `<capability>` delta: open `openspec/specs/<capability>/spec.md`, then
apply the delta's sections in the order above — rename the named requirements,
delete the removed ones, replace the modified ones whole, append the added ones.
Re-run the requirement grammar rules on the result. This is exactly what the
script automates; the script is an optional accelerator, not a dependency.

## Running the bundled scripts (optional)

```bash
# validate a change's delta, or the whole living-spec tree
python scripts/validate-spec.py openspec/changes/<name>/specs
python scripts/validate-spec.py openspec/specs

# preview the merge (dry-run), then apply it into the living specs
python scripts/archive-merge.py --change openspec/changes/<name> --specs openspec/specs
python scripts/archive-merge.py --change openspec/changes/<name> --specs openspec/specs --apply

# both scripts self-check with no repo:
python scripts/validate-spec.py --selftest
python scripts/archive-merge.py --selftest
```

Absence of Python is a clean skip: fall back to the by-hand procedures above.
