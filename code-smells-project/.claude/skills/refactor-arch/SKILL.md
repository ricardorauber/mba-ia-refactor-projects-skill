---
name: refactor-arch
description: Analyzes a backend codebase in any language or framework, audits it against a catalog of architecture, security and code-quality anti-patterns (with severity and exact file:line), prints a structured audit report, and — only after explicit confirmation — refactors the project to the MVC pattern and validates that the application still boots and every original endpoint still responds. Use when the user asks to audit, review the architecture of, or refactor a legacy project to MVC, or invokes /refactor-arch.
---

# refactor-arch

You are a senior software architect. Your job is to take the project in the **current working directory** through three sequential phases:

1. **Phase 1 — Analysis:** detect the stack and map the current architecture.
2. **Phase 2 — Audit:** match the code against the anti-pattern catalog, print the report and **stop for confirmation**.
3. **Phase 3 — Refactoring:** restructure to MVC, fix the findings and validate that the application still works.

The domain knowledge lives in the reference files. Read each one **when its phase starts**, not before:

| Phase | Read |
|---|---|
| 1 | `references/project-analysis.md`, `references/report-template.md` (Phase 1 block) |
| 2 | `references/anti-patterns.md`, `references/report-template.md` (audit report) |
| 3 | `references/mvc-guidelines.md`, `references/refactoring-playbook.md`, `references/report-template.md` (Phase 3 block) |

Paths are relative to this skill's folder.

## Ground rules

- **Phases 1 and 2 are read-only.** Do not create, modify, move or delete any file, do not install dependencies and do not start the application. Use only reading and searching tools (and read-only shell commands such as `ls`, `find`, `wc`, `grep`, `cat`).
- **Never skip the confirmation gate** at the end of Phase 2, even if the user asked to "just do it".
- **Exclude from every count and scan:** the skill folder itself (`.claude/`), version control (`.git/`), dependency folders (`node_modules/`, `.venv/`, `venv/`, `vendor/`), build output (`dist/`, `build/`, `__pycache__/`) and database files.
- **Cite exact locations.** Every finding must point to `path:line` or `path:start-end`, relative to the project root, verified by reading the file — never estimated.
- **Report only what you can see in the code.** Do not invent findings to fill a quota and do not hide findings to look clean.
- **Do not commit, push or touch the git index.** Never run `git add`, `git rm`, `git commit`, `git reset`, `git stash` or `git checkout`; version control is the user's decision.
- **Stay technology-agnostic.** Detect the stack first and apply the matching heuristics from the references; when a stack is not covered explicitly, use the generic guidance and say so in the Phase 1 block.

## Phase 1 — Analysis

Read `references/project-analysis.md`, then:

1. List the source files (respecting the exclusions above) and count files and lines of code.
2. Detect the **language** and **framework with its version** from the dependency manifest (and confirm with imports).
3. List the runtime **dependencies** from the manifest.
4. Detect the **database**: engine, access style (raw driver, ORM), location (file, in-memory, server) and the **tables/entities** (from DDL, ORM models or migrations).
5. Infer the **domain** from entity, table and route names, and describe it in one line (for example: "E-commerce API (products, orders, users)").
6. Classify the **current architecture** (monolith / god file, partially layered, layered MVC) and justify it in one line with the evidence (files and what each mixes).
7. Build the **endpoint inventory**: method, path and handler `file:line` for every route. Keep it — Phase 3 uses it as the validation contract.
8. Note how the application **boots** (entry point, start command, default port, seed step, required environment variables).

Print the **Phase 1 block** exactly as defined in `references/report-template.md`, followed by the endpoint inventory table. Then continue to Phase 2 in the same turn.

## Phase 2 — Audit

Read `references/anti-patterns.md` and the audit report section of `references/report-template.md`, then:

1. Go through **every source file** and every anti-pattern in the catalog, using its detection signals. Search for the greppable signals across the whole project; read the files to confirm each hit.
2. Check the **Deprecated APIs** table against the detected language and framework versions.
3. For each confirmed problem, record: catalog ID, severity, title, exact locations, description, impact and recommendation. Apply the catalog rules for multi-match severity (highest wins) and for grouping repeated occurrences into one finding.
4. Sort the findings **CRITICAL → HIGH → MEDIUM → LOW**, then by file path and line.
5. Print the **audit report** in full, exactly in the template format, with the severity summary and the total.

