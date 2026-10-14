# 0004 - References: project analysis heuristics and report template

## Goal
Give the skill the knowledge for Phase 1 (stack and architecture detection) and the fixed format for the Phase 2 report.

## Scope
- In: `code-smells-project/.claude/skills/refactor-arch/references/project-analysis.md` and `references/report-template.md`.
- Out: anti-pattern catalog (0005), architecture guidelines and playbook (0006).

## Requirements
- R1: `project-analysis.md` SHALL give detection heuristics, by manifest and import signals, for at least: Python (Flask, Django, FastAPI), Node.js (Express, NestJS, Fastify), plus a generic fallback for other stacks (Java/Spring, Go, PHP/Laravel, Ruby/Rails, C#/ASP.NET) by manifest file.
- R2: `project-analysis.md` SHALL describe how to detect the database (driver, ORM, connection string, in-memory vs file) and list tables (DDL, ORM models, migrations).
- R3: `project-analysis.md` SHALL describe how to classify the current architecture (monolith/god file, partial layering, layered MVC) and how to build the endpoint inventory (method, path, handler file:line) for Flask, Express and a generic case.
- R4: `project-analysis.md` SHALL describe how to infer the domain from table/entity/route names and how to count source files and lines (excluding dependencies, virtualenvs, build output and the skill folder).
- R5: `report-template.md` SHALL define the Phase 1 block and the Phase 2 report: header (project, stack, files, LOC), `## Summary` with counts per severity, `## Findings` with one `### [SEVERITY] Title` per finding with `File:`, `Description:`, `Impact:`, `Recommendation:` fields, and a footer with the total; plus the closing confirmation question.
- R6: `report-template.md` SHALL state the ordering (CRITICAL → LOW, then by file), the line-reference format (`path:line` or `path:start-end`, paths relative to the project root) and that descriptions are in Brazilian Portuguese while headings/labels stay in English.
- R7: `report-template.md` SHALL define the Phase 3 completion block (new structure tree, validation checklist with `✓`/`✗`, baseline vs after table per endpoint).

## Acceptance criteria
- [x] AC1: `project-analysis.md` names the manifests/imports for each stack in R1 and has sections for database, architecture, endpoint inventory, domain and file counting. (R1–R4)
- [x] AC2: `report-template.md` contains a full example report with the fields of R5, the rules of R6 and the Phase 3 block of R7. (R5–R7)

## Unit tests
- T1: `tests/test_skill_structure.py` — `report-template.md` contains `## Summary`, `## Findings`, `File:`, `Description:`, `Impact:`, `Recommendation:` and the confirmation question (AC2).
- T2: `tests/test_skill_structure.py` — `project-analysis.md` mentions `requirements.txt`, `package.json`, `pom.xml`, `go.mod`, `composer.json`, `Gemfile` and `.csproj` (AC1).
