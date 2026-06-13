---
name: instrument-observability
description: "Adds production-grade application observability instrumentation with Sentry by default: error tracking, crash reporting, tracing, release health, workflow breadcrumbs, user/agent attribution, privacy filtering, cost/usage tracking, and real-runtime verification. Use when adding Sentry, telemetry, tracking, monitoring, crash reporting, performance tracing, session replay, workflow failure monitoring, agent cost/usage monitoring, frontend/backend correlation, Electron crash capture, or production debugging; use existing OpenTelemetry, Datadog, New Relic, Honeycomb, LogRocket, Highlight, or structured-log standards only when the repo or user requires them. NOT for diagnosing one live incident (use diagnose-loop), a general quality/hardening pass (use optimization-loop), or fixing one known bug (use the host bugfix skill) — this skill adds instrumentation, it does not run the debugging loop."
---

# Instrument Observability

Instrument an application so it can explain itself when it breaks, slows down,
burns money, or fails a user workflow. Default to **Sentry** unless the repo has
an existing observability standard, the user asks for another provider, or
privacy/local-only constraints make structured logs the correct first step.

**Output:** a working observability implementation: one centralized telemetry
module, privacy filters before capture, release/environment metadata, identity
set only after sign-in/profile fetch, critical workflows wrapped with spans and
breadcrumbs, handled failures captured without swallowing errors, tests/smoke
checks run, and dashboards/alerts recommended.

## When NOT to use

This skill **adds instrumentation; it does not run the debugging loop.**

- Diagnosing a single live incident → diagnose-loop.
- A general quality/hardening pass → optimization-loop.
- Fixing one known bug → the host bugfix skill (external).

The telemetry, dashboards, and alerts produced here are the input
[production-readiness](../../systems-design/production-readiness/SKILL.md)
consumes at its launch gate.

## Operating Contract

- Do not add provider code until the investigation gate is complete. Use real
  subagents when the host supports them; otherwise emulate separate
  investigation passes with isolated notes.
- Prefer one reusable wrapper over scattered provider calls. Provider setup
  belongs in one module such as `src/observability.ts`,
  `src/lib/observability.ts`, `server/observability.py`, or
  `electron/observability.ts`.
- Add privacy filtering before any event, breadcrumb, replay, span, or log can
  leave the process. Never send secrets, tokens, cookies, raw prompts, raw model
  responses, transcripts, audio, payment data, full request/response bodies, or
  customer records.
- High-cardinality and correlation identifiers (`tenant_id`, `job_id`,
  `request_id`, `submission_id`, `checkout_session_id`, and similar) are not
  safe by virtue of where they sit. Moving them from `tags` to event `extra`,
  `context`, or a span attribute does not make them safe — it just relocates the
  same leak/cardinality problem. They may be attached only after the
  Privacy/Data-Safety report has mapped each one as a sensitive surface and
  assigned a `safe_replacement` (hash, opaque id, count, or category), and only
  in the form that report approves.
- An existing logger, sanitizer, or scrubber is not a substitute for the
  sensitive-surface map. "There is already a sanitizer" does not let you attach
  correlation IDs before the surfaces and their safe replacements are mapped;
  the map decides what may be attached, the sanitizer only enforces it.
- Preserve behavior. Telemetry failures must not break the app; captured errors
  must be rethrown unless existing code intentionally swallows them.
- Do not claim production-ready telemetry until real runtime smoke events
  arrive with correct release, environment, attribution, readable stacks, and
  redaction verified. Completion requires the **full** relevant smoke checklist
  in the playbook, not a sampled subset. "Build succeeds plus one forced
  renderer error plus one forced main/IPC error" is partial coverage, not done —
  every P0 surface the merged plan named (workflow success *and* failure,
  external-dependency failure, identity set/clear, child/worker lifecycle and
  crash/respawn, release/source-map verification, redaction) must run or be
  listed as an explicit `known_gap` with a `safe_next_step`. Deferring traces,
  source-map upload, dashboards, breadcrumbs, worker lifecycle, or the test
  suite is allowed only as a logged gap, never as a silent "later polish."

