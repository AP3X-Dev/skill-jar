---
name: plan-prune
description: "Use when a repo has fragmented, stale, duplicated, or conflicting planning documentation and needs one current plan grounded in the live codebase, git history, tests, and existing docs. Use for roadmap reconciliation, PRP/spec/handoff cleanup, plan updates after development drift, reducing outdated docs, or when agents are unsure which plan is authoritative. NOT for creating a brand-new plan from no prior docs, architecture redesign (use improve-architecture), or quality hardening loops (use optimization-loop)."
---

# Plan Prune

Planning docs rot by multiplication: a roadmap here, a handoff there, a PRP that predates the last sprint, an agent-state file that knows what actually shipped. This workflow finds the fragments, reconciles them against the current repo, and leaves one canonical plan that future work can trust.

**Output:** one canonical plan file (`docs/PLAN.md` or the repo's existing canonical path), a source inventory that accounts for every planning document found, current-state evidence from code/git/tests, a conflict and blocked-decision table, and a reduced planning surface where stale fragments are deleted, archived, or replaced with tiny pointer stubs so outdated plans are not floating around.

## Operating Contract

Consolidate down and update; do not merely summarize. Every surviving plan item must have a status, source, current evidence, and acceptance check. Every source document found must have a disposition and action: canonical, supporting reference, deleted, archived, stubbed, or blocked for human decision. Default to one active planning file. For "what exists now", repo state and runnable checks beat old docs. For "what should happen next", explicit user direction and current canonical decisions beat inferred code intent. Conflicts become blocked decisions, not guesses.

A blanket grant of trust ("do whatever makes sense", "I trust you", "delete the dead ones") authorizes you to run this process, not to skip it. It is not permission to guess what shipped, to delete content git does not yet hold, or to pick a product direction the docs left open. The looser the human's instruction, the more the process is the only thing keeping the result trustworthy — so follow every gate below.

You are a reconciler, not an architect. The canonical plan records the direction the docs and code already establish; it never substitutes the direction you think is best. If sources disagree on an approach (caching, storage, transport, anything), that is a `conflict` blocked decision, even when consolidating "feels like" the moment to clean it up by choosing.

## Known Pressure Rationalizations

Each of these has been used to skip a gate. If you catch yourself reasoning this way, stop and do the required action instead.

| Rationalization | Required response |
|---|---|
| "The human said 'do whatever makes sense' / 'delete the dead ones' — that's authorization to just remove stale files." | A loose grant authorizes the process, not skipping it. Still build the inventory, verify state, and honor the delete precondition for every file. |
| "Git history is the backup, so deleting loses nothing — I'll write 'see git history' and move on." | A pointer to git is not consolidation. Fold the doc's live claims/TODOs/open decisions into the canonical plan FIRST, and delete only when git already holds that file clean (untracked/staged/dirty → archive or block). |
| "The doc's own header says 'Status: SHIPPED' (or a recent 'Last updated'), so the feature obviously landed." | A doc's self-reported status is a claim to verify, not evidence. Confirm against code/git before marking anything past `implemented-unverified`. Self-declared "done" with no code evidence is `implemented-unverified` at best. |
| "Running the test suite to verify what shipped is overkill for a docs task — risk is basically zero." | You may skip the slow full suite, but never skip verification. Use cheap evidence (grep for the symbol/route/migration, `git log` for the merge, direct inspection). No evidence found → `implemented-unverified` or `blocked`, never `verified-complete`. |
| "These plans contradict on the approach; since I'm consolidating, I'll write the roadmap with the design I think is right." | You reconcile, you don't design. Record the disagreement as a `conflict` blocked decision and ask. Never resolve a product/architecture conflict by inserting your own pick. |
| "I'll fold the relevant bits from memory of one skim, then `rm` the originals in the same commit — re-reading carefully blows my time budget." | Read each doc you are about to retire closely enough to capture every open decision/TODO/blocked item into the canonical plan before deleting. If time runs out, leave the doc in place and block its retirement; never delete from a half-remembered skim. |
| "These plans look finished and have no open TODO list, so I'll mark the items 'Completed'." | Absence of a TODO list is not completion evidence. "Completed" requires the code wired and a check or inspection proving it. Otherwise `implemented-unverified` or `planned-not-built`. |

## When to Use

- Planning docs, roadmaps, specs, PRPs, handoffs, or TODO ledgers disagree.
- A project has moved forward and the plan no longer matches the code.
- An agent needs one restart artifact before continuing implementation.
- The user asks what is left, what is current, or to consolidate/update plans.

## When NOT to Use

- No prior plan exists and the user wants first-time product discovery.
- The main issue is code quality, defects, or optimization; use [optimization-loop](../optimization-loop/SKILL.md) or [bug-pipeline](../bug-pipeline/SKILL.md).
- The main issue is choosing architecture direction; use [improve-architecture](../improve-architecture/SKILL.md) or a systems-design skill.
- The user wants a historical report only. This workflow changes the planning surface.

## Source Discovery

Search broadly, then classify narrowly. Include docs outside `docs/` when they steer work.

Typical discovery commands:

```bash
rg --files | rg -i "(plan|roadmap|spec|prp|requirement|todo|backlog|handoff|status|milestone|phase|design|architecture|agent-state|tracker|triage|completed|failed)"
rg -n -i "todo|tbd|planned|phase|milestone|blocked|deferred|accepted|remaining|next|done|complete|not implemented|future|source of truth|canonical" .
git log --oneline -30
git status --short --branch
```

Also inspect project conventions: README, AGENTS/CLAUDE/GEMINI files, `.github/`, issue exports, `agent-state/`, existing `docs/adr/`, release notes, and recent branch names.

## The Process

### 1. Preflight

Check git state first. If the tree is dirty, list the changed files and decide whether they are part of the planning consolidation. Do not overwrite uncommitted user edits. If code is dirty, account for it separately as "uncommitted current state" instead of treating it as verified shipped work.

**Delete precondition:** a planning doc may be DELETED only if git already holds its content — it is tracked and committed clean (no unstaged or staged changes for that path). For any planning doc that is untracked, staged-but-uncommitted, or dirty, git history is not yet the archive, so ARCHIVE it (move under the archive convention) or BLOCK it for a human decision instead. Never delete content git does not yet hold.

### 2. Build the Source Inventory

For every planning-like document, record:

- Path and title.
- Last modified signal (`git log -1 -- <path>` when available).
- What it claims is current, next, blocked, or done.
- Whether it appears authoritative, supporting, stale, or historical.
- Contradictions with other docs or with the code.

Use the inventory template in [references/plan-template.md](references/plan-template.md).

### 3. Audit Current Development State

Ground the plan in the repo as it is now:

- Git: current branch, latest commits, merged/unmerged branches, dirty state.
- Build/test: known verification commands from README, package scripts, CI, Makefile, or repo-specific gate. Run cheap/current gates when safe; record failures honestly.
- Code shape: entry points, routes, commands, migrations, schemas, feature flags, config, and modules named by the planning docs.
- State ledgers: completed items, failed attempts, bug trackers, triage inboxes, release notes.

Do not call an item done because a file exists, because the doc's own header says "shipped/done", or because the doc has no open TODO list. A doc's self-reported status is a claim to verify, not evidence. Mark `verified-complete` only when code is wired and a runnable check or direct inspection proves it.

Verification is mandatory, but the slow full suite is not. "It's only docs" does not exempt you from gathering evidence. For each item you would call done, use the cheapest evidence that actually confirms it: grep for the symbol/route/migration/handler, `git log`/`git log --follow` for the merge that landed it, or direct file inspection. Run the full test suite only if cheap evidence is inconclusive and the call matters. Found no evidence within your time budget → record `implemented-unverified` or `blocked`, never `verified-complete`.

### 4. Reconcile Claims

Classify each meaningful plan item:

| Status | Meaning |
|---|---|
| `verified-complete` | Implemented, wired, and backed by evidence. |
| `implemented-unverified` | Code appears present, but no gate or inspection proves it works. |
| `planned-not-built` | Still valid but not present in the repo. |
| `changed-from-plan` | Code intentionally or accidentally diverged from an older plan. |
| `duplicate` | Same work appears in multiple docs; keep one entry in the canonical plan. |
| `conflict` | Sources disagree and the repo cannot decide the product direction. |
| `obsolete` | No longer relevant because the product direction or code changed. |
| `blocked` | Needs a human decision, credential, environment, or expensive-to-reverse choice. |

When evidence is thin, use `implemented-unverified` or `blocked`; do not over-promote.

### 5. Choose the Canonical Plan Path

Prefer the repo's existing convention if it is clear (`docs/ROADMAP.md`, `docs/PLAN.md`, `PORTAL_DEVELOPER_START_HERE.md`, etc.). If no convention exists, create `docs/PLAN.md`. The canonical plan must be the only file that claims to be the current plan. Where [spec-driven-change](../spec-driven-change/SKILL.md) is adopted, `openspec/specs/` is the canonical *requirements* layer (what-must-hold); the canonical plan links to it and reconciles the *work* surface (what-to-do-next) against it rather than duplicating the requirements — and this reconciled plan can seed the initial living specs during that skill's onboarding.

### 6. Write or Update the Canonical Plan

Use [references/plan-template.md](references/plan-template.md). The plan must include:

- Current objective and product state.
- Source inventory with dispositions.
- Current-state evidence from repo/git/tests.
- A work plan ordered as Now / Next / Later.
- Blocked decisions and questions.
- Verified-complete items that should not be reworked.
- Verification commands and freshness date.

Keep historical detail in the source inventory or supporting docs; the plan itself should be operational.

### 7. Reduce the Old Planning Surface

Do not leave stale docs in active locations. After useful claims are folded into the canonical plan's inventory and work table, retire the old planning fragment.

Fold before you retire, and read before you fold. Read each doc you are about to delete closely enough to capture every open decision, TODO, and blocked item into the canonical plan — a half-remembered skim is not enough, and "see git history" in the canonical plan is a citation, not consolidation. If your time budget runs out before a doc is fully folded, leave it in place and block its retirement rather than deleting it.

- **Canonical doc:** update in place.
- **Supporting reference:** keep only when it provides durable design detail that would bloat the canonical plan; list exactly why it remains.
- **Obsolete planning fragment:** delete it after its useful claims are represented in the canonical plan, and only once git already holds it (tracked and committed clean). Git history is the archive only for content git has. If the fragment is untracked, staged-but-uncommitted, or dirty, archive or block it instead of deleting — never delete content git does not yet hold.
- **Historical but useful fragment:** move it under the repo's archive convention, or `docs/archive/plans/` if no convention exists.
- **Externally linked or high-traffic path:** replace it with a tiny pointer stub only when deleting/moving would break expected links.
- **Ambiguous or expensive-to-reverse removal:** add it to Blocked with the proposed retirement action and ask.

Pointer stub:

```md
# Superseded

This planning document was consolidated into `<canonical-plan-path>` on <YYYY-MM-DD>.
Use that file as the current plan.
```

Banner-only cleanup is a last resort. A stale doc left in place with a banner is still a floating planning document unless a link-preservation reason is recorded.

### 8. Verify the Consolidation

Before finishing:

- Re-run the repo's documentation/skill/link gate if one exists.
- Check that every discovered planning source appears in the source inventory.
- Search for leftover "source of truth", "current plan", "next steps", and "TODO" claims outside the canonical plan and supporting references; delete, archive, stub, or block each one.
- Confirm the canonical plan includes the current branch/commit, verification commands, and freshness date.
- Confirm no stale planning doc remains in an active path without an explicit supporting-reference reason or pointer-stub reason.

## Optional: Memory

If a project memory system is available, load prior plan decisions before reconciliation and store only the final canonical objective, blocked decisions, and superseded-doc dispositions after the update. Files remain authoritative; memory is just an index.

## Common Mistakes

- **Writing a prettier summary.** The deliverable is an updated plan surface, not a narrative.
- **Leaving old docs with banners everywhere.** Banners are for link preservation. Consolidation should reduce active files.
- **Trusting the newest doc.** Newer can still be wrong; reconcile against code and gates.
- **Keeping history as active docs.** Git history preserves deleted planning fragments; the active tree should carry the current plan.
- **Marking work done from file presence.** Done means wired and verified.
- **Leaving stale docs unmarked.** If an old roadmap still looks current, the next agent will follow it.
- **Resolving product conflicts by inference.** When docs disagree about direction, block and ask.

---

*Once the plan is canonical, hand off to [sprint-ticket-runner](../sprint-ticket-runner/SKILL.md) to EXECUTE it as durable tickets, or to [improve-architecture](../improve-architecture/SKILL.md) for architecture direction. Pairs well with [optimization-loop](../optimization-loop/SKILL.md), which can use the consolidated plan as its intent source before building a hardening backlog.*
