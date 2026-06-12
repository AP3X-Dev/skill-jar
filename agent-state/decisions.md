# Decisions -- jar-audit

> Choices made and their rationale (the file-based fallback for what MemBerry
> would otherwise remember). Enrich from references/state-templates.md.

| Decision | Rationale | Cycle |
|----------|-----------|-------|
| Hook declarations live in role files and generated agent packs | Keeps hook behavior attached to the agent roles that produce evidence while `skill-forge` remains the only path that edits skills | hook-runtime-drop-in |