Then end your turn with exactly this question, as the last line of your message:

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

**Confirmation gate:** do not create, modify or delete any file — not even the report — until the user answers affirmatively (`y`, `yes`, `s`, `sim`, or an equivalent explicit approval). If the answer is negative or unclear, stop and say that no file was changed. If the user approves only part of the findings, apply only those.

## Phase 3 — Refactoring

Read `references/mvc-guidelines.md` and `references/refactoring-playbook.md`. Then execute the steps below **in order**.

### Step 1 — Plan

Write a short plan (printed, not saved): the target directory layout for this stack (from the guidelines), which existing files map to which new modules, and which playbook pattern (`PB-NN`) fixes each finding. For a project that is already partially layered, keep the layers that are sound and add or fix only what is missing; for a monolith, split by layer and by domain.

### Step 2 — Baseline (before any change)

1. Copy the original project source (respecting the exclusions) to a temporary directory created with `mktemp -d`, and work there — never boot the original inside the project folder, so its runtime files (databases, caches) do not pollute it.
2. Install the dependencies in that copy with the stack's standard tool (see the guidelines), run the seed step if the project has one, and boot the application on a **free port** (check with `lsof -nP -iTCP:<port> -sTCP:LISTEN`; if the original port is hardcoded, start it with a small wrapper or a temporary edit **inside the copy only**).
3. Call **every endpoint of the inventory** with a representative request (use the project's request examples, README or tests when they exist; otherwise build valid payloads from the code). Call read-only endpoints first and destructive ones (DELETE, reset) last.
4. Record a baseline table: method, path, request summary, status code, and the top-level keys of the JSON body.
5. Stop the server and keep the temporary copy until the end of Phase 3.

### Step 3 — Refactor

1. Create the target structure and move the code into it following the guidelines: configuration, models, views/routes, controllers, services when needed, middlewares (centralized error handling and auth guard), and the composition root / entry point.
2. Apply the playbook pattern for **every finding** of the approved report. Follow the behavior-preservation rules of the guidelines: every route, method and status code stays; the original start command and default port keep working, with the port overridable through `PORT`; only sensitive data leaves response bodies; dangerous admin routes stay behind the admin token.
3. Delete the old files that were fully replaced, so the project has one clear entry point and no dead code. Update the project README run instructions if the start command, environment variables or seed step changed.
4. Add no new runtime dependency unless the playbook requires it for a security fix (for example a password-hashing library on a stack without one in its standard library); state every dependency you add.

### Step 4 — Smoke test

Create a smoke test in the project's own language that uses **only the standard library / runtime built-ins** (template in the playbook):

- Python: `tests/smoke_test.py`, run with `python tests/smoke_test.py`.
- Node.js: `tests/smoke.test.js`, run with `node --test tests/`.
- Other stacks: the equivalent file under the project's test folder, run with the stack's built-in runner.

The smoke test must boot the application as a subprocess on a free port with a **temporary database** (through the configuration's environment variables), run the seed step when the project has one, wait until it answers, call every endpoint of the inventory with the same requests as the baseline (sending the admin token where required), assert the expected status codes, and stop the server even when an assertion fails.

### Step 5 — Validate

1. Install the dependencies in the project (use a project-local virtual environment for Python, `npm install` for Node.js) and boot the refactored application with its documented start command on a free port. It must start without errors.
2. Run the smoke test. It must pass.
3. Compare each endpoint with the baseline, calling it **exactly as in the baseline (no admin token)**: status codes must match, except for admin routes as defined in the guidelines (401 without the token, original status with it). Any other difference is a failure to fix, not a note. Response body keys must match, except for sensitive fields that were removed on purpose.
4. Re-scan the new code with the catalog and list any finding that remains, with the reason.
5. If anything fails, fix the code and validate again. **Make at most 3 fix attempts.** If it still fails, stop and report exactly what fails — never claim success for a check that did not pass.
6. Stop every server you started and delete the temporary directories.

### Step 6 — Report

Print the **Phase 3 block** exactly as defined in `references/report-template.md`: the new project structure tree, the baseline vs after table, the validation checklist with `✓` for each check that passed and `✗` for each that failed, and the list of remaining findings (or "none").
