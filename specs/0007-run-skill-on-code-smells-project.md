# 0007 - Run the skill on code-smells-project (Python/Flask)

## Goal
Prove the skill on the unstructured Flask e-commerce monolith: correct analysis, an audit with real findings, and an MVC refactor that keeps every endpoint responding.

## Scope
- In: `code-smells-project/` (refactored code produced by Phase 3), `reports/audit-project-1.md`, `reports/logs/project-1-*`, `tests/test_reports.py`, `scripts/run_skill.sh` (the headless runner of ADR 0003, reused by 0008 and 0009), iterations on the reference files when a criterion fails.
- Out: the other two projects.

## Requirements
- R1: `scripts/run_skill.sh <project-dir> <phase12|phase3>` SHALL run the headless commands of ADR 0003, save the raw stream to `reports/logs/project-N-<phase>.jsonl`, save a readable transcript (assistant text messages in order) to `reports/logs/project-N-<phase>.md`, and print the session id needed by `phase3`.
- R2: The Phase 1 output SHALL detect Python, Flask 3.1.1, flask-cors, SQLite with tables `produtos`, `usuarios`, `pedidos`, `itens_pedido`, the e-commerce domain, a monolithic architecture and 4 source files.
- R3: The Phase 2 report SHALL follow the template, have ≥5 findings with ≥1 CRITICAL or HIGH, findings ordered by severity, exact file:line references, and SHALL contain at least 5 of the problems of this project listed in the manual analysis.
- R4: The run SHALL stop after Phase 2 with the confirmation question and SHALL NOT have changed any file (verified with `git status` between the two runs).
- R5: `reports/audit-project-1.md` SHALL contain the Phase 2 report as printed by the skill (Phase 1 block included at the top for context), without edits other than trimming text outside the two blocks.
- R6: After Phase 3, the project SHALL have an MVC layout (config, models, views/routes, controllers, centralized error handling, clear entry point), boot without errors with `PORT=<free port> python app.py` (or the entry point the skill documents), and every original endpoint SHALL answer with the same status code as the baseline for the same request, except where ADR 0004 allows a change (admin routes without token).
- R7: The generated smoke test SHALL pass when run against the refactored app.
- R8: IF any criterion fails, THEN the reference files (not the project code by hand) SHALL be adjusted and the skill re-run from a clean checkout of the project (`git checkout -- code-smells-project && git clean -fd code-smells-project`, keeping the skill), up to 4 iterations; each iteration and its cause SHALL be recorded for the README.

## Acceptance criteria
- [ ] AC1: `reports/logs/project-1-phase12.jsonl` and `project-1-phase3.jsonl` exist and come from `claude-opus-5-5`. (R1)
- [ ] AC2: The Phase 1 block matches R2. (R2)
- [ ] AC3: `reports/audit-project-1.md` passes the report checks and ≥5 of its findings map to manual-analysis rows of project 1. (R3, R5)
- [ ] AC4: `git status --porcelain code-smells-project` is empty right after the phase12 run. (R4)
- [ ] AC5: The refactored tree has config, models, views or routes, controllers and middleware folders/modules and a single entry point; `grep -rn "minha-chave-super-secreta-123"` finds nothing in code. (R6)
- [ ] AC6: Running the smoke test against the refactored app on a free port exits 0; the Phase 3 log shows the baseline vs after comparison with no unexpected difference. (R6, R7)

## Unit tests
- T1: `tests/test_reports.py` — for each existing `reports/audit-project-*.md`: has `## Summary` and `## Findings`; ≥5 `### [SEVERITY]` findings; ≥1 CRITICAL or HIGH; severities non-increasing in order; every finding has a `File:` line matching `path:\d+(-\d+)?`; summary counts equal the counted findings (AC3).
- T2: `tests/test_reports.py` — every `File:` path in `audit-project-1.md` exists in `git show 6d1ce62` for `code-smells-project/` and its line numbers are within that file's length (AC3).
