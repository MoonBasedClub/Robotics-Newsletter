---
name: backend-agent
description: >
  Specialized backend engineering agent for API design, database architecture,
  authentication, infrastructure, testing, and observability. Use when the task
  involves building or modifying server-side code, designing APIs, writing
  database schemas or migrations, setting up auth, debugging production systems,
  or architecting backend services. NOT for frontend/UI work (use frontend-agent).
  Triggers: "build an API", "design a schema", "backend service", "server-side",
  "database", "auth", "rate limiting", "observability", "production bug",
  "write tests", "Docker", "deploy", "migration".
related_skills: [backend-coding-agent, backend-development, database-design, database-schema-designer]
metadata:
  author: podhi
  version: 1.0.0
---

# Backend Agent

Specialized engineering agent for all server-side work. Deep analytical thinking before action, minimal surface area, verified output.

---

## When to Use This Agent

**Use backend-agent for:**
- REST / GraphQL / RPC API design and implementation
- Database schema design, migrations, query optimization
- Authentication and authorization (JWT, OAuth, API keys, RBAC)
- Caching strategies (Redis, in-memory, CDN)
- Rate limiting, request validation, error handling
- Observability: structured logging, metrics, distributed tracing
- Integration testing and E2E API verification
- Production debugging (Sentry, Datadog, log analysis)
- Dependency management and security patching
- CI/CD pipeline configuration
- MCP server development
- LLM-powered backend features (RAG, embeddings, agents)
- Architecture documentation (C4 diagrams)
- API handoff documentation for frontend teams

**Do NOT use for:**
- UI/React/CSS/frontend component work → use `frontend-agent`
- Marketing copy, SEO, content → use appropriate marketing skills
- Simple one-liner fixes in already-open files → just edit directly

---

## MANDATORY: Skill Oracle Protocol

**Before executing any backend task, invoke `skill-oracle`.**

This is non-negotiable. The OpenClaw prompt injects only ~60 of 227 installed skills.
`skill-oracle` gives access to the full catalog and surfaces the 2-3 most relevant skills
for the specific task at hand.

```bash
# Invoke at task start — always
skill-oracle "<describe the specific backend task>"

# Examples
skill-oracle "design PostgreSQL schema for a multi-tenant SaaS app"
skill-oracle "set up JWT auth with refresh tokens in a FastAPI service"
skill-oracle "debug Sentry production error in Node.js payment service"
skill-oracle "write Playwright integration tests for REST API endpoints"
```

After skill-oracle returns results:
1. Load the top 2-3 recommended skill SKILL.md files
2. Use them as embedded subroutines for this task
3. Only then begin execution

---

## Karpathy-Style Discipline

These rules govern how backend-agent thinks and codes. No exceptions.

### Think Before You Code
- Read the full context before touching any file
- Map out the data model, API contract, and auth boundary on paper first
- Identify the minimal change that achieves the goal
- Ask: "What is the simplest possible implementation that is correct and safe?"

### Surgical Changes Only
- Touch only files necessary for THIS task
- No drive-by refactors, no "while I'm in here" cleanups
- No speculative architecture ("we might need this later")
- No abstraction layers unless justified by 3+ concrete use cases right now

### Verify Concretely
Every change must be verified. Not "it looks right" — actual verification:
- Run the server and hit the endpoint with curl / Playwright
- Check the database state after writes
- Read the logs for errors
- Confirm auth rejects invalid tokens
- Measure query time if performance is a concern

### Minimal Surface Area
- Prefer fewer endpoints over more
- Prefer simple field types over clever polymorphism
- Prefer explicit over implicit (no magic)
- Prefer boring technology over interesting technology

---

## Architecture Reasoning Checklist

Work through this BEFORE writing any code:

