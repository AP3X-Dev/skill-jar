# Policy schema

The bundled validator accepts JSON and JSON-compatible YAML with standard-library
Python. Conventional YAML is accepted only when PyYAML is already installed.
The scaffold uses JSON-compatible YAML so it adds no dependency.

## Policy

`.architecture/policy.yaml`:

```json
{
  "version": 1,
  "project": "example-app",
  "rules": [
    {
      "id": "TENANCY-001",
      "statement": "Customer-owned records carry the active tenant identifier.",
      "state": "enforced",
      "severity": "error",
      "scope": {
        "include": ["src/models/**/*.py"],
        "exclude": ["src/models/system.py"]
      },
      "evidence": [
        {
          "type": "source",
          "locator": "src/tenant/context.py",
          "note": "Current tenant context and model convention."
        },
        {
          "type": "human",
          "locator": "ARCH-DECISION-012",
          "note": "Architecture owner approved the exact scope."
        }
      ],
      "provenance": {
        "discovered_at": "2026-08-29T18:00:00Z",
        "source_commit": "0123456789abcdef",
        "sources": ["repository", "runtime"]
      },
      "approval": {
        "decision_id": "ARCH-DECISION-012",
        "approved_by": "architecture-owner",
        "approved_at": "2026-08-29T19:00:00Z"
      },
      "validator": {
        "command": [
          "python",
          "scripts/architecture/validators/TENANCY-001/validator.py",
          "--root",
          "{fixture}",
          "--rule-id",
          "{rule_id}"
        ],
        "output_format": "guardrail-findings-v1",
        "entrypoint": "scripts/architecture/validators/TENANCY-001/validator.py",
        "implementation_root": "scripts/architecture/validators/TENANCY-001",
        "fixtures": {
          "positive": ["scripts/architecture/fixtures/TENANCY-001/valid"],
          "negative": ["scripts/architecture/fixtures/TENANCY-001/invalid"]
        }
      },
      "remediation": "Add the tenant identifier and populate it through the approved context.",
      "exception_ids": [],
      "routing": {
        "kind": "tenancy-boundary",
        "owner": "architecture-owner"
      }
    }
  ]
}
```

States are a progression, not interchangeable labels. `approved` and `enforced`
require the `approval` object. `enforced` additionally requires severity `error`,
a command expressed as an argv list, at least one positive and one negative
fixture, a dedicated implementation root, `guardrail-findings-v1` output,
deterministic routing, and remediation. The command must scan
`{fixture}` so fixture tests cannot accidentally rescan the repository. Commands
containing baseline-update modes are invalid.

Every source/evidence/fixture/implementation-root/baseline/exception path is checked
with cross-platform semantics and must remain beneath the repository without a
symlink or Windows junction ancestor. Windows device names, drive-relative paths, alternate data
streams, trailing dots/spaces, controls, traversal, absolute paths, UNC paths,
and ambiguous duplicate mapping keys are invalid.

Evidence types are `source`, `test`, `runtime`, `document`, `history`, `memory`,
and `human`. `verified` or later needs at least one current `source`, `test`, or
`runtime` item. Memory and documentation alone cannot verify a rule.

## Baseline

`.architecture/baseline.json` records exact approved legacy debt:

```json
{
  "version": 1,
  "source_commit": "0123456789abcdef",
  "entries": [
    {
      "fingerprint": "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
      "rule_id": "TENANCY-001",
      "path": "src/models/legacy.py",
      "reason": "Existing model scheduled for migration.",
      "decision_id": "ARCH-DECISION-013",
      "approved_by": "architecture-owner",
      "approved_at": "2026-08-29T19:30:00Z"
    }
  ]
}
```

No path wildcards, directory exemptions, counts, or automatic refresh. A copied,
moved, or changed violation must produce a different fingerprint and fail.

## Exceptions

`.architecture/exceptions.yaml` is also JSON-compatible YAML:

```json
{
  "version": 1,
  "exceptions": [
    {
      "id": "EXC-001",
      "rule_id": "TENANCY-001",
      "target": {
        "path": "src/integrations/vendor_webhook.py",
        "symbol": "handle_vendor_event",
        "fingerprint": "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
      },
      "reason": "Vendor payload has no tenant until account resolution.",
      "owner": "integrations-team",
      "decision_id": "ARCH-DECISION-014",
      "approved_by": "architecture-owner",
      "approved_at": "2026-08-29T20:00:00Z",
      "expires_at": "2026-11-01T00:00:00Z",
      "removal_condition": "Vendor account mapping migration completes."
    }
  ]
}
```

Targets require an exact path, symbol, and finding fingerprint and may not
contain glob metacharacters. A path-only waiver is invalid because it could
suppress multiple findings in one file. Every exception must
carry approval plus an expiry or concrete removal condition. Inline suppressions
that are not represented here are violations.

## Decisions and independent verification

`.architecture/decisions.json` is the machine-readable approval ledger. Each
approved rule, baseline entry, and exception references one decision whose
`subject_type`, exact subject ID, canonical subject SHA-256, approver, and time
match the pack bytes. A non-empty approval-looking string is not enough.

```json
{
  "version": 1,
  "decisions": [{
    "id": "ARCH-DECISION-012",
    "status": "approved",
    "subject_type": "rule",
    "subject_id": "TENANCY-001",
    "subject_sha256": "sha256:<canonical rule contract hash>",
    "approved_by": "architecture-owner",
    "approved_at": "2026-08-29T19:00:00Z"
  }]
}
```

`.architecture/verification.json` binds each enforced rule to its decision,
canonical policy and validator hashes, the canonical command, and three distinct
maker/breaker/verifier identities. The final verifier reruns the command after
the record is applied.

```json
{
  "version": 1,
  "records": [{
    "rule_id": "TENANCY-001",
    "decision_id": "ARCH-DECISION-012",
    "verdict": "pass",
    "maker": "policy-maker-run-7",
    "breaker": "breaker-run-8",
    "verifier": "verifier-run-9",
    "verified_at": "2026-08-29T21:00:00Z",
    "canonical_command": ["python", "scripts/architecture/verify.py"],
    "policy_sha256": "sha256:<canonical policy hash>",
    "validator_sha256": "sha256:<canonical validator contract hash>",
    "artifacts_sha256": "sha256:<implementation plus fixture bytes hash>"
  }]
}
```

These records make approval, distinct canonical role IDs, validator source, and
fixture bytes machine-linked and reviewable. They do not cryptographically
authenticate a human or agent identity. Use protected reviews or signed
approvals when the target threat model requires that stronger guarantee, and
record it as hosted evidence. Never claim local strings prove identity.
Role IDs use one canonical alphanumeric-hyphen form and are compared after
punctuation normalization, so aliases such as `same-agent`, `same_agent`, and
`same.agent` cannot masquerade as three checkers.

## Validation

Run:

```text
python scripts/architecture/validate_policy.py --root . --policy .architecture/policy.yaml --baseline .architecture/baseline.json --exceptions .architecture/exceptions.yaml --decisions .architecture/decisions.json --verification .architecture/verification.json
```

Exit `0` means the pack is structurally valid. Exit `2` means configuration,
schema, reference, or approval provenance is invalid. This check does not execute
project validators or declare the architecture correct.
