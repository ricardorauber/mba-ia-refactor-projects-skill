# 0002 - Manual analysis of the three projects

## Goal
Document, before writing the skill, the problems found by reading the three legacy projects, so the skill's catalog is grounded on real findings.

## Scope
- In: section "Análise Manual" of the root `README.md` (Brazilian Portuguese), replacing the challenge statement that currently fills the README (the statement stays reachable through a link to the upstream repository).
- Out: sections "Construção da Skill", "Resultados" and "Como Executar" (0010). Any code change.

## Requirements
- R1: The section SHALL have one subsection per project (`code-smells-project`, `ecommerce-api-legacy`, `task-manager-api`), each with a table: severity, problem, file:line(s), justification (why it matters).
- R2: Each project SHALL list at least 5 problems, including at least 1 CRITICAL or HIGH, at least 2 MEDIUM and at least 2 LOW, using the severity scale of the challenge (CRITICAL, HIGH, MEDIUM, LOW).
- R3: Every file:line reference SHALL point to the original upstream code (commit `6d1ce62`) and be exact.
- R4: Rows SHALL be ordered CRITICAL → HIGH → MEDIUM → LOW within each project.
- R5: The section SHALL mark which problems are deprecated-API usages, when any exist.

## Acceptance criteria
- [ ] AC1: `README.md` has a `## Análise Manual` heading with three project subsections and tables with the four columns in R1. (R1)
- [ ] AC2: Each table has ≥5 rows with ≥1 CRITICAL/HIGH, ≥2 MEDIUM and ≥2 LOW, ordered by severity. (R2, R4)
- [ ] AC3: Spot-checking every row against `git show 6d1ce62:<file>` confirms the cited lines contain the described problem. (R3)
- [ ] AC4: At least one row (in `task-manager-api`) is marked as deprecated API. (R5)

## Unit tests
- T1: `tests/test_readme.py` — parses the `## Análise Manual` section; for each project subsection asserts ≥5 rows, the severity minimums in R2 and CRITICAL→LOW ordering (AC2).
