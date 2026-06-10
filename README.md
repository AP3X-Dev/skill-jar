<p align="center">
  <img src="assets/skill-jar-banner.png" alt="skill-jar — collect skills, unlock potential" width="100%">
</p>

# skill-jar

[![audit](https://github.com/AP3X-Dev/skill-jar/actions/workflows/audit.yml/badge.svg)](https://github.com/AP3X-Dev/skill-jar/actions/workflows/audit.yml)

A growing collection of **Agent Skills** — drop-in capabilities that teach an AI agent how to do a specific job well. Reach into the jar when you need one.

## What's an Agent Skill?

Each skill is a self-contained `SKILL.md` (plus any bundled resources) with frontmatter describing **when** to use it and instructions for **how**. Skills load on demand — the agent only reads one when the task actually matches, so the jar can grow without bloating context. The format is portable across any agent that supports skills.

## Using a skill

Skills are grouped into **categories**, and each category installs as its own Claude Code plugin — so you pull in just the categories you want.

**Claude Code — install the categories you want:**

```
/plugin marketplace add AP3X-Dev/skill-jar
/plugin install skill-jar-development@skill-jar    # the development category
# /plugin install skill-jar-marketing@skill-jar    # (coming soon)
```

Skills then load on demand (`/skill-jar-development:bug-pipeline`, etc.) and update with the repo. There's no all-in-one bundle plugin — install each category you want; it keeps your plugin list clean and avoids copying the whole repo into your cache.

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
| [**dead-code-reaper**](development/dead-code-reaper/SKILL.md) | A **FUGAZI-native** specialized loop that *safely removes* confirmed-dead code: a Scout runs FUGAZI's dead-code family and proves zero reachability with `trace`, a Reaper deletes one cluster per cycle with the smallest diff, and an independent Validator re-runs FUGAZI + the suite/build against a finding-count/LOC ratchet. Public API and dynamic/reflective usage are blocked for a human call; it never runs `fugazi fix` unattended. Builds and dry-runs the loop, then **offers** launch. |
| [**diagnose-loop**](development/diagnose-loop/SKILL.md) | A **bounded diagnosis loop** for one hard bug or perf regression — builds on superpowers *systematic-debugging* with **parallel hypotheses** (each made to refute itself), optional **FUGAZI** suspect seeding and **MemBerry** root-cause memory, a locked regression test, and a separate verifier (the fixer never certifies its own root cause). Reproduce → minimize → seed suspects → fan out → converge → lock & fix; escalates to a human after three failed fix rounds. |
| [**review-panel**](development/review-panel/SKILL.md) | **Adversarial multi-lens code review** built on superpowers *requesting/receiving-code-review*: an optional **FUGAZI** pre-pass grounds the panel, then independent reviewers each work a distinct lens (correctness, security, simplicity/reuse) in parallel, findings are deduped and severity-ranked, and every finding is **verified against the codebase before it's acted on** — no performative agreement. Optional **MemBerry** false-positive memory de-noises future panels. Ships the lens templates and the verify-before-act protocol. |
| [**optimization-loop**](development/optimization-loop/SKILL.md) | A specialized loop built on `loop-engineer`: audits an existing codebase first (intent discovery → parallel audit → gap analysis), builds a concrete file-level backlog with a measured metric baseline, scaffolds the loop (agent-state spine, dual-mode driver, maker≠checker verifier, no-regression ratchet) — then **wires the trigger and closes cycle 1 before handing off**, so you get a running **audit → fix → measure → track** loop, not a prompt on a shelf. Terminates on CONVERGED / STALLED / DIVERGING over its own metrics. Built for hardening / quality passes after feature work. |
| [**auto-research**](development/auto-research/SKILL.md) | A specialized loop generalizing **Karpathy's autoresearch** pattern to any domain with a runnable metric: the agent runs **fixed-budget experiments** against a frozen eval harness — hypothesize → mutate one file → run → keep/discard by ONE scalar metric → log to `results.tsv` → repeat until interrupted. Builds the harness if the repo lacks one (metric, budget, frozen paths, mutable surface), scaffolds the loop, runs the real baseline, then **offers** launch — the human owns the spend. |
| [**test-backfill-loop**](development/test-backfill-loop/SKILL.md) | A `loop-engineer` loop that **raises coverage one module per cycle**: a Scout finds high-value uncovered code (optional **FUGAZI** `cold-code`/`hot-path`), a maker writes **characterization tests** that pin current behaviour, and a separate verifier confirms each test actually **bites** (goes red when behaviour is perturbed) and that coverage ratchets up — never down. Suspected bugs are filed, never encoded as "expected." Builds + dry-runs, then **offers** launch. |
| [**autonomous-advisor**](development/autonomous-advisor/SKILL.md) | Full hands-off execution: hand it a PRP and it runs the entire pipeline — design → plan → implement → finish → optimize — with zero human input. An **advisor** sub-agent stands in for the human at direction decisions; a separate **verifier** sub-agent gates every work product with evidence and can reject (maker≠checker). Crash-safe via a run-state file with phase-gate evidence and a failed-attempts log; hard guardrails (no prod deploys, no main pushes, no scope creep). |
| [**clean-room**](development/clean-room/SKILL.md) | Reimplement, port, or clone an existing codebase via a firewalled **clean-room rewrite**: multi-pass analysis (AST inventory + 10 analytical passes) produces an exhaustive design doc, an improvements triage, and a PRP — then hands off to `autonomous-advisor` for implementation. Three modes (full clean-room, Parity, Transparent), a mode-locked run-state file so a resumed session can never accidentally breach the firewall, runnable phase gates, and a contamination-scan merge gate. Ships the AST extractor / differ / coverage / contamination scripts. |
| [**improve-architecture**](development/improve-architecture/SKILL.md) | Human-in-the-loop **deep-module refactoring**: find shallow modules, leaky seams, and AI-driven architecture drift, then ship the fix. A strategic human owns direction; the AI explores for friction, presents candidates as a **visual before/after HTML report**, grills the chosen one into a module shape (updating `CONTEXT.md` / ADRs inline), then converts the approved design into an issue and a careful, behaviour-preserving migration. Bundles the deep-module glossary, deepening/testing strategy, design-it-twice interface exploration, and a depth-check → migrate → verify checklist. Run it as a periodic entropy check, not an autonomous pass. |
| [**arch-drift-watch**](development/arch-drift-watch/SKILL.md) | The **detection half of `improve-architecture`**: a scheduled, **FUGAZI**-driven watch that runs `boundaries`/`circular-deps`/`health`/`dupes` read-only, diffs against a committed **baseline**, and files only *new* drift to a triage inbox — routing structural-judgment items to a human review and duplication to `dead-code-reaper`. Detection-only by default (no code writes); trivial auto-fix is earned. Reports the delta, not the backlog. |
| [**skill-forge**](development/skill-forge/SKILL.md) | Automates the superpowers *writing-skills* discipline into a loop: **RED** pressure-test a fresh agent *without* the skill and capture the rationalizations it invents, **GREEN** patch the `SKILL.md` to close them, **REFACTOR** re-run until K consecutive clean runs — then a runnable **structure lint** (the jar's own `audit-jar.py`). Optional **MemBerry** grows a cross-skill rationalization corpus. The jar uses it to harden itself. |

*Thirteen skills and counting — the jar fills up over time.*

## For agents

Reading this repo programmatically? Route from [`skills.json`](skills.json) — a generated index of every skill's `name`, routing `description`, and `path` (one fetch, no directory crawl; it's gate-checked against the frontmatter, so it can't drift). Install via the plugin marketplace above (Claude Code) or copy a skill's folder (any host). Every push is verified by `python scripts/audit-jar.py` — the badge above is that gate. If you *operate* in this repo (run a loop cycle, fix a bug), the rules in [`AGENTS.md`](AGENTS.md) bind you.

## Self-hosted loop

The jar takes its own medicine. [loop-engineer](development/loop-engineer/SKILL.md) scaffolded a loop system into this very repo (state spine in `agent-state/`, role agents in `.claude/agents/`, drivers in `docs/prompts/`):

- **jar-audit** — keeps the jar publish-ready. Discovery is a deterministic gate, `python scripts/audit-jar.py`: frontmatter parses, descriptions carry triggers, names match directories, every relative link resolves, scripts compile, the scaffolder stays idempotent. Red check → one fix per cycle, verified by a separate agent.
- The repo also dogfoods the [**bug-pipeline**](development/bug-pipeline/SKILL.md) skill on itself — its instance lives in `.claude/agents/` + `docs/prompts/bug-pipeline-driver.md`, tracking to `agent-state/BUG_TRACKER.md`.

Run a cycle by handing your agent the matching driver in `docs/prompts/`. Both loops run at autonomy Level 2: they commit locally; a human reviews and pushes.
