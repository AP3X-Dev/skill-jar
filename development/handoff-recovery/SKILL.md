---
name: handoff-recovery
description: "Use when resuming interrupted or compacted repository work, reconciling a stale handoff, inheriting an uncertain worktree, or determining whether a partially implemented task is complete, verified, blocked, or safe to continue. Produces a typed evidence-bound recovery record and exactly one continuation without changing repository or hosted state. NOT for disaster or deleted-data recovery, incident remediation, consolidating plans, ordinary new-task planning, or executing the recovered next action."
---

# Handoff Recovery

Recover the exact state of interrupted repository work before continuing it.
A handoff is a claim-bearing source, not current truth. Reconcile the current
request, applicable instructions, Git and worktree identity, local-change
custody, durable state, source, and executable evidence into one bounded record.

## When NOT to use

- For an operational incident or repair, use
  [diagnose-loop](../diagnose-loop/SKILL.md).
- For fragmented plan consolidation, use
  [plan-prune](../plan-prune/SKILL.md).
- For disaster recovery or restoration of deleted data, stop and use the
  system's authorized recovery process.
- For ordinary planning of a new task with no interrupted state, use the normal
  planning workflow.

## Non-mutation contract

The entire recovery invocation is read-only. Do not reset, clean, checkout or
switch, stash, apply a patch, edit application files, merge, rebase, continue or
abort a Git operation, commit, push, delete, stop processes, install
dependencies, run migrations, replay work, or mutate a hosted system. Do not
stage a file to test ownership. Broad permission to "continue" does not waive
this boundary.

Classify a proposed command by semantic effect before running it. A command that
can update an index, cache, lease, lock, working file, service, or remote state
is not read-only merely because it is commonly used for inspection. Record it
as unexecuted or choose a safer discriminator. Emitting the single
`Continuation` row ends this workflow: neither `exact_next_action` nor
`acceptance_command` may run without a separate request and authorization.

## 1. Bind the recovery request

Capture the current user request before examining branch-shaped clues. Bind:

- canonical absolute repository root;
- requested outcome and exact task or slice;
- environment and required evidence boundary;
- authorization boundary;
- referenced handoff or state source; and
- current RFC 3339 UTC time.

Resolve paths within the user's scope and retain exact repository/worktree
identity. If repository, task, environment, or authority cannot be bound, keep
it `unknown`; do not substitute the current directory, default branch, latest
timestamp, or most polished state file.

The newest user instruction defines desired outcome and permission, but does
not prove repository state or ownership. Repository instructions constrain the
work but do not prove completion. Git objects prove committed identity; index
and working-tree observations prove current deltas; neither proves intent.
Recorded state proves only what its identified bytes said. Source proves current
bytes. A command result proves only its exact command, cwd, environment, time,
exit status, inputs, and captured output. Runtime evidence proves only the
queried boundary.

## 2. Inventory every relevant repository and worktree

Before selecting a continuation, inventory all worktrees that can plausibly hold
the task. For each record canonical root and worktree path, attached/detached/
unborn branch state, HEAD object, upstream if locally available, cleanliness,
sparse/submodule indicators, and active merge, rebase, cherry-pick, revert, or
bisect state. Compute ahead/behind only from locally available refs; recovery
does not authorize network access.

Do not provisionally select a worktree from cwd, branch name, staged changes,
modification time, or recent activity. First establish task-to-worktree identity
from a task record plus bound path/content evidence. A detached worktree or
in-progress operation remains a first-class candidate and is never absorbed,
continued, or abandoned during recovery.

## 3. Establish custody of local changes

Inventory staged, unstaged, untracked, deleted, renamed, copied, conflicted,
type-changed, ignored-relevant, and submodule state separately. Record safe
object IDs or SHA-256 identities. Do not read ignored content merely to decide
relevance; record safe path metadata only unless the user explicitly placed the
content in scope. Ignored content has unknown custody unless independently
task-bound.

For every local change assign:

- task relation: `confirmed`, `plausible`, `unrelated`, `conflicting`, or
  `unknown`;
- ownership: `current_task`, `other_work`, `shared`, or `unknown`;
- continuation overlap: `yes`, `no`, or `unknown`; and
- risk: `none`, `low`, `material`, `destructive`, or `unknown`.

`confirmed` requires an explicit task record plus content/path binding. Branch
name, directory, timestamp, polish, user permission, or similarity is
insufficient. Ownership of an unexplained change stays `unknown`.

