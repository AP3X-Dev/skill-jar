# Validator contract

Every enforced rule has a project-specific validator. Prefer the strongest
existing layer that can express the invariant: compiler/type system, AST-aware
lint, dependency graph, runtime assertion, then a focused custom validator.
Regex or path scans are acceptable only when their supported syntax and blind
spots are explicit and fixture-tested.

## Command contract

The policy stores commands as argv lists; never shell strings. Each command has
the strict shape `runtime + exact entrypoint + arguments`. The entrypoint must be
the second argv token and live beneath one repo-contained `implementation_root`.
Every repository file or directory named anywhere in argv, including
standalone paths, `--option=path`, `--option:path`, compact `-Ipath`, and `@file`
forms (including composites such as `--option=@file`), must live beneath that
root. Response markers always require an existing bound path. Other terminal
arguments must be placeholders, existing bound paths, or simple literals made
only from letters, digits, `_`, `+`, and `-`. Missing paths, punctuation-bearing
values, delimited lists, and other encoded containers are invalid; use repeated
simple options or move the value into configuration beneath the bound root.
Long options consume only their first `=` or `:` delimiter, then any leading
response markers; the terminal payload is never reinterpreted as another option.
A compact short option consumes exactly its one-character option name and the
entire remaining payload; later suffixes are never searched for a usable path.
Every long-option assignment must have a non-empty terminal payload and an
option name matching `--[A-Za-z0-9][A-Za-z0-9_-]*`; path-like, empty, and
extra-hyphen prefixes are invalid rather than discarded.
The supported `-I` form is always path-bearing, so bare `-I` is invalid and
even a punctuation-free payload must already exist beneath
`implementation_root`. Existing lexical symlinks and junctions never fall back
to literals, even when their names contain no punctuation.
Inline and module execution forms are invalid.
The verifier recursively hashes every regular file and descendant directory
entry beneath the root, including NTFS named-stream bytes on Windows,
so imports and configuration cannot escape the authority binding merely because
they were omitted from a hand-maintained list. Placeholders must be standalone
argv values or exact `--option={placeholder}` values; composing paths such as
`{root}/helper.py` is invalid because it would name code outside the bound root.
Placeholders are
limited to `{root}`, `{rule_id}`, `{policy}`, `{baseline}`, `{exceptions}`, and
`{fixture}`. A rule validator must be read-only and deterministic. It reports
raw rule matches; the canonical verifier centrally applies exact committed
baseline and exception entries so every project receives identical waiver
semantics.

Project-validator exit codes:

- `0`: complete scan, no raw match.
- `1`: one or more raw matches. The canonical verifier may suppress an exact
  approved baseline occurrence or exception before deciding its own exit.
- `2`: invalid configuration, incomplete scan, missing dependency, unsupported
  syntax required by scope, or tool failure.

Output is one `guardrail-findings-v1` JSON object containing `rule_id`,
`complete: true`, and a `findings` list. Every finding names the same rule ID,
exact safe repo-relative path/symbol, `sha256:` fingerprint, message, and
remediation. Malformed, incomplete, unsafe-path, or exit/output-inconsistent
results are configuration failures, never passes.

The canonical command is:

```text
python scripts/architecture/verify.py
```

It validates policy/baseline/exceptions plus decisions and verification bindings,
rereads and recursively hashes each validator implementation root and every fixture,
runs every positive fixture expecting `0` with no findings, runs every negative
fixture expecting `1` with a finding, then runs each enforced rule against the
repository. Zero enforced rules exits `2`; Level 1 schema-only work uses
`--policy-only`. Hook and CI wrappers invoke the exact default command and may
not use a semantic subset. The verifier has no write-baseline mode.

For an approved `arch-drift-watch` handoff, `--repo-only --format json` uses the
same policy and validator engine while omitting fixture repetition. It emits
`guardrail-verification-v1` with complete status, authority digest, rules run,
exact findings, routing kind, and owner. Its authority digest includes the
current validator/fixture artifact hashes. It is not a weaker policy mode.

## Fixture and canary rules

For every enforced rule:

- Positive fixture: representative valid code exits `0`.
- Negative fixture: representative violation exits `1` and identifies the rule.
- Parser/extractor failure: exits `2`, never a false pass.
- Approved exact exception: passes; a nearby unapproved case fails.
- Exact baseline occurrence: suppressed as debt; copied/moved/changed occurrence
  fails; stale entries fail when the project enables stale-baseline enforcement.

Capture a RED result before remediation with validator bytes/configuration
frozen. Re-run the same bytes for GREEN. If the validator changes, restart the
proof with independent fixtures or a negative-control mutation. Do not treat a
combined application+validator green diff as canary evidence.

## Breaker gauntlet

The breaker attempts:

- Alias or rename a forbidden import.
- Re-export through a barrel or sanctioned directory.
- Introduce an alternate API/procedure/adapter layer.
- Hide a side effect behind a nominal query/read operation.
- Move code into an excluded directory or unsupported extension.
- Add an inline suppression or disable directive.
- Add an overly broad exception or baseline path.
- Copy a baselined violation elsewhere.
- Delete/rename the validator, fixture, hook, or workflow.
- Make a missing/empty/erroring scan appear green.
- Modify validator and application code in the same proof packet.

The verifier rejects any bypass, duplicate JSON keys, uncovered in-scope syntax, weakened existing
gate, unexplained scope change, or self-verification. Validator/policy changes
must be reviewed by a checker who did not author them.

## Tamper boundary

Application changes should not be able to weaken the rule that evaluates them.
The verification ledger binds the complete implementation-root tree and fixture
bytes, so editing either without a fresh independent record is a configuration
failure. Keep every custom import, helper, parser, query, and validator config
beneath that root; an independent checker must reject a validator that loads
project-controlled executable content from elsewhere.
The canonical verifier also recomputes policy, baseline, exception, decision,
verification, validator, fixture, and canonical-tool authority after running all
commands. A validator that mutates those inputs can never return green. Full
filesystem write isolation still belongs to an OS/container sandbox when the
target threat model requires it. The canonical verifier establishes deterministic
policy enforcement, not a security sandbox for an intentionally malicious
already-approved validator or a compromised language runtime; those remain
trusted-code and environment boundaries requiring independent review and, where
needed, OS-enforced read-only execution.
Where the host supports path protection or required reviews, require independent
review for `.architecture/**`, `scripts/architecture/**`, hook, and architecture
workflow changes. CI configuration cannot enforce its own branch-protection rule,
so record that external repository setting as hosted evidence, not local proof.
