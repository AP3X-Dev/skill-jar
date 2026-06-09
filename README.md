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
| [**loop-engineering**](loop-engineering/SKILL.md) | Scaffolds a self-running **agent loop** into a repo — automation discovers work, a maker agent executes, a *separate* checker verifies, state is recorded, and the loop decides what runs next. Lays down state files, maker≠checker subagents (Claude Code **and** Codex), trigger + per-cycle driver prompts, runnable verification gates, `AGENTS.md` safety rules, worktree isolation, and install-ready triage / code-review / release role-skills. Agent-agnostic; starts at triage-only and earns autonomy one level at a time. |
| [**building-optimization-loops**](building-optimization-loops/SKILL.md) | A specialized loop (one that `loop-engineering` can scaffold as its execution stage): generates a self-sustaining optimization-loop prompt for an existing codebase. Audits first, builds a concrete file-level backlog, then drives repeated **audit → fix → measure → track** cycles — with a re-measured metric vector, a no-regression ratchet, a restartable progress log, and guardrails for unattended runs. Built for hardening / quality passes after feature work. |

*Two skills and counting — the jar fills up over time.*

## Self-hosted loops

The jar takes its own medicine: [loop-engineering](loop-engineering/SKILL.md) scaffolded two loops into this very repo (shared state spine in `agent-state/`, role agents in `.claude/agents/`, drivers in `docs/prompts/`):

- **jar-audit** — keeps the jar publish-ready. Discovery is a deterministic gate, `python scripts/audit-jar.py`: frontmatter parses, descriptions carry triggers, names match directories, every relative link resolves, scripts compile, the scaffolder stays idempotent. Red check → one fix per cycle, verified by a separate agent.
- **bug-pipeline** — Hunter → Fixer → Validator over `agent-state/BUG_TRACKER.md`. The hunter files evidence-backed defects, the fixer repairs one per cycle, and an independent validator (different model) promotes to `verified` or reopens.

Run a cycle by handing your agent the matching driver in `docs/prompts/`. Both loops run at autonomy Level 2: they commit locally; a human reviews and pushes.