Overlap includes same-path edits, rename source or destination, deletion,
submodule boundary, generated source or consumer, dependency effects, and any
action that could overwrite, absorb, hide, duplicate, or misattribute the
change. Preserve all uncertain changes and do not mutate them to test custody.

## 4. Reconcile durable state and claims

Discover applicable repository instructions and narrowly relevant handoff,
run-state, tracker, decision, failed-attempt, roadmap, source, and Git-history
records. Search by the bound task and paths rather than filename keywords or
mtime alone. For every StateSources row record exact locator, SHA-256 hash,
tracked state, checkpoint, claimed next action, freshness, decision status,
owner, authority evidence, contradictions, and supporting evidence.

A state source becomes stale or unbound when its repository revision, worktree,
task, covered path hashes, referenced decision, or required boundary changes.
Keep conflicts explicit; never pick the convenient authority. A pending,
rejected, or authority-unbound decision gate blocks continuation.

Atomize recovery statements into Claims with exactly one status:

- `completed`: the intended artifact exists at the recovered revision, without
  sufficient current verification;
- `verified`: the artifact or outcome exists and current applicable checks pass
  against its complete input identity and required boundary;
- `implemented_unverified`: implementation bytes exist but required checking is
  absent or stale;
- `in_progress`: evidence binds partial work to the task;
- `not_started`: evidence establishes that the task has not begun;
- `blocked`: a known condition prevents progress; or
- `unknown`: evidence cannot select a stronger status.

Each Claim cites its exact subjects, evidence, checks, contradictions, boundary,
confidence, and limitations. HEAD lacking a change does not make uncommitted
work absent. Narrative completion does not imply verification.

## 5. Re-establish executable truth

Identify the smallest safe checks capable of separating stale state from current
state. Before execution, record exact command, canonical cwd, environment,
semantic mutation class, bounded cost, timeout, expected proof, proof limit, and
complete input identity. Commands contain credential handles or environment
variable names, never values.

Run only authorized checks classified `read_only`. Missing dependencies,
unavailable services, empty suites, command errors, and commands that did not
run are not passes. A historical green result is stale when any relevant
revision, index/working-tree content, dependency lock or installed dependency
identity, configuration, fixture, environment, command, or gate definition has
changed.

An unexecuted check is explicit: `result=not_run`, with `exit_status`,
`executed_at`, and `output_hash` all `not_applicable`. It supplies no execution
evidence. An executed check records integer exit status, execution time, and a
SHA-256 of its captured safe output.

Keep proof boundaries exact. Fixture evidence proves its fixture; local evidence
proves only the identified local inputs; hosted evidence proves only the queried
hosted surface; live evidence proves only the observed live path. Production
requires direct identity-bound observation in the named production environment.
Local source and gates cannot make a deployment-verification outcome
`already-complete`.

## 6. Bound sensitive-history inspection

Repository history, reflogs, editor recovery data, shell history, and similar
sources can expose unrelated work or personal data. Before proposing any such
read, bind repository/worktree, task, exact source, path set, time or entry
range, fields required, permission, access boundary, sensitivity, redaction,
retention, cost, and stop condition. Prefer repository-contained metadata over
user-profile-wide content.

If the read cannot be bounded or requires unrelated content, do not run it.
Represent the unresolved question with a Discriminators row whose safety or
access remains `blocked` or `unknown`. Never recommend a broad search of all
reflogs, stashes, editor histories, or user files as routine recovery.

Replace removed values with exactly `[REDACTED:credential]`,
`[REDACTED:secret]`, or `[REDACTED:personal]`. If a restricted raw source is
retained, represent its locator as `restricted:sha256:<64-lowercase-hex>`.
That locator provides provenance, not permission to disclose or execute.
A redaction marker without a SHA-256-bound safe output or locator cannot support
identity. Reject authorization headers, private-key material, and credential
values embedded in URLs or commands.

## 7. Select one continuation

Choose the earliest unchecked action supported by the complete recovery
closure. Tie it to one selected Repositories row and its exact worktree and
revision; a non-empty exact decomposition of the requested outcome; supporting
claims, checks, evidence, material conflicts, decision gates, preserved local
changes, discriminator, and next owner.

State exact target paths, prerequisites, next action, and acceptance command.
Actual records never contain placeholder paths or placeholder commands. If an
exact canonical worktree, action, or command cannot be written, use `unknown`,
leave the check `not_run`, and return the applicable blocked verdict. Do not
repeat a completed step merely because a handoff is stale, and do not start over
as a substitute for custody.

