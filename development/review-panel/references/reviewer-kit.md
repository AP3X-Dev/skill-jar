# Reviewer kit

Bundled lens templates, the verify-before-act protocol, and the optional FUGAZI/MemBerry mappings for [review-panel](../SKILL.md). Self-contained — adapt `<placeholders>` to the repo.

## Review package template

Return this package after synthesis and verification. A raw reviewer transcript is not enough.

```md
# Review Panel: <branch-or-pr>

## Diff Under Review
- **Base:** <BASE_SHA>
- **Head:** <HEAD_SHA>
- **Scope note:** <files/areas intentionally included or excluded>

## Lens Results
| Lens | Findings returned | Notes |
|------|-------------------|-------|
| Correctness | <count> | <short summary> |
| Security | <count> | <short summary> |
| Simplicity / reuse | <count> | <short summary> |

## Verified Findings
| Severity | File:line | Claim | Verification evidence | Action |
|----------|-----------|-------|-----------------------|--------|

## Refuted Findings
| File:line | Claim | Refutation evidence |
|-----------|-------|---------------------|

## Gate Evidence
- **Review gate:** <commands or checks run, with exit/result>
- **Fix gate:** <commands proving Critical/Important fixes, if any>
```

## Lens templates (dispatch one per lens, in parallel)

Each reviewer gets: the diff (`git diff <BASE>...<HEAD>`), read access to the repo, and its lens prompt. Each returns findings as `severity | file:line | claim | why it matters | suggested direction`.

### Correctness lens

```md
You review ONLY for correctness. Diff under review: <BASE>...<HEAD>.
Hunt: logic errors, off-by-one, wrong/missing edge cases, error paths that
swallow or mis-handle failures, data-flow mistakes, race conditions, broken
invariants. For each finding give file:line, the concrete input/sequence that
triggers it, and the wrong result. Ignore style and security — other reviewers
own those. A finding without a triggering case is a hypothesis; mark it as such.
Return: findings (severity | file:line | claim | trigger | impact), or "none".
```

### Security lens

```md
You review ONLY for security. Diff under review: <BASE>...<HEAD>.
Hunt: missing authz/authn checks, injection (SQL/shell/path/template), secrets
in code, unsafe deserialization, missing input validation at trust boundaries,
SSRF, unsafe defaults, dependency risk introduced by the diff. For each finding:
file:line, the attack/abuse path, and the blast radius. Default to flagging when
unsure — a security maybe is worth a human look. Return: findings or "none".
```

### Simplicity / reuse lens

```md
You review ONLY for simplicity and reuse. Diff under review: <BASE>...<HEAD>.

Walk each new/changed piece of code down this ladder and stop at the first rung
that holds — the rung it *skipped* is the finding:
  1. does this need to exist at all? (speculative / unused → delete)
  2. already in this repo? (a helper/util/type/pattern → reuse it; cite the symbol)
  3. does the stdlib do it?
  4. does a native platform feature cover it? (<input type="date"> over a picker
     lib, a DB constraint over app code, CSS over JS)
  5. does an already-installed dependency solve it? (don't add a new dep for a
     few lines)
  6. can it be one line?
  7. only then: the minimum code that works.

Tag each finding, one line — `<tag> <what to cut>. <replacement>. file:line`:
  - `delete:` dead code, unused flexibility, speculative feature. Replacement: nothing.
  - `stdlib:` hand-rolled thing the standard library ships. Name the function.
  - `native:` dependency or code doing what the platform already does. Name the feature.
  - `yagni:` abstraction with one implementation, config nobody sets, layer with one caller.
  - `shrink:` same logic, fewer lines. Show the shorter form.

Prefer "delete this and call <existing>" over any new abstraction. Do NOT demand
more abstraction, and never flag a single smoke test / assert-based self-check as
bloat. A deliberate shortcut whose comment already names its ceiling and upgrade
path is intent, not a finding — leave it unless that named ceiling is now being
hit. Return: findings (severity | file:line | tag | claim | first rung skipped
or existing symbol to reuse) or "none". End with `net: -<N> lines possible.`
```

### Synthesizer

```md
You merge three lens reports (below) into ONE ranked list.
<paste correctness / security / simplicity findings>
- Dedupe: collapse findings that are the same issue seen from two lenses.
- Rank each: Critical (prod-breaking correctness/security) | Important (real,
  not a blocker) | Minor (style/preference).
- Add NOTHING the reviewers didn't raise.
Return: the single ranked list, each entry tagged with its origin lens.
```

## Verify-before-act protocol

The author runs this on **every** synthesized finding before touching code:

1. **Restate** the finding in your own words. If you can't, ask the reviewer (or re-read) — don't guess.
2. **Reproduce against the codebase.** Trace the actual path: does the edge case reach this line? Is the "duplicate" truly equivalent (read both)? Does the security path actually reach untrusted input? Run the code or the test if cheap.
3. **Verdict:**
   - *Verified* → act (fix Critical/Important now, each as its own small diff; note Minor).
   - *Refuted* → record a one-line reason and do NOT implement it. Pushing back with evidence is correct; performative agreement ("great catch!") followed by a needless change is the failure mode this prevents.
4. **Conflicts:** if two lenses disagree (refactor vs leave-as-is), the author decides with reasoning and records why.

Never reply "you're absolutely right" and implement before step 2.

## FUGAZI pre-pass → lens routing (optional)

Run read-only on the changed files; route each finding `kind` to the lens that owns it. Every routed finding still goes through the verify protocol.

| FUGAZI kind | Route to | Reviewer reads it as |
|---|---|---|
| `unused-exports` / `unused-files` / dead param | Simplicity | Did the diff orphan code, or add an unused export? |
| `code-duplication` / `duplicate-exports` | Simplicity | Reintroduced a clone instead of reusing |
| `boundary-violations` | Correctness (+ Security if a trust seam) | Crossed an architectural seam |
| `circular-dependencies` | Correctness | Added a load-order/init hazard |
| `complexity-hotspot` / `cognitive-complexity` | Correctness | The changed function most likely to hide a bug — read it line by line |
| `unresolved-imports` / `unlisted-dependencies` | Correctness | The diff references something unresolved |

Keep it read-only — review-panel never runs `fugazi fix`.

## MemBerry false-positive schema (optional)

Store a refuted finding so it doesn't re-surface as noise:

```
berry_store(
  session_id: "<session>",
  task: "[project:<tag>] review false-positive",
  content: "FINDING: <what was flagged> | WHY FALSE: <the durable reason —
            reflection-loaded, deliberate separation, framework entrypoint> |
            LOCATION PATTERN: <file/symbol pattern it recurs at>",
  outcome: "approved"
)
```

Load with `berry_load(task: "code review: <area>", tags: ["project:<tag>"])` at step 2. Treat returned false-positives as **de-prioritization hints**, never as a reason to skip the verify protocol on a fresh finding.
