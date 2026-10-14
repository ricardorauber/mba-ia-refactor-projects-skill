# 0008 - Run the skill on ecommerce-api-legacy (Node.js/Express)

## Goal
Prove the same skill works unchanged on a different stack: the Express LMS API with checkout.

## Scope
- In: copy of `code-smells-project/.claude/skills/refactor-arch/` into `ecommerce-api-legacy/.claude/skills/refactor-arch/`, refactored `ecommerce-api-legacy/`, `reports/audit-project-2.md`, `reports/logs/project-2-*`.
- Out: the other two projects except keeping the skill copies identical.

## Requirements
- R1: The skill copy SHALL be byte-identical to the project 1 copy; any reference change made during iterations SHALL be applied to every copy.
- R2: The Phase 1 output SHALL detect JavaScript/Node.js, Express 4.x, sqlite3, in-memory SQLite with tables `users`, `courses`, `enrollments`, `payments`, `audit_logs`, the LMS/checkout domain, a god-class architecture and 3 source files.
- R3: The Phase 2 report SHALL meet the same rules as 0007 R3–R5, saved to `reports/audit-project-2.md`, with ≥5 of the manual-analysis problems of this project.
- R4: After Phase 3, the app SHALL boot with `PORT=<free port> npm start`, and `POST /api/checkout` (approved and denied card), `GET /api/admin/financial-report` and `DELETE /api/users/:id` SHALL answer with the baseline status codes (except as ADR 0004 allows), and the financial report SHALL keep returning the same data for the seed.
- R5: The generated `tests/smoke.test.js` SHALL pass with `node --test` and add no dependency to `package.json`.
- R6: Iteration rule of 0007 R8 applies.

## Acceptance criteria
- [ ] AC1: `diff -r code-smells-project/.claude/skills/refactor-arch ecommerce-api-legacy/.claude/skills/refactor-arch` is empty. (R1)
- [ ] AC2: The Phase 1 block matches R2. (R2)
- [ ] AC3: `reports/audit-project-2.md` passes the report checks and maps ≥5 findings to manual-analysis rows. (R3)
- [ ] AC4: The refactored app boots, the smoke test passes and the Phase 3 log shows no unexpected status-code difference; `grep -rn "pk_live_1234567890abcdef\|senha_super_secreta_prod_123"` finds nothing in code. (R4, R5)
- [ ] AC5: `package.json` dependencies are unchanged or only gain packages justified in the Phase 3 output. (R5)

## Unit tests
- T1: `tests/test_skill_structure.py` — every `*/.claude/skills/refactor-arch` copy present in the repo is identical to the project 1 copy (AC1).
- T2: `tests/test_reports.py` already covers `audit-project-2.md` (AC3); add T2 of 0007 for project 2 paths.