## Canonical recovery record

Begin with exactly these root fields. Angle-bracket text is template notation;
an actual record uses a bound value or literal `unknown`, never a placeholder.

```yaml
---
schema_version: handoff-recovery/v1
repository_root: <absolute-path-or-unknown>
requested_outcome: <text-or-unknown>
task_slice: <text-or-unknown>
environment: <name-or-local-or-unknown>
authorization_boundary: <text-or-unknown>
generated_at: <RFC-3339-UTC>
verdict: <ready-to-continue-or-blocked-by-state-conflict-or-blocked-by-unknown-custody-or-blocked-by-missing-evidence-or-already-complete>
---
```

Then emit these nine tables in exactly this order and with exactly these
columns.

## Repositories

| id | canonical_root | worktree | branch_state | head | upstream | operation_state | cleanliness | evidence_ids |
|---|---|---|---|---|---|---|---|---|

## Evidence

| id | kind | locator | hash_or_object | captured_at | command | cwd | exit_status | boundary | scope | observation | proves | limits | strength | freshness |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

## LocalChanges

| id | repository_id | path | tracking_state | index_state | worktree_state | object_or_hash | task_relation | ownership | continuation_overlap | evidence_ids | risk |
|---|---|---|---|---|---|---|---|---|---|---|---|

## StateSources

| id | kind | locator | hash | tracked_state | stated_checkpoint | stated_next_action | freshness | decision_status | owner | authority_evidence_ids | contradiction_ids | evidence_ids |
|---|---|---|---|---|---|---|---|---|---|---|---|---|

## Claims

| id | statement | status | subject_ids | evidence_ids | check_ids | contradiction_ids | confidence | boundary | limits |
|---|---|---|---|---|---|---|---|---|---|

## Checks

| id | exact_command | cwd | environment | mutation_class | cost_bound | timeout_ms | result | exit_status | executed_at | output_hash | input_identity | boundary | proves | limits | evidence_ids |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

## Conflicts

| id | subject | source_a | source_b | impact | material | resolution_status | discriminator_id |
|---|---|---|---|---|---|---|---|

## Discriminators

| id | question | exact_read_only_action | cwd | permission | cost_bound | timeout_ms | signal_a | signal_b | side_effects | owner | safe_status |
|---|---|---|---|---|---|---|---|---|---|---|---|

## Continuation

| id | verdict | repository_id | exact_next_action | target_paths | prerequisites | acceptance_command | decision_gate_ids | preserved_changes | outcome_claim_ids | claim_ids | check_ids | conflict_ids | evidence_ids | discriminator_id | next_owner | rationale |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

Every cell is required. Unknown scalars use `unknown`; `not_applicable` is used
only where this contract permits it. Arrays are compact JSON. `target_paths` and
`prerequisites` are arrays of strings; every `*_ids` field and
`preserved_changes` is an array of IDs. Empty arrays are `[]`.

All rows share one stable, globally unique ID namespace. References are typed:

- Repositories `evidence_ids` references Evidence.
- LocalChanges `repository_id` references Repositories and `evidence_ids`
  references Evidence.
- StateSources authority/evidence arrays reference Evidence and
  `contradiction_ids` references Conflicts.
- Claims `subject_ids` references Repositories, LocalChanges, or StateSources;
  its other reference arrays target the named tables.
- Checks `evidence_ids` references Evidence.
- Conflicts `source_a` and `source_b` reference Evidence, StateSources, Claims,
  or Checks; its discriminator references Discriminators or an allowed literal.
- Continuation `repository_id` references the selected Repositories row;
  `decision_gate_ids` references StateSources with `kind=decision`;
  `preserved_changes` references LocalChanges; `outcome_claim_ids` is the
  non-empty subset of Claims that exactly decomposes `requested_outcome`;
  `claim_ids` contains that subset plus supporting Claims; remaining arrays
  reference their named tables.

Every other singular `*_id` references its named table. Missing, duplicate,
dangling, or wrongly typed references are invalid.

Exactly one Continuation row exists. Its verdict equals the root verdict and is
derived only from its referenced closure. A blocked Continuation references one
safe capable discriminator or uses `none_available`; the latter requires a
`next_owner` and rationale naming the missing inputs. A non-blocked Continuation
uses `discriminator_id=not_applicable`.

## Exact encodings

