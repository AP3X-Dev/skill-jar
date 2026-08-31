# Managed architecture guardrail instructions -- __PROJECT__

Review and merge this section into the repository's applicable `AGENTS.md` and
host instructions. Do not overwrite existing instruction files automatically.

- Run `python scripts/architecture/verify.py` before claiming architecture
  compliance.
- Only rules with state `enforced` are blocking. Observed, documented, and
  verified candidates are not approved policy.
- Architecture policy, baseline, exception, validator, fixture, hook, or CI
  changes require a checker who did not author the change.
- Approved/enforced rules bind to `.architecture/decisions.json`; enforced rules
  also bind distinct maker, breaker, and verifier identities plus policy and
  validator contract, implementation, and fixture hashes in
  `.architecture/verification.json`.
- Never add wildcard or directory-wide baseline/exception entries.
- The canonical verifier is read-only. Baseline updates are separate,
  human-approved changes.
- Conflicting architecture evidence becomes a decision item; do not infer intent
  from the most common code pattern.
- `watch_guardrail.py` must be explicitly initialized from an approved clean
  handoff. Its cursor classifies findings but never suppresses them.
