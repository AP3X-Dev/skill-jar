# Forge kit

Bundled prompt templates, the structure-lint checklist, and the optional MemBerry corpus schema for [skill-forge](../SKILL.md). Self-contained — adapt `<placeholders>`.

## Forge run package template

Store this beside the skill under review or in the repo's agent-run docs. The package is the evidence that the skill changed because pressure exposed a loophole.

```md
# Forge Run: <skill-name>

## Scenario Set
| ID | Pressure | Shortcut tempted |
|----|----------|------------------|

## RED Evidence
| Scenario | Fresh-agent result | Verbatim rationalization |
|----------|--------------------|--------------------------|

## GREEN Patch
- **Skill files changed:** <paths>
- **Loopholes closed:** <named rationalizations>
- **Rules added/tightened:** <sections>

## REFACTOR Verdicts
| Run | Scenario | Verdict | Evidence |
|-----|----------|---------|----------|

## Lint Evidence
- **Command/check:** <command or checklist>
- **Result:** <exit/result>
```

## Pressure-test (RED — fresh subagent, no skill)

The scenario must create *real* pressure to take the shortcut the skill exists to prevent. A weak scenario the agent passes by accident teaches nothing.

```md
You are <role>. <Concrete task that tempts the shortcut>. There is time
pressure / the easy path is right there / the test is annoying to write.

<Give it the situation, NOT the skill.> Do the task. Think out loud about
trade-offs as you go.
```

Run it 2–3 times (agents vary). Capture **verbatim** every rationalization it uses to justify the shortcut — these are your test cases:

> "This is just a simple case, so I'll skip the full check."
> "I'll write the test right after, once I see it works."
> "The existing pattern is overkill here."

## Judge (REFACTOR — fresh subagent, WITH the skill)

```md
You are <role>. You have access to the <skill-name> skill. <Same scenario as RED>.

Do the task.
```

Then evaluate the transcript:

```md
Decide whether the agent COMPLIED with <skill-name> or found a LOOPHOLE.
- Compliant: it followed the discipline even under the pressure.
- Loophole: it obeyed the letter while dodging the intent — quote the exact
  rationalization and how the current skill text let it through.
Return: COMPLY, or LOOPHOLE + the verbatim dodge + which skill section failed.
A new loophole sends the forger back to GREEN. K consecutive COMPLY runs
(default K=3, fresh agent each time) across the scenario set = done.
```

## GREEN patterns (closing loopholes)

When you patch the SKILL.md, close the *named* rationalizations, not the general topic:

- **Rationalization table** — two columns, the dodge and the reality:
  | Thought | Reality |
  |---|---|
  | "Just a simple case" | Simple cases become complex. The rule holds. |
- **Red flags list** — the phrases that mean "stop, you're rationalizing".
- **Tighten the rule** — make the required/forbidden action unambiguous; an "iron law" line for discipline skills.
- **CSO (description)** — ensure the trigger phrases an agent would match on are present, so the skill actually loads when relevant.

## Structure-lint checklist

Runnable checks — each a real pass/fail (if the repo ships a skill-audit script, it runs all of these at once):

- [ ] Frontmatter parses as YAML; has `name` and non-empty `description`.
- [ ] `description` ≤ 1024 chars, third person, contains `use when` / `use during`.
- [ ] `name` == directory name.
- [ ] Every relative Markdown link resolves to a real file inside the skill/repo.
- [ ] SKILL.md is lean; heavy content split into `references/` (one level deep).
- [ ] No time-sensitive info; consistent terminology; concrete examples present.
- [ ] (If it ships scripts) every script compiles; no dead/tangled helper code.

## MemBerry rationalization corpus (optional)

```
berry_store(
  session_id: "<session>",
  task: "[project:<tag>] skill-forge: loophole closed in <skill-name>",
  content: "RATIONALIZATION: <verbatim dodge> | CONTEXT: <what task/pressure
            surfaced it> | CLOSED BY: <the rule/red-flag added>",
  outcome: "approved"
)
```

Load at RED: `berry_load(task: "skill pressure scenarios: <domain>", tags: ["project:<tag>"])` — seed the new scenario with dodges that beat other skills, so RED starts from a harder attack. The corpus is an accelerator; the per-skill RED→GREEN→REFACTOR loop is what actually proves the skill.