## Provider Decision

Use Sentry unless a stronger local signal says otherwise:

1. Extend an existing Sentry setup if present.
2. Use the org's explicit provider if the repo documents one.
3. Use Sentry when the user asked for Sentry or did not specify a provider.
4. Use OpenTelemetry when vendor neutrality, collectors, or multi-backend export
   is required.
5. Use Datadog/New Relic/Honeycomb/LogRocket/Highlight only when already
   standard or specifically requested.
6. Use structured logs first for local-only or privacy-restricted apps.

Keep the same wrapping model with any provider: errors, traces/spans,
breadcrumbs/logs, metrics, user identity, releases, privacy filters, and
verification.

## Required Workflow

1. **Inspect the app.** Identify framework, runtime, entry points, auth,
   logging, env/config, release/version source, build/test commands, current
   error handling, existing provider, and sensitive data surfaces.
2. **Run the investigation.** Follow
   [references/investigation-model.md](references/investigation-model.md).
   Keep each specialist report separate, then merge into a prioritized plan.
3. **Pass the investigation gate.** Before code changes, print the required
   `Sub-agent investigation complete` summary with critical workflows, failure
   surfaces, external dependencies, identity moments, cost/latency hotspots,
   process boundaries, sensitive risks, recommended focus, and will-not-track
   items.
4. **Implement in priority order.** Use
   [references/instrumentation-playbook.md](references/instrumentation-playbook.md)
   for what to wrap, identity rules, release/source-map rules, tests, smoke
   checks, dashboards, and alerts.
5. **Use provider patterns.** For Sentry details, safe wrappers, redaction, and
   examples, read [references/sentry-patterns.md](references/sentry-patterns.md).
6. **Verify with runnable gates.** Run lint/typecheck/tests plus provider smoke
   checks that exercise handled/unhandled errors, workflow success/failure,
   external dependency failure, identity set/clear, release metadata, readable
   stacks, and redaction.
7. **Report exactly what happened.** Use the JSON output contract or the
   human-readable completion format below. Do not claim checks that were not
   actually run.

## Investigation Gate