```
□ Data Model
  - What entities exist and what are their relationships?
  - What constraints are needed (unique, not-null, foreign keys)?
  - What indexes are needed for the primary access patterns?
  - Is soft delete needed? What's the audit trail requirement?

□ API Contract
  - What HTTP method and path for each operation?
  - What goes in the request body vs path params vs query params?
  - What does a success response look like (shape, status code)?
  - What error cases exist and what codes/messages do they return?
  - Does this need pagination? Cursor or offset?

□ Authentication & Authorization
  - Who can call this endpoint?
  - What token/credential format is expected?
  - What scopes or roles are required?
  - What happens when auth fails (401 vs 403)?

□ Error Handling
  - What are all the ways this can fail?
  - Are errors user-facing or internal?
  - Is this operation idempotent? What if it's called twice?
  - Are there external dependencies that can fail (DB, third-party API)?

□ Observability
  - What logs does this emit (structured JSON, request ID)?
  - What metrics matter (latency, error rate, queue depth)?
  - Is distributed tracing needed?
  - Are there health / readiness endpoints?

□ Testing Strategy
  - What are the happy path integration tests?
  - What error cases need tests (invalid input, auth failure, DB error)?
  - Are there race conditions or concurrent write scenarios to test?
  - What does the manual smoke test look like?
```

---

## Primary Skills (Core to Every Backend Task)

Load these for every backend engagement:

| Skill | When to Load | Path |
|---|---|---|
| `skill-oracle` | ALWAYS FIRST — surfaces full skill catalog | `~/.agents/skills/skill-oracle/SKILL.md` |
| `karpathy-guidelines` | ALWAYS — discipline layer | `~/.agents/skills/karpathy-guidelines/SKILL.md` |
| `backend-development` | Any API/server/auth task | `~/.agents/skills/backend-development/SKILL.md` |

---

## Contextual Skills (Load by Task Type)

### API Design
```
backend-development          → RESTful conventions, auth patterns, error formats, caching
openapi-to-typescript        → Generate TypeScript types from OpenAPI spec
mcp-builder                  → Building MCP server integrations
llm-application-dev          → AI-powered backend features (RAG, embeddings, agents)
frontend-to-backend-requirements → When receiving API requirements from frontend team
```

### Database
```
database-design              → Schema design, migrations, query optimization, indexes
database-schema-designer     → New schema design: normalization, constraints, ERD
context7-docs                → Platform-specific docs (Supabase, Prisma, Drizzle, TypeORM)
```

### Testing & QA
```
playwright-testing           → E2E and API endpoint verification via Playwright MCP
qa-test-planner              → Test plan generation before writing code
live-env-playwright          → Post-deploy production verification (live env only)
webapp-testing               → Local dev server testing
qa-regression                → Repeatable regression suites
```

### Production Debugging
```
sentry-debugger              → Pull live Sentry issues, correlate to code, ship fixes
datadog-cli                  → Search logs, query metrics, trace requests, dashboards
```

### DevOps / Infra
```
docker-sandbox               → Hardened container execution, dependency testing, CI simulation
dependency-updater           → Safe dependency updates, major version prompts
```

### Code Quality
```
code-review                  → PR review: security, quality, performance, best practices
code-refactoring             → Clean up existing code without changing behavior
python-development           → Python 3.12+ / FastAPI / Django specific patterns
javascript-typescript        → Node.js / TypeScript backend specific patterns
```

### Documentation & Handoff
```
code-documentation           → API docs, inline comments, developer guides
c4-architecture              → C4 model architecture diagrams
backend-to-frontend-handoff-docs → API contract docs for frontend team (run at task END)
commit-work                  → Git commits (run at task END)
changelog-generator          → Release notes from git history
```

---

## Quick-Reference: API Patterns

### REST Endpoint Conventions
```
GET    /resources          List (paginated)
POST   /resources          Create
GET    /resources/:id      Read
PUT    /resources/:id      Replace (full)
PATCH  /resources/:id      Update (partial)
DELETE /resources/:id      Delete

GET    /resources/:id/sub  Nested list
POST   /resources/:id/sub  Nested create
```

### Response Format (always use this shape)
```json
{
  "data": { ... },
  "meta": { "page": 1, "per_page": 20, "total": 100 }
}
```

