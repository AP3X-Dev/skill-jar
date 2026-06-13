---
name: instrument-observability
description: "Adds production-grade application observability instrumentation with Sentry by default: error tracking, crash reporting, tracing, release health, workflow breadcrumbs, user/agent attribution, privacy filtering, cost/usage tracking, and real-runtime verification. Use when adding Sentry, telemetry, tracking, monitoring, crash reporting, performance tracing, session replay, workflow failure monitoring, agent cost/usage monitoring, frontend/backend correlation, Electron crash capture, or production debugging; use existing OpenTelemetry, Datadog, New Relic, Honeycomb, LogRocket, Highlight, or structured-log standards only when the repo or user requires them."
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
- Preserve behavior. Telemetry failures must not break the app; captured errors
  must be rethrown unless existing code intentionally swallows them.
- Do not claim production-ready telemetry until real runtime smoke events
  arrive with correct release, environment, attribution, readable stacks, and
  redaction verified.

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

No instrumentation code may be added before this is produced:

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
