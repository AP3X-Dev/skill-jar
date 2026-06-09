# PRP Template (Product Requirements Plan)

Use this template to write a PRP that the autonomous advisor can execute against. The more specific and complete the PRP, the better the advisor's decisions.

---

```markdown
# [Project Name] — Product Requirements Plan

## Goal

What are we building and why? One paragraph.

## Scope

### In Scope
- [Feature/deliverable 1]
- [Feature/deliverable 2]
- ...

### Out of Scope
- [Explicitly excluded thing 1]
- [Explicitly excluded thing 2]
- ...

## Requirements

### Functional Requirements

#### [Feature Area 1]
- FR-1: [Specific, testable requirement]
- FR-2: [Specific, testable requirement]
- ...

#### [Feature Area 2]
- FR-3: [Specific, testable requirement]
- ...

### Non-Functional Requirements
- NFR-1: [Performance, security, accessibility, etc.]
- NFR-2: ...

## Constraints

### Tech Stack
- Language: [e.g., TypeScript]
- Framework: [e.g., Next.js 14]
- Database: [e.g., PostgreSQL with Prisma]
- Other: [testing framework, styling, etc.]

### Patterns to Follow
- [e.g., "Follow existing controller/service/model pattern"]
- [e.g., "Use Zod for validation at API boundaries"]

### Patterns to Avoid
- [e.g., "No ORMs other than Prisma"]
- [e.g., "No class-based components"]

## Success Criteria

How do we know this is done? Be specific:
- [ ] [Criterion 1 — testable/observable]
- [ ] [Criterion 2 — testable/observable]
- ...

## Architecture Preferences (optional)

Any strong opinions about how the system should be structured:
- [e.g., "Prefer thin controllers, business logic in services"]
- [e.g., "One file per component, co-locate tests"]

## Prior Art / References (optional)

Existing code, docs, or examples to follow:
- [e.g., "See src/controllers/auth.ts for the pattern to follow"]
- [e.g., "API should match the OpenAPI spec at docs/api.yaml"]

## Open Questions (optional)

Things you're unsure about — the advisor will make judgment calls on these:
- [e.g., "Not sure whether to use server actions or API routes for mutations"]
- [e.g., "Pagination: offset vs cursor?"]

Note: The advisor will choose based on project context and engineering judgment. If you have a strong preference, move it to Constraints instead.
```

---

## Tips for Writing Good PRPs

**Be specific about requirements.** "Add user auth" is vague. "Add email/password auth with JWT, bcrypt hashing, login/register/logout endpoints, and protected route middleware" gives the advisor what it needs.

**Explicitly exclude scope.** The advisor won't add things not in the PRP, but being explicit about what's OUT prevents ambiguity at the edges.

**State constraints, not implementations.** Say "must work with PostgreSQL" not "use a JOIN on the users table." Let the design phase figure out the how.

**List success criteria you can verify.** "Works well" isn't criteria. "All endpoints return correct status codes, validation errors return 400 with field-level messages, auth middleware rejects expired tokens" is criteria.

**Use the Open Questions section.** It's better to acknowledge uncertainty than to leave a gap the advisor has to guess about. Open questions get engineering judgment; gaps get nothing.
