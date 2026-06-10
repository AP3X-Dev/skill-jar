---
name: skill-forge
description: "Loop that hardens an agent skill with pressure-test discipline. RED: run a pressure scenario against a fresh subagent WITHOUT the skill and record the rationalizations it invents; GREEN: draft or patch the SKILL.md to close them; REFACTOR: re-run, hunt new loopholes, repeat until K consecutive clean runs. Lints structure (frontmatter parses, description carries a trigger, links resolve, length) and grows a rationalization corpus in optional MemBerry; Superpowers writing-skills is optional lineage, not a prerequisite. Use when writing a new skill or hardening an existing one against the loopholes agents talk themselves into — especially behavioural/discipline skills. NOT for a one-line skill tweak (just edit it), authoring non-skill docs, or building a code loop (use loop-engineer)."
---

# Skill Forge

Writing a skill that *holds under pressure* is test-driven work: a skill is only as good as the rationalizations it stops an agent from making. This loop automates the pressure-test cycle — generate the pressure, watch a fresh agent fail, close the loophole, repeat — until the skill survives K runs in a row. Maker≠checker is structural: the skill's author never judges whether it holds; a **fresh subagent under pressure** does, because the author already knows the intended behaviour and can't un-know it.

**Output:** a hardened `SKILL.md` — tight description, a rationalization table, a red-flags list, closed loopholes — proven by K consecutive clean pressure runs and a passing structure lint.

## Operating Contract

Do not edit a skill from taste alone. Every rule added or tightened must map to a captured pressure-run failure, a known routing/install defect, or a concrete user requirement. Keep the run package: RED transcript, verbatim rationalizations, patch summary, REFACTOR verdicts, and lint evidence. A skill is not forged until the package shows one failing run first, then K clean runs with the skill loaded.

## When to Use

- Authoring a new skill, especially a **discipline/behavioural** one (an agent must do — or refuse — something under pressure).
- Hardening an existing skill that agents keep wriggling out of.
- Turning a vague "do it this way" doc into a skill with teeth.

## When NOT to Use

- A one-line edit to an existing skill — just make it.
- Reference/how-to docs with no behavioural pressure to test — plain writing, not forging.
- Building a *code* loop (CI, triage, fixes) — use **loop-engineer**.

## The loop (RED → GREEN → REFACTOR)

One skill per run; iterate until it holds.

| Stage | Action | Exit condition |
|---|---|---|
| **RED** | Run a **pressure scenario** against a fresh subagent that does NOT have the skill. Record the exact rationalizations / shortcuts it invents — verbatim, they become the test corpus. | At least one realistic failure captured (if the agent never fails, the scenario isn't pressured enough). |
| **GREEN** | Write or patch the `SKILL.md` to close *those specific* rationalizations — name them in a rationalization table, add red flags, tighten the rule. | The skill addresses every captured rationalization by name. |
| **REFACTOR** | Re-run the scenario(s) against a fresh subagent that NOW has the skill. Did it comply? Find any *new* loophole it invented and return to GREEN. | **K consecutive clean runs** (default K=3) across the scenario set with zero new loopholes. |
| **LINT** | Run the structure gate (below). | Frontmatter parses; description ≤1024 chars with a `use when` trigger; `name` matches the directory; every relative link resolves. |

**Iron law:** no skill ships without a failing pressure run first. A skill written from imagination closes the loopholes you guessed, not the ones agents actually take.

## Roles (maker ≠ checker)

| Role | Job | Never |
|---|---|---|
| **Pressure-tester** (fresh subagent) | Attempt the scenario; rationalize freely; surface the shortcuts a real agent would take | See the skill during a RED run |
| **Forger** (maker) | Write/patch the SKILL.md to close the captured rationalizations | Judge its own skill by re-reading it |
| **Judge** (checker) | Run the scenario *with* the skill against a fresh agent, decide comply / loophole-found with evidence | Be lenient because the skill "reads well" |
| **Linter** (gate) | Structure check — a runnable pass, not an opinion | Pass a skill whose links break or whose description lacks a trigger |

Templates for all three prompts: [references/forge-kit.md](references/forge-kit.md).

## Structure lint gate

A skill that holds behaviourally still fails if it can't be installed or routed. The lint is runnable, not a vibe — a real pass/fail per item, not an opinion:

- Frontmatter parses as YAML with `name` + non-empty `description`.
- `description` ≤ 1024 chars, written third-person, and contains a trigger (`use when` / `use during`) so an agent can route to it.
- `name` matches the skill's directory name.
- Every relative Markdown link resolves to a real file (bundle references one level deep).
- Progressive disclosure: SKILL.md stays lean; heavy templates/catalogs live in `references/`.

Where the host repo ships a skill-audit script (a jar-style `audit-jar.py`, say), the LINT step just calls it; otherwise run these as a short script or by hand. The full checklist is in [references/forge-kit.md](references/forge-kit.md).

## Optional: MemBerry rationalization corpus

If a MemBerry-style memory MCP is available, the loophole knowledge compounds across skills. `berry_load` at RED to seed the pressure scenario with rationalizations that defeated *other* skills (agents reuse the same dodges — "it's just a simple case", "I'll add the test after"), and `berry_store` each newly-closed loophole. Over time the corpus makes RED start from a stronger attack. Skip entirely if absent — the per-skill loop works without it.

## Optional: FUGAZI for script-bearing skills

If the skill ships utility scripts and [FUGAZI](https://github.com/AP3X-Dev/FUGAZI) is available, run `fugazi dead-code` / `health` on the `scripts/` directory as part of LINT — a skill shouldn't ship dead or tangled helper code. Read-only; skip if the skill is docs-only or FUGAZI isn't installed.

## Generated agents

Copy-ready generated agents live in [../agents/README.md](../agents/README.md) and are sourced from [../agents/manifest.json](../agents/manifest.json). Install only the roles needed for the active skill-forge loop: `skill-forge-pressure-tester`, `skill-forge-forger`, `skill-forge-judge`, `skill-forge-linter`.

## Common Mistakes

- **Writing the skill first, testing never.** You'll close imagined loopholes and miss the real ones. RED before GREEN, always.
- **Testing with the author.** The author knows the intent and "complies" automatically. Pressure-test a *fresh* agent that's never seen the skill.
- **One clean run = done.** Agents are creative; loopholes appear on run 2 or 3. Require K consecutive clean runs.
- **A description that summarizes the workflow.** The description is for *routing*, not explaining — it needs the triggers an agent matches on, or the skill never loads. The lint checks for a trigger; make it a good one.
- **Skipping the lint because it "reads fine".** A broken relative link or a missing trigger ships a skill that can't be used. The gate is runnable for a reason.

---

*Automates pressure-test → close loopholes → repeat for any agent that loads `SKILL.md` files — a personal skill folder, a plugin, or a published collection. Superpowers writing-skills and TDD skills are optional lineage; the forge runs from this file plus [references/forge-kit.md](references/forge-kit.md). Where a repo already ships a skill-audit script, the LINT step simply calls it.*
