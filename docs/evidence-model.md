# Evidence Model

Skill Jar stays category-installed. Categories such as `development` and
`systems-design` are the install surface. Metadata describes what a skill does;
it does not create a second install system.

## Metadata Fields

`tags` are for routing, filtering, and discovery. They describe behavior such
as `meta`, `repair-loop`, `validation`, or `pressure-test`. Tags are not install
groups.

`core: true` marks a skill as part of the jar's self-improvement substrate: it
helps maintain, test, evaluate, improve, or operate the jar. Core skills still
live in their normal category and install through that category.

`maturity` records the current confidence level:

| Level | Meaning |
|---|---|
| `draft` | The skill exists but has not been meaningfully tested. |
| `linted` | The skill passes structure/audit checks. |
| `dry-run` | The skill has been manually walked through or tested on a fixture. |
| `dogfooded` | The skill has been used on Skill Jar itself. |
| `external-tested` | The skill has been used on at least one external repo/project. |
| `battle-tested` | The skill has repeated evidence across multiple real uses. |

`evidence` links to a proof packet or proof index when one is available. The
path is relative to the repository root and must exist. Evidence should contain
real run artifacts, not marketing claims.

See [../proof/README.md](../proof/README.md) for the proof packet shape.

## Fork Model

Do not delete the core self-improvement substrate unless you intentionally want
a static skill pack.

For most forks, keep the core/meta skills and add your own domain skills. The
core skills act like the jar's maintenance system: they help create, test,
review, audit, and improve the skills over time.

## What This Is Not

This model is intentionally small. It does not add a complex type hierarchy,
runtime ontology, or new plugin category. The jar is the container, skills are
the payload, core/meta skills are the self-improvement substrate, evidence
packets are the proof layer, and categories remain the install surface.
