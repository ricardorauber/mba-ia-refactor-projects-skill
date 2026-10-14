# 0003 - Run the skill on each project with the headless Claude Code CLI

- Date: 2026-10-14
- Spec: 0001-repository-setup-and-conventions
- Status: accepted

## Context
The challenge requires invoking `/refactor-arch` inside each project and requires Phase 2 to stop and ask for confirmation before Phase 3. The runs must be reproducible and leave evidence (Phase 1 summary, Phase 2 report, Phase 3 validation) for the README and the reports.

## Options considered
- A: Headless CLI in two steps: `claude -p "/refactor-arch"` (Phases 1–2, ends at the confirmation question), then `claude -p --resume <session_id> "y"` (Phase 3) — real skill invocation, full logs, uses the user's Claude Code account.
- B: The user runs `claude "/refactor-arch"` interactively and answers `y` — faithful but manual and without structured logs.
- C: Follow SKILL.md by hand in the building session — does not actually invoke the skill.

## Decision
"Claude CLI headless" — option A, with model `claude-opus-5-5`, `--permission-mode acceptEdits --allowedTools Bash` ("acceptEdits + Bash liberado") and `--output-format stream-json --verbose`, so every intermediate assistant message is kept.

## Consequences
A runner script executes both steps from inside the project folder, stores the raw stream as `.jsonl` and a readable transcript in `reports/logs/`, and prints the session id used to resume. The confirmation gate is proven by the first step ending with the question and by `git status` showing no change between the steps.
