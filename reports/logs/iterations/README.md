# Skill iterations

Runs that failed an acceptance criterion and led to a change in the skill. The logs of each failed run are kept in its folder.

## Project 1 — iteration 1

- Result: Phases 1–2 correct (20 findings, stopped at the confirmation with no file changed). Phase 3 booted the app and the smoke test passed, but it put the admin-token guard on non-admin routes flagged as AP-22 (`GET /usuarios`, `GET /pedidos`, `GET /relatorios/vendas`, `POST/PUT/DELETE /produtos`, `PUT /pedidos/<id>/status`), changing their status codes from 200/201 to 401; moved the seed admin password to an environment variable (seed login `admin@loja.com`/`admin123` stopped working by default); added a new 409 rule for deleting products with orders; and ran `git rm`/`git reset` on the index.
- Cause: the behavior-preservation rule about "private data routes" allowed the guard on any CRITICAL/HIGH route, seed credentials were not explicitly protected, and the skill did not forbid git commands.
- Change: `mvc-guidelines.md` restricts the guard to admin routes (admin namespace, client-supplied SQL/code, table wipes) and keeps AP-22 elsewhere as a remaining finding; forbids new business restrictions that change status codes; requires the same seed credentials. `anti-patterns.md` treats seed demo passwords as AP-18, not AP-01. `SKILL.md` forbids git index commands and makes any non-admin status difference a failure. `refactoring-playbook.md` PB-04 example uses an admin route.

## Project 1 — iteration 2 (interrupted)

- Result: the Phase 1–2 run was aborted with `API Error: Your computer went to sleep mid-response` / `Request timed out`; no file was changed.
- Cause: macOS idle sleep during the headless run (not a skill problem).
- Change: `scripts/run_skill.sh` runs `claude` under `caffeinate -i` and keeps the raw log and transcript even when `claude` fails.

## Project 1 — iteration 3 (accepted)

- Result: same Phase 1–2 output (20 findings); Phase 3 kept all 17 public routes with the baseline status codes, guarded only `/admin/query` and `/admin/reset-db`, kept the seed logins, and its smoke test passed (29 checks).
