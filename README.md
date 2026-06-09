<p align="center">
  <img src="assets/skill-jar-banner.png" alt="skill-jar — collect skills, unlock potential" width="100%">
</p>

# skill-jar

A growing collection of **Agent Skills** — drop-in capabilities that teach an AI agent how to do a specific job well. Reach into the jar when you need one.

## What's an Agent Skill?

Each skill is a self-contained `SKILL.md` (plus any bundled resources) with frontmatter describing **when** to use it and instructions for **how**. Skills load on demand — the agent only reads one when the task actually matches, so the jar can grow without bloating context. The format is portable across any agent that supports skills.

## Using a skill

Copy the skill's folder into your agent's skills directory — for example, in Claude Code:

```
~/.claude/skills/<skill-name>/
```

Then invoke it by name (`/<skill-name>`) or just describe your task — a capable agent picks the matching skill automatically.

## Skills in the jar

| Skill | What it does |
|-------|--------------|
| [**building-optimization-loops**](building-optimization-loops/SKILL.md) | Generates a self-sustaining optimization-loop prompt for an existing codebase. Audits first, builds a concrete file-level backlog, then drives repeated **audit → fix → measure → track** cycles — with a re-measured metric vector, a no-regression ratchet, a restartable progress log, and guardrails for unattended runs. Built for hardening / quality passes after feature work. |

*One skill today — the jar only fills up over time.*