No instrumentation code may be added before this is produced. The gate is **not
waivable** by a deadline, a demo, an "obvious" first target (e.g. "just
instrument the expensive LLM calls"), or "the entry points are obvious." A
deadline shrinks *scope* (what lands as P0 vs. a logged gap), never the gate or
the merged prioritized plan. Initializing the provider in "obvious entry points"
before the merged plan exists **is** adding instrumentation code — it fails this
gate. Reusing an existing logger/telemetry boundary is still provider code: it
may not be wired to emit telemetry until the gate passes.

```text
Sub-agent investigation complete.

Found:
- critical workflows:
- failure surfaces:
- external dependencies:
- identity moments:
- cost/latency hotspots:
- process boundaries:
- sensitive telemetry risks:

Recommended focus:
1.
2.
3.

Will not track:
1.
2.
3.
```

## What To Instrument First

Prioritize workflow importance over technical convenience.

- **P0:** app boot/config/auth/profile fetch, critical user workflows, costly
  model/provider calls, payment/submission flows, worker/job failures, Electron
  main/renderer/IPC/child process crashes, privacy filters, release metadata.
- **P1:** dependency spans, retry/timeout metrics, user actions that explain
  failures, source-map upload, dashboards and actionable alerts.
- **P2:** lower-risk breadcrumbs, additional metrics, non-critical background
  work, replay only after masking policy is explicit.
- **Do not track:** raw prompts/transcripts, secrets, full bodies, sensitive
  screens without masking, every click, expected validation failures, or noisy
  warnings.

## Known pressure rationalizations

Each of these is a dodge that feels reasonable under deadline or scope pressure.
The required response is the rule, not the excuse.

| Rationalization | Required response |
|-----------------|-------------------|
| "Demo deadline — skip the sub-agent investigation/merged plan and just add Sentry init in the obvious entry points." | The gate is not waivable by deadline or demo. A deadline shrinks P0 scope, never the gate. Provider init in "obvious" entry points before the merged plan is instrumentation code and fails the gate. |
| "Capture only crash/error paths now; defer traces, source-map upload, dashboards, breadcrumbs, deep worker lifecycle, and tests." | Crash/error-only is a P0 subset, not completion. Each deferral is an explicit `known_gap` with a `safe_next_step`, not a silent omission — and source-map verification on JS/TS/Electron is P0, not deferrable to polish. |
| "Build plus one forced renderer error plus one forced main/IPC error is enough runtime proof." | That is partial smoke coverage. Run the full relevant checklist (workflow success *and* failure, dependency failure, identity set/clear, child/worker crash + respawn, release/source-map, redaction) or log each unrun item as a gap. |
| "Cost is the obvious priority, so instrument the expensive LLM calls first and skip the specialist investigation." | An obvious target does not waive the gate. The Cost/Latency and Privacy investigators must run first so cost fields and their sensitive surfaces are mapped before any provider call is wrapped. |
| "Attach `tenant_id` / `job_id` / `request_id` / `submission_id` / `checkout_session_id` as tags so we can correlate." | These are high-cardinality/correlation IDs. They may be attached only after the Privacy report maps each as a sensitive surface with an approved `safe_replacement` (hash/opaque id/count/category). |
| "Putting those IDs in event `extra`/`context` instead of tags avoids the cardinality rule." | Relocating an identifier does not sanitize it — `extra`, `context`, and span attributes carry the same leak. The sensitive-surface map governs every field regardless of slot. |
| "Pipe telemetry through the existing logger and rely on its sanitizer — the boundary already exists." | Reusing the logger is still provider wiring behind the gate, and a sanitizer is not a sensitive-surface map. Map surfaces and safe replacements first; attach submission/correlation IDs only in the approved form. |
| "Full dashboards and broad PII scrubbing are later polish, not part of finishing this." | Privacy filtering before capture is P0 and part of the completion contract; dashboards/alerts are recommended deliverables. Neither is optional polish — defer only as a logged gap. |

## Output Contract

On success, emit:

```json
{
  "ok": true,
  "provider": "sentry",
  "files_changed": [],
  "instrumented_surfaces": [],
  "critical_workflows_wrapped": [],
  "identity_fields": [],
  "privacy_filters": [],
  "verification_steps": [],
  "dashboards_or_alerts_recommended": [],
  "known_gaps": []
}
```

On failure, emit:

```json
{
  "ok": false,
  "code": "MISSING_DSN | UNSUPPORTED_STACK | PRIVACY_BLOCKER | TEST_FAILURE | PARTIAL_IMPLEMENTATION",
  "retryable": true,
  "user_message": "Explain what blocked completion.",
  "operator_detail": "Detailed technical reason.",
  "files_changed": [],
  "safe_next_step": "Concrete next action."
}
```

For user-facing closeout, use this shape:

```text
Implemented application observability tracking.

Provider:
- Sentry

Files changed:
- ...

Wrapped:
- app boot
- auth/profile fetch
- critical workflow X
- provider call Y
- background job Z

Identity:
- user.id attached after sign-in
- agent_id tag attached
- logout clears identity

Privacy:
- tokens redacted
- request bodies not sent
- raw prompts/transcripts not sent

Verification:
- lint passed
- typecheck passed
- tests passed
- smoke event verified
- release/environment visible
- stack trace readable

Known gaps:
- ...
```

## Common Mistakes

- Adding Sentry in several random files instead of one telemetry module.
- Capturing every caught exception or every click.
- Swallowing errors after capture.
- Sending raw prompts, transcripts, bodies, tokens, or customer records.
- Tagging with high-cardinality private values such as email, phone, full URL,
  request ID, prompt, transcript, or customer name.
- Enabling replay on sensitive screens before masking is designed and verified.
- Forgetting source maps, release metadata, child processes, workers, or logout
  identity clearing.
- Creating alerts that page on warnings instead of actionable symptoms.
- Calling telemetry complete without a real smoke event and readable stack.

## Core Question

Do not ask, "Where can I add Sentry?" Ask, "What does this application need to
explain when something goes wrong?"
