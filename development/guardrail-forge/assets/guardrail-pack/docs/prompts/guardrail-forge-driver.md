# Guardrail Forge -- one finite bootstrap cycle

Run exactly one narrow cycle, then stop.

1. Recover `agent-state/architecture-guardrail/loop-state.md` and applicable repo
   instructions. Confirm the base commit and current autonomy level.
2. At Level 1, perform one read-only discovery lane and update evidence/decision
   state only. Do not install enforcement.
3. At Level 2+, choose one human-approved rule. The policy maker implements it in
   the isolated worktree with positive and negative fixtures.
4. A separate breaker attempts bypasses; a separate verifier runs
   `python scripts/architecture/verify.py`, the target repo gates, and the scope
   check. Either may reject.
5. Record pass/reject and exact command output in the verification ledger. Record
   failed attempts without deleting history.
6. Update loop state before any local commit. Commit pack and state together only
   on a real pass. Never push or merge.

Stop on conflicting architecture evidence, missing approval, incomplete scan,
unproven negative fixture, self-verification, gate weakening, or public/security/
schema/on-disk contract change.
