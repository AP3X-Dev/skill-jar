# Sentry patterns

Use these patterns when the provider decision selects Sentry. Adapt imports and
API names to the app's language/runtime.

## Required initialization

Always set:

```text
dsn
environment
release
tracesSampleRate or tracesSampler
beforeSend
```

Set when applicable:

```text
replaysSessionSampleRate
replaysOnErrorSampleRate
profilesSampleRate
integrations
debug
sendDefaultPii
```

Default privacy stance:

```text
sendDefaultPii: false
```

Only enable PII intentionally.

## Privacy filter

```ts
const DENY_KEYS = [
  "authorization",
  "cookie",
  "set-cookie",
  "token",
  "access_token",
  "refresh_token",
  "password",
  "secret",
  "api_key",
  "openai_api_key",
  "transcript",
  "audio",
  "ssn",
  "credit_card"
];

function redactValue(key: string, value: unknown): unknown {
  const normalized = key.toLowerCase();

  if (DENY_KEYS.some(blocked => normalized.includes(blocked))) {
    return "[REDACTED]";
  }

  return value;
}

export function safeTelemetryData(
  input: Record<string, unknown>
): Record<string, unknown> {
  return Object.fromEntries(
    Object.entries(input).map(([key, value]) => [key, redactValue(key, value)])
  );
}
```

## Initialization example

```ts
import * as Sentry from "@sentry/node";

import { safeTelemetryData } from "./observability";

export function initObservability(): void {
  const dsn = process.env.SENTRY_DSN;

  if (!dsn) {
    return;
  }

  Sentry.init({
    dsn,
    environment: process.env.APP_ENV ?? "development",
    release: process.env.APP_RELEASE,
    sendDefaultPii: false,
    tracesSampleRate: process.env.APP_ENV === "production" ? 0.1 : 1.0,
    beforeSend(event) {
      if (event.request?.headers) {
        event.request.headers = safeTelemetryData(
          event.request.headers
        ) as Record<string, string>;
      }

      if (event.extra) {
        event.extra = safeTelemetryData(event.extra);
      }

      return event;
    }
  });
}
```

## Handled exception

Use for caught errors that affect users, block workflows, indicate dependency
failure, or should appear in issue triage. Do not capture expected validation
failures already represented as normal app state.

```ts
try {
  await submitPortalForm(payload);
} catch (error) {
  Sentry.captureException(error, {
    tags: {
      workflow: "portal.submit",
      provider: "portal"
    },
    extra: {
      retry_count: retryCount,
      status_code: getStatusCode(error)
    }
  });

  throw error;
}
```

## Breadcrumb

Use breadcrumbs for workflow checkpoints, user actions, retry attempts,
dependency calls, state transitions, and fallback paths.

```ts
Sentry.addBreadcrumb({
  category: "workflow",
  message: "portal.submit.started",
  level: "info",
  data: {
    workflow: "portal.submit",
    attempt: attemptNumber
  }
});
```

Do not put secrets or raw customer data in breadcrumb data.

## Span or trace

Use spans around full workflows, external API calls, model calls, database
calls, file operations, slow computations, background jobs, and startup phases.

```ts
return await Sentry.startSpan(
  {
    name: "portal.submit",
    op: "workflow.portal",
    attributes: {
      workflow: "portal.submit",
      agent_id: agentId,
      release: appRelease
    }
  },
  async span => {
    span.setAttribute("attempt", attemptNumber);

    const result = await submitPortalForm(payload);

    span.setAttribute("result", "success");
    return result;
  }
);
```

## Safe wrapper utility

Prefer a reusable wrapper over repeated ad hoc code.

```ts
type TelemetryContext = {
  workflow: string;
  stage?: string;
  userId?: string;
  agentId?: string;
  provider?: string;
  tags?: Record<string, string>;
  extra?: Record<string, unknown>;
};

export async function withTelemetry<T>(
  name: string,
  context: TelemetryContext,
  fn: () => Promise<T>
): Promise<T> {
  Sentry.addBreadcrumb({
    category: "workflow",
    message: `${name}.started`,
    level: "info",
    data: safeTelemetryData(context)
  });

  return await Sentry.startSpan(
    {
      name,
      op: context.workflow,
      attributes: safeTelemetryData({
        workflow: context.workflow,
        stage: context.stage,
        agent_id: context.agentId,
        provider: context.provider,
        ...context.tags
      })
    },
    async span => {
      try {
        const result = await fn();

        span.setAttribute("result", "success");

        Sentry.addBreadcrumb({
          category: "workflow",
          message: `${name}.success`,
          level: "info",
          data: safeTelemetryData(context)
        });

        return result;
      } catch (error) {
        span.setAttribute("result", "error");

        Sentry.captureException(error, {
          tags: {
            workflow: context.workflow,
            stage: context.stage ?? "unknown",
            provider: context.provider ?? "unknown",
            ...context.tags
          },
          extra: safeTelemetryData(context.extra ?? {})
        });

        throw error;
      }
    }
  );
}
```

The wrapper must preserve original behavior, rethrow original errors unless the
existing code intentionally swallows them, never convert failures into false
success, redact unsafe fields, and keep telemetry failures from breaking the
app.

## Metrics

Use metrics for counts, gauges, and distributions:

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

Metrics should answer how often something happens, how often it fails, whether
it is getting slower, and which user, agent, release, model, or provider caused
the change.