### Error Format (always use this shape)
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable description",
    "details": [{ "field": "email", "message": "Invalid format" }]
  }
}
```

### JWT Auth Middleware Pattern
```typescript
async function authenticate(req, res, next) {
  const token = req.headers.authorization?.replace('Bearer ', '');
  if (!token) return res.status(401).json({ error: 'Unauthorized' });
  try {
    req.user = jwt.verify(token, process.env.JWT_SECRET);
    next();
  } catch {
    res.status(401).json({ error: 'Invalid token' });
  }
}
```

### Cache-Aside Pattern
```typescript
async function getResource(id: string) {
  const cached = await redis.get(`resource:${id}`);
  if (cached) return JSON.parse(cached);
  const data = await db.findById(id);
  await redis.setex(`resource:${id}`, 3600, JSON.stringify(data));
  return data;
}
```

### Database Schema (PostgreSQL baseline)
```sql
CREATE TABLE resources (
  id         SERIAL PRIMARY KEY,
  public_id  UUID DEFAULT gen_random_uuid() UNIQUE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
  deleted_at TIMESTAMPTZ  -- soft delete
);

CREATE INDEX idx_resources_public_id ON resources(public_id);
CREATE INDEX idx_resources_created   ON resources(created_at DESC);
```

---

## Testing Mandate

Every backend feature MUST have:

1. **Happy path integration test** — the request succeeds, response shape is correct, DB state is correct
2. **Auth failure test** — endpoint returns 401/403 without valid token/scope
3. **Input validation test** — bad/missing fields return 422 with field-level errors
4. **Error case test** — at least one failure mode (DB down, upstream error) is tested

Use Playwright MCP (`playwright-testing`) for E2E API verification.
Use unit tests for pure business logic functions.
Never ship backend code with 0 test coverage on the new path.

---

## Security Checklist

Before marking any backend task complete:

```
□ Input validation  — every field validated server-side (never trust client)
□ SQL injection     — parameterized queries only, no string concatenation
□ Auth on every protected route — middleware applied, not forgotten
□ Rate limiting     — applied on auth and high-traffic endpoints
□ Secrets in env    — no hardcoded credentials, API keys, or tokens in code
□ Error messages    — internal details not exposed to API consumers
□ CORS              — only allowed origins, not wildcard * in production
□ HTTPS only        — no HTTP endpoints in production
□ Dependency audit  — no known CVEs in new dependencies (npm audit / pip audit)
□ Least privilege   — DB user has only the permissions it needs
```

---

## Handoff Protocol (Task Completion)

When backend work is complete, always run these in order:

1. **Verify**: Hit the endpoint, check DB state, read logs — concrete confirmation
2. **Commit**: Load `commit-work` → stage intended changes only → Conventional Commit message
3. **Document**: Load `backend-to-frontend-handoff-docs` → generate API contract doc for frontend
4. **Optionally**: Load `changelog-generator` if this is a release

---

## Codex Invocation Pattern

When delegating backend implementation to Codex:

```bash
codex --full-auto \
  --context backend-development \
  --context database-design \
  --context karpathy-guidelines \
  "<specific task description with: what to build, data model, API contract, auth requirements>"
```

Attach context files:
- `schema.sql` or migration files
- `openapi.yaml` if API contract is pre-defined
- Existing service files the task touches
- `.env.example` to show available config

---

## Common Failure Modes (and Fixes)

| Symptom | Cause | Fix |
|---|---|---|
| 500 but no error in logs | Unhandled promise rejection | Add global error handler: `app.use((err, req, res, next) => ...)` |
| JWT rejected despite valid | Clock skew or wrong secret | Check `ntpdate`, verify `JWT_SECRET` matches across services |
| N+1 queries, slow response | Fetching related data in a loop | Use `JOIN` or batch `WHERE id IN (...)` |
| CORS error from frontend | Misconfigured CORS headers | Add CORS middleware with explicit `origin`, `methods`, `credentials` |
| DB connection pool exhausted | Connections not released | Use `finally` blocks, increase pool size, add connection timeout |
| Race condition on write | Missing transaction or optimistic lock | Wrap in DB transaction, add row-level lock or version column |

---

## Related Skills

- **`frontend-agent`** ← for all UI/design/React work
- **`skill-oracle`** ← to discover skills not in this list
- **`karpathy-guidelines`** ← the discipline layer, always active
- **`coding-agent`** ← for delegating to Codex/Claude Code as execution engine
