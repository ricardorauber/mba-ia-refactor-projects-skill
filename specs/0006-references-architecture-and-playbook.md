# 0006 - References: MVC architecture guidelines and refactoring playbook

## Goal
Define the target MVC architecture and the concrete transformations Phase 3 applies, with before/after code for each anti-pattern.

## Scope
- In: `code-smells-project/.claude/skills/refactor-arch/references/mvc-guidelines.md` and `references/refactoring-playbook.md`.
- Out: running the refactoring (0007–0009).

## Requirements
- R1: `mvc-guidelines.md` SHALL define the target layers and their responsibilities: config (settings from environment with safe defaults, no secrets in code), models (data access and domain rules, no HTTP), views/routes (HTTP mapping only: path, method, request parsing, response serialization), controllers (application flow: orchestrate models/services, no SQL, no framework globals beyond the request DTO), optional services for side effects (notifications, payment) and middlewares (centralized error handling, auth guard), and the composition root / entry point.
- R2: `mvc-guidelines.md` SHALL give the target directory layout for Python/Flask and Node.js/Express and a generic mapping for other stacks, plus allowed dependency directions between layers.
- R3: `mvc-guidelines.md` SHALL define the behavior-preservation rules of ADR 0004: keep every route, method and status code; keep the original default port but read `PORT` from the environment; only remove sensitive fields from responses; keep dangerous admin routes behind an admin token from the environment; keep seed data and seed logins working.
- R4: `mvc-guidelines.md` SHALL tell the agent how to adapt to a partially layered project (keep useful existing layers, add the missing ones, move misplaced logic) versus a monolith (split by domain).
- R5: `refactoring-playbook.md` SHALL contain at least 14 patterns (`PB-NN`), each with: anti-patterns it fixes, steps, and before/after code; at least 8 SHALL have both Python and JavaScript before/after examples.
- R6: The playbook SHALL cover every anti-pattern ID in the catalog, including deprecated-API replacement, parameterized queries, extracting config, password hashing with a migration path for seed data, N+1 → join/eager load, centralized error handler, admin-token guard, and the smoke-test template for Python and Node.js.

## Acceptance criteria
- [ ] AC1: `mvc-guidelines.md` has sections for each layer in R1, the layouts in R2, the rules in R3 and the adaptation guidance in R4. (R1–R4)
- [ ] AC2: The playbook has ≥14 `PB-NN` patterns, each with `Before` and `After` code blocks, ≥8 with both Python and JavaScript. (R5)
- [ ] AC3: Every `AP-NN` in the catalog is referenced by at least one `PB-NN`. (R6)

## Unit tests
- T1: `tests/test_skill_structure.py` — count `### PB-NN` headings ≥14 and each has a `Before` and an `After` fenced block (AC2).
- T2: `tests/test_skill_structure.py` — ≥8 patterns contain both a ```` ```python ```` and a ```` ```js ```` / ```` ```javascript ```` block (AC2).
- T3: `tests/test_skill_structure.py` — set of `AP-NN` referenced in the playbook ⊇ set of `AP-NN` defined in the catalog (AC3).
- T4: `tests/test_skill_structure.py` — `mvc-guidelines.md` contains headings for Config, Models, Views, Controllers, Middlewares and Composition root (AC1).
