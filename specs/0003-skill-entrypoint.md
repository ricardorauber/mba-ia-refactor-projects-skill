# 0003 - Skill entry point: SKILL.md with the three phases

## Goal
Create the `refactor-arch` Claude Code skill entry point that drives Analysis, Audit (with a mandatory confirmation gate) and MVC Refactoring with validation, delegating domain knowledge to reference files.

## Scope
- In: `code-smells-project/.claude/skills/refactor-arch/SKILL.md`.
- Out: the content of the reference files (0004–0006), running the skill (0007–0009).

## Requirements
- R1: SKILL.md SHALL have YAML frontmatter with `name: refactor-arch` and a `description` stating what it does (analyze, audit, refactor to MVC, validate) and when to use it; it SHALL be written in English.
- R2: SKILL.md SHALL define three sequential phases and SHALL tell the agent which reference file to read at each phase (progressive disclosure), naming them by relative path under `references/`.
- R3: Phase 1 SHALL detect language, framework (with version from the manifest), dependencies, database and tables, domain, current architecture, source file count and the inventory of HTTP endpoints, and SHALL print the `PHASE 1: PROJECT ANALYSIS` block in the format of the challenge example.
- R4: Phase 2 SHALL cross the code with the anti-pattern catalog, and SHALL print the report exactly in the template format, with exact `file:line` or `file:start-end` per finding, findings sorted CRITICAL → LOW, and a severity summary.
- R5: WHEN Phase 2 finishes, the skill SHALL end its turn with the question `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]` and SHALL NOT create, modify or delete any file (including the report) before an explicit affirmative answer; on a negative answer it SHALL stop.
- R6: Phase 3 SHALL, in order: boot the original app on a free port and record the status code of every inventoried endpoint (baseline); refactor following the architecture guidelines and the playbook; create a smoke test in the project's own language with no new dependencies (`tests/smoke_test.py` for Python, `tests/smoke.test.js` run by `node --test` for Node.js) that boots the app and calls every original endpoint; boot the refactored app, run the smoke test and compare against the baseline; re-check the catalog on the new code.
- R7: WHEN validation fails, the skill SHALL fix and re-validate (bounded to 3 attempts) and SHALL report any remaining failure instead of claiming success.
- R8: Phase 3 SHALL end by printing the `PHASE 3: REFACTORING COMPLETE` block with the new project structure tree and the validation checklist (`✓`/`✗`), as in the challenge example.
- R9: SKILL.md SHALL be technology-agnostic: no project names, file names or table names of the three target projects; stack-specific details only appear as examples or in the references.
- R10: SKILL.md SHALL stay under 500 lines.

## Acceptance criteria
- [ ] AC1: The frontmatter parses as YAML with `name == "refactor-arch"` and a non-empty `description`. (R1)
- [ ] AC2: SKILL.md contains the headings for Phase 1, 2 and 3 and references every file under `references/` by relative path. (R2)
- [ ] AC3: SKILL.md contains the exact confirmation sentence of R5 and an explicit rule forbidding file changes before an affirmative answer. (R5)
- [ ] AC4: SKILL.md contains the baseline → refactor → smoke test → compare steps and the 3-attempt bound. (R6, R7)
- [ ] AC5: SKILL.md does not contain `produtos`, `AppManager`, `loja.db`, `tasks.db`, `code-smells-project`, `ecommerce-api-legacy` or `task-manager-api`; it has fewer than 500 lines. (R9, R10)

## Unit tests
- T1: `tests/test_skill_structure.py` — frontmatter name/description (AC1).
- T2: `tests/test_skill_structure.py` — every `references/*.md` path mentioned in SKILL.md exists, and every file in `references/` is mentioned (AC2).
- T3: `tests/test_skill_structure.py` — confirmation sentence present (AC3).
- T4: `tests/test_skill_structure.py` — forbidden project-specific tokens absent and line count < 500 (AC5).
