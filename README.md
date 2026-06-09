<p align="center">
  <img src="assets/skill-jar-banner.png" alt="skill-jar — collect skills, unlock potential" width="100%">
</p>

# skill-jar

[![audit](https://github.com/AP3X-Dev/skill-jar/actions/workflows/audit.yml/badge.svg)](https://github.com/AP3X-Dev/skill-jar/actions/workflows/audit.yml)

A growing collection of **Agent Skills** — drop-in capabilities that teach an AI agent how to do a specific job well. Reach into the jar when you need one.

## What's an Agent Skill?

Each skill is a self-contained `SKILL.md` (plus any bundled resources) with frontmatter describing **when** to use it and instructions for **how**. Skills load on demand — the agent only reads one when the task actually matches, so the jar can grow without bloating context. The format is portable across any agent that supports skills.

## Using a skill

Skills are grouped into **categories**, and each category installs as its own Claude Code plugin — so you can grab a whole category, or the entire jar.

**Claude Code — install a category, or everything:**

```
/plugin marketplace add AP3X-Dev/skill-jar
/plugin install skill-jar-development@skill-jar   # just the development category
/plugin install skill-jar@skill-jar                # the whole jar (all categories)
```

Skills then load on demand (`/skill-jar-development:bug-pipeline`, etc.) and update with the repo.

**Any agent — copy the folder** into its skills directory, e.g. in Claude Code:

```
~/.claude/skills/<skill-name>/      # from <category>/<skill-name>/ in this repo
```

Then invoke it by name (`/<skill-name>`) or just describe your task — a capable agent picks the matching skill automatically.

## Skills in the jar

### development

| Skill | What it does |
|-------|--------------|
| [**loop-engineer**](development/loop-engineer/SKILL.md) | Scaffolds a self-running **agent loop** into a repo — automation discovers work, a maker agent executes, a *separate* checker verifies, state is recorded, and the loop decides what runs next. Lays down state files, maker≠checker subagents (Claude Code **and** Codex), trigger + per-cycle driver prompts, runnable verification gates, `AGENTS.md` safety rules, worktree isolation, and install-ready triage / code-review / release role-skills. Agent-agnostic; starts at triage-only and earns autonomy one level at a time. |
| [**bug-pipeline**](development/bug-pipeline/SKILL.md) | A specialized loop for any codebase: a three-agent **Hunter → Fixer → Validator** repair pipeline over a shared `BUG_TRACKER.md`. The hunter files evidence-backed defects (`file:line` + repro, no style nits), the fixer repairs one bug per cycle with the smallest diff that passes the repo gate, and an independent validator — ideally a different model — promotes to `verified` or reopens. Ships the tracker schema, all three agent templates, and the per-cycle driver outline. |
| [**optimization-loop**](development/optimization-loop/SKILL.md) | A specialized loop built on `loop-engineer`: audits an existing codebase first (intent discovery → parallel audit → gap analysis), builds a concrete file-level backlog with a measured metric baseline, scaffolds the loop (agent-state spine, dual-mode driver, maker≠checker verifier, no-regression ratchet) — then **wires the trigger and closes cycle 1 before handing off**, so you get a running **audit → fix → measure → track** loop, not a prompt on a shelf. Terminates on CONVERGED / STALLED / DIVERGING over its own metrics. Built for hardening / quality passes after feature work. |
| [**autonomous-advisor**](development/autonomous-advisor/SKILL.md) | Full hands-off execution: hand it a PRP and it runs the entire pipeline — design → plan → implement → finish → optimize — with zero human input. An **advisor** sub-agent stands in for the human at direction decisions; a separate **verifier** sub-agent gates every work product with evidence and can reject (maker≠checker). Crash-safe via a run-state file with phase-gate evidence and a failed-attempts log; hard guardrails (no prod deploys, no main pushes, no scope creep). |
| [**clean-room**](development/clean-room/SKILL.md) | Reimplement, port, or clone an existing codebase via a firewalled **clean-room rewrite**: multi-pass analysis (AST inventory + 10 analytical passes) produces an exhaustive design doc, an improvements triage, and a PRP — then hands off to `autonomous-advisor` for implementation. Three modes (full clean-room, Parity, Transparent), a mode-locked run-state file so a resumed session can never accidentally breach the firewall, runnable phase gates, and a contamination-scan merge gate. Ships the AST extractor / differ / coverage / contamination scripts. |

*Five skills, one category, and counting — the jar fills up over time. New categories (e.g. `marketing/`) become their own installable plugin automatically.*

## For agents

Reading this repo programmatically? Route from [`skills.json`](skills.json) — a generated index of every skill's `name`, routing `description`, and `path` (one fetch, no directory crawl; it's gate-checked against the frontmatter, so it can't drift). Install via the plugin marketplace above (Claude Code) or copy a skill's folder (any host). Every push is verified by `python scripts/audit-jar.py` — the badge above is that gate. If you *operate* in this repo (run a loop cycle, fix a bug), the rules in [`AGENTS.md`](AGENTS.md) bind you.

## Self-hosted loop

The jar takes its own medicine. [loop-engineer](development/loop-engineer/SKILL.md) scaffolded a loop system into this very repo (state spine in `agent-state/`, role agents in `.claude/agents/`, drivers in `docs/prompts/`):

- **jar-audit** — keeps the jar publish-ready. Discovery is a deterministic gate, `python scripts/audit-jar.py`: frontmatter parses, descriptions carry triggers, names match directories, every relative link resolves, scripts compile, the scaffolder stays idempotent. Red check → one fix per cycle, verified by a separate agent.
- The repo also dogfoods the [**bug-pipeline**](development/bug-pipeline/SKILL.md) skill on itself — its instance lives in `.claude/agents/` + `docs/prompts/bug-pipeline-driver.md`, tracking to `agent-state/BUG_TRACKER.md`.

Run a cycle by handing your agent the matching driver in `docs/prompts/`. Both loops run at autonomy Level 2: they commit locally; a human reviews and pushes.
