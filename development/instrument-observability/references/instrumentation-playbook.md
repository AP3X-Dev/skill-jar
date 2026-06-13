# Instrumentation playbook

Use this after the investigation gate passes. The goal is not to dump logs into
a provider; the goal is to make the app answer what broke, who was affected,
which workflow and step failed, which release caused it, which provider was
involved, how long it took, how many retries happened, what it cost, whether
sensitive data was protected, and how to reproduce it.

## Phase 1: Inspect the application

Before writing code, identify:

- framework and runtime
- frontend entry point
- backend entry point
- worker/engine entry point
- CLI entry point
- Electron main process, renderer process, and preload scripts if present
- auth system
- current logging system
- release/version source
- environment config system
- build system
- test command
- existing error handling
- existing observability provider
- sensitive data surfaces

Do not guess. Inspect package files, app entry points, config files, environment
docs, logging utilities, and existing provider code.

## Base module requirements

Add one centralized observability module. Preferred locations:

```text
src/observability.ts
src/telemetry.ts
src/lib/observability.ts
app/observability.py
server/observability.py
electron/observability.ts
```

The module must support:

- provider initialization
- environment
- release
- user identity
- tags
- breadcrumbs/log events
- spans/traces
- handled exception capture
- privacy filtering
- graceful no-op mode when DSN/config is absent

## What to wrap

### App lifecycle

Wrap app boot, config load, env validation, auth bootstrap, profile fetch,
database/cache connection, update check, shutdown, and cleanup.

Recommended names:

```text
app.boot
app.config.load
app.auth.bootstrap
app.profile.fetch
app.shutdown
app.cleanup
```

### Auth and identity

Wrap sign-in start, OAuth exchange, token refresh/rotation, profile fetch,
logout, and permission checks.

Attach safe identity after sign-in/profile fetch:

```json
{
  "id": "stable-user-id",
  "username": "agent-or-user-handle"
}
```

Avoid email unless policy allows it. Attach tags such as `agent_id`,
`account_id`, `org_id`, `role`, and `auth_state`. Never attach bearer tokens,
refresh tokens, cookies, OAuth codes, passwords, or raw auth headers.

### Critical user workflows

Find the workflows that define whether the app works and wrap their start,
major steps, success, expected failures, unexpected failures, timeout, retry,
and cancellation. Examples:

```text
checkout.start
checkout.payment_authorize
checkout.complete

call.start
call.audio_capture
call.transcription
call.form_generate
call.portal_submit
call.wrap_up

agent.invoke
agent.tool_call
agent.memory_retrieve
agent.provider_request
agent.finalize
```

Every critical workflow should have a top-level span.

### External dependencies

Wrap outside systems: HTTP APIs, model providers, payments, auth providers,
portal APIs, databases, queues, file storage, email/SMS, websockets, browser
automation, OCR, transcription, and audio services.

Attach safe attributes:

```text
provider
endpoint_category
status_code
retry_count
timeout_ms
rate_limited
```

Do not attach full request or response bodies by default.

### Expensive operations

Wrap operations that can burn time or money: LLM calls, embeddings,
transcription, OCR, video/audio processing, batch jobs, queue consumers, report
generation, scraper runs, browser automation, and long database queries.

Attach safe measurements:

```text
model
provider
input_tokens
output_tokens
total_tokens
estimated_cost_usd
duration_ms
retry_count
cache_hit
```

### Background jobs and workers

Wrap job received, started, lock acquired, timeout, retry, dead letter,
completed, and failed.

Attach:

```text
job_type
job_id_hash
queue_name
attempt
max_attempts
worker_id
```

Hash or omit job IDs if they contain sensitive data.

### UI actions

Use breadcrumbs, not errors, for important UI actions: screen opened, button
clicked, modal submitted, form validation failed, upload started/failed, user
retried, or user cancelled. Do not track every click.

### Electron surfaces

For Electron apps, instrument main process, renderer process, preload scripts,
IPC handlers, native crashes, auto updater, child process spawn, engine/worker
spawn, crash respawn, offline event cache, and window lifecycle.

Important names:

```text
electron.main.boot
electron.window.create
electron.ipc.handle
electron.child.spawn
electron.child.respawn
electron.auto_update
electron.native_crash
```

When a child process is spawned, pass only safe telemetry context:

```text
APP_RELEASE
APP_ENVIRONMENT
SENTRY_DSN
SENTRY_USER_JSON
SENTRY_TAGS_JSON
TRACE_PARENT
```

Never pass secrets unless required and approved.

## Naming and fields

Use stable names:

```text
app.boot
auth.profile_fetch
agent.invoke.stage1_fact
portal.submit
transcription.generate
form.validate
job.wrap_up
```

Recommended fields:

```text
workflow
stage
provider
model
release
environment
agent_id
account_id
org_id
job_type
attempt
status
error_category
```

Keep tag cardinality controlled. Good tags are stable categories such as
`workflow=portal.submit`, `stage=validate`, `provider=openai`,
`model=gpt-4.1-mini`, `environment=production`, and `release=1.4.2`.

Avoid high-cardinality/private tags such as raw prompt, full URL with query,
customer name, email, phone, transcript, request body, and response body.

## Privacy and safety

Never send:

- API keys
- auth tokens
- refresh tokens
- cookies
- passwords
- raw prompts
- raw model responses
- transcripts
- audio
- full customer records
- phone numbers
- full email addresses unless approved
- payment details
- medical/legal/private content
- full request bodies
- full response bodies
- screenshots of sensitive screens
- DOM replay from sensitive views

Use a provider filter such as `beforeSend`. Telemetry must never create a
larger security problem than the bug it helps debug.

## Identity attribution

Pin identity only after the app has a real signed-in identity. App boot with a
stored token may pin identity after profile fetch. Token refresh must not clear
identity. Logout clears identity. Child processes receive safe identity context
when needed. Malformed identity context is ignored, not fatal. Anonymous mode is
allowed when identity is unavailable.

Safe identity:

```json
{
  "id": "stable-portal-user-id",
  "username": "agent-tag"
}
```

Optional only when allowed:

```json
{
  "email": "user@example.com"
}
```

## Release and source maps

Every production telemetry event should include:

```text
release
environment
commit_sha
build_number
platform
runtime
```

For JavaScript, TypeScript, frontend, and Electron apps, upload source maps
during build, associate them with the release, verify minified stack traces map
to source files, test a production-like build, and test Electron main and
renderer processes separately.

Do not mark implementation complete until production-like stack traces are
readable, or list source-map verification as a known gap.

## Metrics

Track counts, gauges, and distributions that answer frequency, failure rate,
latency, affected user/agent/release/provider, and cost:

```text
workflow.started
workflow.completed
workflow.failed
provider.rate_limited
provider.timeout
agent.tokens.total
agent.cost.estimated
queue.depth
job.duration
```

## Alerts

Create alerts only for actionable signals:

```text
new production issue
resolved issue regressed
error rate spike
crash-free sessions dropped
startup failure spike
auth/profile fetch failure spike
critical workflow failure spike
portal submission failure spike
provider timeout spike
provider rate limit spike
agent cost spike
token usage spike
p95 latency regression
```

Avoid alerts for every warning, expected validation failures, normal user
cancellation, debug events, and known noisy browser extension errors.

Every alert should answer who is impacted, what workflow broke, what release
introduced it, whether it is urgent, and what runbook applies.

## Dashboards to recommend

### Application Health

Track crash-free users/sessions, errors by release and environment, startup
failures, p95 startup time, and p95 critical workflow duration.

### Workflow Reliability

Track workflow started/completed/failed, failure rate by workflow and stage,
retry count by provider, and timeout count by provider.

### Agent Cost and Usage

Track token usage by agent/stage, estimated cost by agent/model, failures by
model, retries by model, latency by provider, and cost per successful workflow.

### Release Regression

Track new issues, regressed issues, error rate by release, p95 latency by
release, failed workflows by release, and affected users by release.

## Tests to add

Add focused tests for:

- telemetry module initializes with DSN
- telemetry module no-ops without DSN
- privacy redaction removes secrets
- malformed user JSON does not crash
- logout clears identity
- token refresh does not clear identity
- wrapper rethrows original error
- wrapper records handled exception
- wrapper records success span
- wrapper records failure span
- source-map upload command exists, when applicable
- Electron child process receives safe telemetry env, when applicable

Recommended names:

```text
observability.init.test.ts
observability.privacy.test.ts
observability.identity.test.ts
observability.wrapper.test.ts
observability.electron.test.ts
```

## Smoke checklist

Implementation is not complete until the relevant smoke checks run:

- manual handled exception
- manual unhandled exception in dev
- critical workflow success
- critical workflow failure
- external API timeout
- auth/profile fetch success
- auth/profile fetch failure
- logout identity clear
- release appears correctly
- environment appears correctly
- privacy filter redacts secrets

For Electron:

- main process error
- renderer process error
- IPC handler error
- child process error
- child process crash and respawn
- native crash, if supported
- offline event cache, if relevant

For agent apps:

- agent invocation trace
- tool call span
- model/provider span
- token/cost fields attached
- agent_id attached
- stage attached
- retry attached
- failure attached

Expected result:

- events arrive in provider
- release is correct
- environment is correct
- user/agent attribution is correct
- sensitive data is redacted
- stack traces are readable
- workflow spans are searchable
- dashboards can segment by workflow, stage, release, provider, and agent