Use `sha256:<64-lowercase-hex>` for file, safe captured-output, and state-source
hashes. Use `git:sha1:<lowercase-oid>` or `git:sha256:<lowercase-oid>` for Git
objects. Modification time is never freshness evidence. `captured_at` and an
executed Check's `executed_at` use RFC 3339 UTC. The only timestamp sentinels are
`unknown` where permitted and `not_applicable` for an unexecuted Check.

Evidence `scope` is exactly this compact JSON object with no missing or extra
keys:

```json
{"repository":"<string>","worktree":"<string>","task":"<string>","environment":"<string>","paths":["<string>"]}
```

Checks `input_identity` is exactly this compact JSON object. All values are
strings and there are no missing, extra, or duplicate keys:

```json
{"revision":"<identity>","index_tree":"<identity>","worktree_tree":"<identity>","dependency_lock":"<identity>","installed_dependencies":"<identity>","configuration":"<identity>","fixtures":"<identity>","environment":"<identity>","command":"<identity>","gate_definition":"<identity>"}
```

Each identity is a defined SHA-256 or Git object form, or literal `unknown` or
`not_applicable` where valid. An `unknown` input required by the check caps
freshness and prevents current verification.

Every `cost_bound` is compact JSON:
`{"value":<nonnegative-number-or-"unknown">,"unit":"seconds|requests|bytes|usd|unknown"}`.
`timeout_ms` is a nonnegative integer or `unknown`.

## Closed vocabularies

- Repositories `branch_state`:
  `attached|detached|unborn|unknown`; `operation_state`:
  `none|merge|rebase|cherry_pick|revert|bisect|unknown`; `cleanliness`:
  `clean|dirty|conflicted|unknown`.
- Evidence `kind`:
  `user_request|repo_instruction|git_object|git_state|state_file|source|command_result|runtime_observation|other`;
  `boundary`: `fixture|local|hosted|live|production|unknown`; `strength`:
  `reported|source_observed|check_supported|identity_bound`; `freshness`:
  `current|stale|unbound|conflicting|unknown`.
- LocalChanges `tracking_state`:
  `tracked|untracked|ignored|submodule|unknown`; `index_state` and
  `worktree_state`:
  `absent|added|modified|deleted|renamed|copied|unmerged|type_changed|ignored|unknown`;
  `task_relation`: `confirmed|plausible|unrelated|conflicting|unknown`;
  `ownership`: `current_task|other_work|shared|unknown`;
  `continuation_overlap`: `yes|no|unknown`; `risk`:
  `none|low|material|destructive|unknown`.
- StateSources `kind`:
  `repo_instruction|handoff|run_state|tracker|decision|failed_attempt|roadmap|other`;
  `tracked_state`:
  `tracked_clean|tracked_modified|untracked|ignored|outside_repo|unknown`;
  `freshness`: `current|stale|unbound|conflicting|unknown`; `decision_status`:
  `approved|rejected|pending|not_applicable|unknown`. Only a `decision` row may
  use approved, rejected, or pending; all others use `not_applicable`.
- Claims `status`:
  `completed|verified|implemented_unverified|in_progress|not_started|blocked|unknown`;
  `confidence`: `reported|source_observed|check_supported|identity_bound`;
  `boundary`: `fixture|local|hosted|live|production|unknown`.
- Checks `mutation_class`:
  `read_only|semantic_side_effect_possible|mutating|unknown`; `result`:
  `passed|failed|error|not_run|unavailable`; `boundary`:
  `fixture|local|hosted|live|production|unknown`.
- Conflicts `material`: `yes|no`; `resolution_status`:
  `unresolved|resolved_by_evidence|human_decision_required|no_safe_discriminator`.
  A resolved conflict uses `discriminator_id=not_applicable`; actionable
  unresolved conflict references a safe capable Discriminator; human-decision
  required may reference its decision discriminator or `none_available`; no
  safe discriminator requires `none_available`.
- Discriminators `safe_status`: `safe|unsafe|blocked|unknown|none_available`.

Reject undeclared values instead of normalizing them.

## Strength, freshness, and custody promotion

Strength is ordered:
`reported < source_observed < check_supported < identity_bound`.

- User and state assertions begin `reported`.
- Exact current bytes or Git state with a content/object identity may reach
  `source_observed`.
- A current applicable passing Check may reach `check_supported`.
- `identity_bound` also requires complete repository, worktree, revision, input
  identity, task binding, and required evidence boundary.

