# 0001 - Repository setup and conventions

## Goal
Prepare the fork so the skill, the reports and the validation tests can be built and checked from the repository root, and record the project conventions as ADRs.

## Scope
- In: root `.gitignore`, `requirements-dev.txt`, `pytest.ini`, `tests/` scaffold, `reports/` and `reports/logs/` folders, `adrs/0001`–`adrs/0004`.
- Out: skill files (0003–0006), manual analysis (0002), skill runs (0007–0009), README sections B–D (0010). Any change to the three projects' source code outside a skill run.

## Requirements
- R1: The root `.gitignore` SHALL keep every entry it ships with and SHALL also ignore `.claude/settings.local.json`, `.pytest_cache/` and `*.log` outside `reports/logs/`; `.claude/skills/` SHALL NOT be ignored.
- R2: `requirements-dev.txt` SHALL pin `pytest` and nothing else; `pytest.ini` SHALL make `pytest` run from the repository root and collect only `tests/`.
- R3: `reports/` and `reports/logs/` SHALL exist in git (with a `.gitkeep` until real files land).
- R4: The repository SHALL contain `adrs/0001-user-facing-text-in-brazilian-portuguese.md`, `adrs/0002-fast-forward-default-branch-after-each-spec.md`, `adrs/0003-run-the-skill-with-headless-claude-cli.md` and `adrs/0004-security-fixes-may-change-response-bodies.md`, in the format of the ADRs of the previous challenges (Date, Spec, Status, Context, Options considered, Decision, Consequences).
- R5: ADR 0001 SHALL state: README in Brazilian Portuguese; skill files (SKILL.md and references), specs, ADRs, code and commits in English; audit reports with English headings/labels (as in the challenge example) and Brazilian Portuguese descriptions.
- R6: ADR 0003 SHALL state: each project is run with `claude -p "/refactor-arch"` (Phases 1–2, stops at the confirmation) and then resumed with `--resume <session_id> "y"` (Phase 3), using model `claude-opus-5-5`, `--permission-mode acceptEdits --allowedTools Bash`, and `--output-format stream-json --verbose` so every intermediate message is kept as evidence.
- R7: ADR 0004 SHALL state: routes, methods and status codes of every original endpoint are preserved; response bodies may change only to remove sensitive data (passwords, secret keys) and passwords become real hashes while seed logins keep working; dangerous admin routes stay but require an admin token read from an environment variable; the HTTP port becomes configurable through `PORT` keeping the original default, because ports 5000 and 3000 are taken on this machine.

## Acceptance criteria
- [ ] AC1: `git check-ignore .claude/settings.local.json` succeeds and `git check-ignore code-smells-project/.claude/skills/refactor-arch/SKILL.md` fails; original `.gitignore` entries are still present. (R1)
- [ ] AC2: In a fresh venv, `pip install -r requirements-dev.txt && pytest` from the repo root exits 0 (no tests or only passing tests collected). (R2)
- [ ] AC3: `git ls-files reports` lists `reports/.gitkeep` and `reports/logs/.gitkeep`. (R3)
- [ ] AC4: The four ADR files exist with all seven fields and the decisions in R5–R7. (R4–R7)

## Unit tests
- T1: none — configuration and documentation only; verified by AC1–AC4.
