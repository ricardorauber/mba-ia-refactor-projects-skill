# 0009 - Run the skill on task-manager-api (Python/Flask, partially layered)

## Goal
Prove the skill adapts to a project that already has some layering: it must still find problems and improve the structure without breaking any endpoint.

## Scope
- In: skill copy into `task-manager-api/.claude/skills/refactor-arch/`, refactored `task-manager-api/`, `reports/audit-project-3.md`, `reports/logs/project-3-*`.
- Out: the other two projects except keeping the skill copies identical.

## Requirements
- R1: The skill copy SHALL be byte-identical to the other copies.
- R2: The Phase 1 output SHALL detect Python, Flask 3.0.0, Flask-SQLAlchemy, SQLite file database with tables `users`, `categories`, `tasks`, the Task Manager domain, a partially layered architecture (models/routes/services/utils) and the real number of source files (14 `.py` files including `__init__.py`, or the count the skill's documented rule produces, stated in the block).
- R3: The Phase 2 report SHALL meet the rules of 0007 R3–R5, saved to `reports/audit-project-3.md`, and SHALL include at least one deprecated-API finding (`Query.get()` or `datetime.utcnow()`).
- R4: After Phase 3, `python seed.py` SHALL still populate the database and seed logins (e.g. `joao@email.com` / `1234`) SHALL still succeed; the app SHALL boot with `PORT=<free port>`; every endpoint of `routes/` and `app.py` SHALL answer with the baseline status code; the layering SHALL gain controllers (or equivalent) and centralized error handling while reusing the existing models.
- R5: The generated smoke test SHALL pass.
- R6: Iteration rule of 0007 R8 applies.

## Acceptance criteria
- [ ] AC1: The three skill copies are identical. (R1)
- [ ] AC2: The Phase 1 block matches R2. (R2)
- [ ] AC3: `reports/audit-project-3.md` passes the report checks, maps ≥5 findings to manual-analysis rows and has a deprecated-API finding. (R3)
- [ ] AC4: Seed + boot + smoke test pass; login with a seed user returns 200; no `Query.get(` or `utcnow(` remains in the refactored code. (R4, R5)

## Unit tests
- T1: covered by `tests/test_skill_structure.py` T1 of 0008 and `tests/test_reports.py` (AC1, AC3).
- T2: `tests/test_reports.py` — `audit-project-3.md` contains at least one finding whose title or description mentions "deprecated" (AC3).
