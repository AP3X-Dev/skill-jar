# Reviewer kit

Bundled lens templates, the verify-before-act protocol, and the optional FUGAZI/MemBerry mappings for [review-panel](../SKILL.md). Self-contained — adapt `<placeholders>` to the repo.

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
Hunt: code that reimplements something already in this repo (search for it and
cite the existing symbol), dead or speculative abstraction, over-engineering,
YAGNI, needless indirection. Prefer "delete this and call <existing>" findings.
Do NOT demand more abstraction. Return: findings (with the existing symbol to
reuse where applicable) or "none".
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

## Verify-before-act protocol (receiving-code-review discipline)

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