A Claim is capped by its weakest referenced Evidence, StateSource freshness,
required Check, subject identity, custody binding, and evidence boundary.
`stale`, `unbound`, `conflicting`, or `unknown` freshness caps dependent claims
at `reported`. A failed, erroring, unavailable, or not-run Check cannot support
`check_supported`. A lower evidence boundary cannot promote a higher-boundary
claim. `verified` requires at least `check_supported`. Many weak records do not
compensate for one missing required binding.

Custody is part of promotion, not a side note. Every inventoried change must be
overlap-assessed with evidence. Unknown ownership plus `yes` or `unknown`
overlap blocks continuation even when source looks complete or checks pass.

## Verdict derivation

Use exactly one of these verdicts:

- `ready-to-continue`
- `blocked-by-state-conflict`
- `blocked-by-unknown-custody`
- `blocked-by-missing-evidence`
- `already-complete`

Derive it in this precedence order from the Continuation closure:

1. If an overlapping LocalChanges row has unknown ownership and overlap `yes`
   or `unknown`, return `blocked-by-unknown-custody`.
2. Otherwise, if a material conflict is unresolved or needs a human decision,
   or a referenced decision gate lacks approved status plus authority evidence,
   return `blocked-by-state-conflict`. This includes conflict between the
   current request and applicable instructions or authorization.
3. Otherwise, if a required root, revision, source, artifact, current Check,
   complete input identity, or evidence boundary is unavailable, return
   `blocked-by-missing-evidence`.
4. Otherwise, if every outcome Claim is `verified`, at least
   `check_supported`, current, input-bound, and proven at the requested
   boundary, return `already-complete`.
5. Otherwise, return `ready-to-continue` only when repository/worktree/revision/
   task identity is bound and the earliest unchecked action cannot overlap
   unknown custody or violate a decision gate.

Keep secondary facts in Claims and Conflicts. Do not reinterpret different
worktrees or revisions as one state.

## Validate before returning

Reject the record rather than repairing it by guess when any of these fail:

1. root keys, schema, timestamp, or verdict vocabulary;
2. nine-table order, exact columns, required cells, or exactly-one Continuation;
3. global ID uniqueness, compact arrays, reference resolution, or reference
   types;
4. exact SHA-256/Git identities, scope object, input-identity object, cost,
   timeout, executed/not-run encodings, or timestamps;
5. enum, decision-gate, material-conflict, ignored-custody, requested-outcome,
   preserved-change, or discriminator rules;
6. contradictory result/exit/time fields, placeholder actions represented as
   exact or executed, or a conclusion above weakest evidence/freshness/custody/
   boundary;
7. exposed sensitive material, unbound redaction, or a broad privacy-invasive
   history read; or
8. a Continuation that omits any material conflict or runs its action/check.

Report the verdict and bounded recovery conclusion, then the canonical record.
For a blocked verdict, name the cheapest safe capable discriminator and owner,
or state `none_available` with the missing inputs and next owner. For
`ready-to-continue`, identify why earlier steps need not be repeated. Stop after
the record.

## Pressure defenses

| Shortcut | Required response |
|---|---|
| "The task-named branch has staged work, so select it provisionally." | Bind the current request and task-to-worktree identity first. Inventory every relevant worktree and operation state; if identity is unresolved, block with a safe discriminator rather than selecting a branch. |
| "The command can keep `<worktree-path>` until the operator fills it in." | An actionable check or continuation uses the resolved canonical cwd and exact command. A placeholder is `unknown`, remains `not_run`, and forces the applicable blocked verdict. |
| "A concise prose recap is enough to resume." | Emit the stable nine-table record with globally unique IDs, typed references, complete check input identity, custody overlap, proof boundaries, and weakest-link promotion. |
| "The handoff says tests passed, so verification carries forward." | Rebind the gate to revision, trees, dependencies, configuration, fixtures, environment, command, and gate definition. Any material identity change makes the historical result stale. |
| "The changed file is beside the task, so it belongs to this work." | Proximity, polish, time, branch name, and permission do not prove ownership. Preserve it as unknown custody until a task record plus content/path binding resolves it. |
| "Search all reflogs and editor history; it is read-only." | First bound source, repository/worktree, task, paths, time/entry range, fields, permission, privacy, retention, cost, and stop condition. If that cannot exclude unrelated content, do not inspect it. |
| "Start over to avoid trusting stale state." | Starting over can overwrite or duplicate valid work. Recover the earliest unchecked action while preserving every unresolved change. |
| "A local pass confirms the deployed task is done." | Keep local, hosted, live, and production boundaries separate. Deployment completion requires identity-bound evidence at the requested boundary. |
