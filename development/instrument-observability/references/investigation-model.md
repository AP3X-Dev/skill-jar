# Investigation model

Before adding Sentry, OpenTelemetry, Datadog, or another provider, run a
specialist investigation. Use real subagents when the host supports them. If it
does not, emulate them as separate read-only passes with isolated prompts,
separate notes, and separate findings.

No instrumentation code may be added until the reports are complete and merged.

## Questions to answer

- What are the critical workflows?
- Where do failures hurt the user?
- Where do failures cost money?
- Where does identity become known?
- Where do external systems get called?
- Where do background jobs or child processes run?
- Where can sensitive data leak into telemetry?
- Where will traces, breadcrumbs, tags, errors, and metrics provide the most
  debugging value?

## Required investigators

### Architecture Mapper

Find app entry points, frontend/backend entry points, Electron main/renderer,
preload scripts, worker processes, background jobs, CLI entry points, shared
libraries, config files, and build/release files.

Return:

```json
{
  "entry_points": [],
  "runtime_surfaces": [],
  "process_boundaries": [],
  "config_sources": [],
  "likely_telemetry_init_location": "",
  "notes": []
}
```

### Critical Workflow Mapper

Find workflows that define whether the app works: sign-in, profile fetch, app
boot, onboarding, payment, submission, call/session, form generation,
model/agent invocation, save/export, sync, upload/download, and job completion.

Return:

```json
{
  "critical_workflows": [
    {
      "name": "",
      "files": [],
      "steps": [],
      "success_signal": "",
      "failure_signal": "",
      "user_impact": "low | medium | high | critical",
      "recommended_tracking": ["span", "breadcrumb", "error", "metric", "tag"]
    }
  ]
}
```

### Failure Surface Investigator

Find unhandled exceptions, swallowed exceptions, bare catch blocks, retry loops,
timeouts, fallback paths, network errors, validation/parsing failures, startup
failures, shutdown failures, and cleanup failures.

Return:

```json
{
  "failure_surfaces": [
    {
      "name": "",
      "files": [],
      "failure_mode": "",
      "current_handling": "",
      "risk": "low | medium | high | critical",
      "recommended_wrapper": "captureException | span | breadcrumb | metric"
    }
  ]
}
```

### External Dependency Mapper

Find HTTP clients, SDK clients, model providers, databases, queues, portal/API
calls, auth providers, payment providers, storage, websocket connections,
browser automation, transcription/OCR/audio services, and email/SMS providers.

Return:

```json
{
  "external_dependencies": [
    {
      "provider": "",
      "files": [],
      "operation": "",
      "timeout_behavior": "",
      "retry_behavior": "",
      "recommended_tracking": ["span", "metric", "breadcrumb", "error"],
      "safe_tags": [],
      "unsafe_fields": []
    }
  ]
}
```

### Cost and Latency Investigator

Find operations that can burn time or money: LLM calls, embeddings,
transcription, OCR, report generation, batch jobs, browser automation, expensive
database queries, large file processing, paid API loops, and retries.

Return:

```json
{
  "cost_latency_hotspots": [
    {
      "name": "",
      "files": [],
      "cost_driver": "tokens | API calls | compute | retries | duration | unknown",
      "latency_risk": "low | medium | high | critical",
      "cost_risk": "low | medium | high | critical",
      "measurements_to_attach": []
    }
  ]
}
```

### Identity and Attribution Investigator

Find login success, OAuth exchange, stored-token boot, profile fetch, session
restore, role lookup, account/org selection, agent profile lookup, and logout.

Return:

```json
{
  "identity_moments": [
    {
      "name": "",
      "files": [],
      "identity_fields_available": [],
      "safe_identity_fields": [],
      "unsafe_identity_fields": [],
      "recommended_set_user_location": "",
      "recommended_clear_user_location": ""
    }
  ]
}
```

Rules: set identity only after a real signed-in identity exists; token refresh
must not clear identity; logout must clear identity; safe identity context may
cross child-process boundaries; malformed identity payloads are ignored.

### Privacy and Data Safety Investigator

Find auth tokens, cookies, passwords, API keys, raw prompts, raw model
responses, transcripts, audio, customer records, phone numbers, emails, payment
data, request/response bodies, screenshots, and session replay surfaces.

Return:

```json
{
  "sensitive_surfaces": [
    {
      "name": "",
      "files": [],
      "sensitive_fields": [],
      "redaction_required": true,
      "safe_replacement": "hash | id | count | category | omitted"
    }
  ],
  "recommended_before_send_filters": [],
  "session_replay_policy": ""
}
```

### Runtime and Process Boundary Investigator

Required for Electron, desktop apps, agent engines, workers, and child
processes. Find Electron main/renderer/preload, IPC handlers, child process
spawn, engine spawn, worker processes, crash respawn logic, queue consumers, and
daemon/service entry points.

Return:

```json
{
  "process_boundaries": [
    {
      "name": "",
      "files": [],
      "context_risk": "low | medium | high | critical",
      "required_env_or_headers": [],
      "recommended_tracking": [],
      "respawn_behavior": ""
    }
  ]
}
```

## Optional investigators

- **UI Interaction Investigator:** important button clicks, form submissions,
  validation failures, navigation, modals, retry/cancel paths.
- **Release and Build Investigator:** version source, release name, commit SHA,
  build number, source-map build, source-map upload, CI/CD release step.
- **Alert and Dashboard Investigator:** alerts, dashboards, ownership,
  workflow-health views, cost views, and release-regression views.

## Merge the reports

Merge findings into one plan. Keep the individual reports separate, then rank
candidate tracking targets with this model:

```text
priority =
  user_impact
  + failure_likelihood
  + cost_risk
  + latency_risk
  + debugging_value
  + release_regression_value
  - privacy_risk
  - implementation_complexity
```

Classify every candidate:

- **P0:** must instrument before production.
- **P1:** high value, should instrument now.
- **P2:** useful after core flows.
- **P3:** optional or noisy.
- **Do not instrument:** too noisy, too risky, or low value.

Use this merged plan format:

```json
{
  "provider": "sentry",
  "summary": "",
  "p0_tracking_targets": [
    {
      "name": "",
      "reason": "",
      "files": [],
      "wrap_type": ["span", "breadcrumb", "error", "metric", "tag"],
      "safe_tags": [],
      "safe_extra": [],
      "privacy_notes": [],
      "verification": []
    }
  ],
  "p1_tracking_targets": [],
  "p2_tracking_targets": [],
  "do_not_track": [
    {
      "name": "",
      "reason": ""
    }
  ],
  "implementation_order": [],
  "tests_required": [],
  "known_gaps": []
}
```

The orchestrator must prefer critical workflows over broad logging, privacy
filters before capture, reusable wrappers over provider calls scattered through
the app, identity only after it is known, and verified smoke checks over claims.
