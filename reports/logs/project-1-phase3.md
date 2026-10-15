# Skill run transcript

- Session: `fac2c069-c7bf-4aee-a9de-36dad76607ca`
- Model: `claude-opus-5-5`

> `Read` /Users/ricardorauberpereira/Downloads/MBA-Desafios/Refatoracao_Arquitetural-Skills/.worktrees/spec-0007-run-skill-on-code-smells-project/code-smells-project/.claude/skills/refactor-arch/references/mvc-guidelines.md

> `Read` /Users/ricardorauberpereira/Downloads/MBA-Desafios/Refatoracao_Arquitetural-Skills/.worktrees/spec-0007-run-skill-on-code-smells-project/code-smells-project/.claude/skills/refactor-arch/references/refactoring-playbook.md

## Phase 3, Step 1: Plan

**Target layout (Python / Flask).** This is a monolith, so I'm splitting it first by layer and then by domain:

```
app.py                     composition root: create_app(settings) + __main__
config/settings.py         HOST, PORT, FLASK_DEBUG, DATABASE_PATH, SECRET_KEY, ADMIN_TOKEN, APP_ENV, LOG_LEVEL
database.py                per-request connection (flask.g), schema, seed (hashed passwords), read-only connection
models/                    produto_model, usuario_model, pedido_model, relatorio_model, sistema_model
controllers/               validators, produto/usuario/pedido/relatorio/sistema/admin controllers
views/                     Blueprints: produto/usuario/pedido/relatorio/sistema/admin routes
services/                  notification_service (logs), password_service (werkzeug.security)
middlewares/               errors.py (domain errors), error_handler.py, auth.py (X-Admin-Token)
tests/smoke_test.py, .env.example, README.md
```

**How the old files map to the new modules**
- `app.py` routes → `views/*`.
- `app.py` admin handlers → `views/admin_routes.py`, `controllers/admin_controller.py` and `models/sistema_model.py`.
- `controllers.py` → `controllers/*` (flow) plus `views/*` (HTTP).
- `models.py` → `models/*`.
- `database.py` → `database.py`, rewritten.

**Which playbook pattern fixes each finding**

| Finding | Fix |
|---|---|
| AP-03 | PB-03 |
| AP-01 | PB-01 |
| AP-04 | PB-04: guard plus a read-only `SELECT` console |
| AP-05 | PB-05 |
| AP-18 | PB-18: werkzeug hashing, legacy plain-text verified once and re-hashed |
| AP-02 | PB-02 |
| AP-08 | PB-08 |
| AP-19 | PB-19 |
| AP-22 | PB-04, for admin routes only; the rest stay listed as remaining |
| AP-06 | PB-06 |
| AP-07 | PB-07 |
| AP-10 | PB-10 |
| AP-11 | PB-11 |
| AP-13 | PB-13 |
| AP-12 | PB-12: order in a transaction with a conditional stock decrement; product delete becomes a soft delete through the existing `ativo` column, so order items no longer go orphan |
| AP-09 | PB-09 |
| AP-15 | PB-15 |
| AP-14 | PB-14 |
| AP-16 | PB-16 |
| AP-17 | PB-17 |

Next is Step 2: capturing the baseline from a temporary copy of the original code.

> `Bash` SCR=/private/tmp/claude-501/-Users-ricardorauberpereira-Downloads-MBA-Desafios-Refatoracao-Arquitetural-Skills--worktrees-spec-0007-run-skill-on-code-smells-project-code-smells-project/fac2c069-c7bf-4aee-a9de-36dad76607ca/scratchpad && mkdir -p $SCR && BASE=$(mktemp -d "$SCR/baseline.XXXXXX") && cp  ...

> `Bash` BASE=/private/tmp/claude-501/-Users-ricardorauberpereira-Downloads-MBA-Desafios-Refatoracao-Arquitetural-Skills--worktrees-spec-0007-run-skill-on-code-smells-project-code-smells-project/fac2c069-c7bf-4aee-a9de-36dad76607ca/scratchpad/baseline.nnXQkl && cd $BASE && python3 -m venv .venv && .venv/bin/ ...

Now the baseline client script (stdlib only, kept in the scratchpad) and a wrapper that boots the original on a free port without editing it.

> `Write` /private/tmp/claude-501/-Users-ricardorauberpereira-Downloads-MBA-Desafios-Refatoracao-Arquitetural-Skills--worktrees-spec-0007-run-skill-on-code-smells-project-code-smells-project/fac2c069-c7bf-4aee-a9de-36dad76607ca/scratchpad/probe.py

> `Write` /private/tmp/claude-501/-Users-ricardorauberpereira-Downloads-MBA-Desafios-Refatoracao-Arquitetural-Skills--worktrees-spec-0007-run-skill-on-code-smells-project-code-smells-project/fac2c069-c7bf-4aee-a9de-36dad76607ca/scratchpad/run_original.py

> `Bash` SCR=/private/tmp/claude-501/-Users-ricardorauberpereira-Downloads-MBA-Desafios-Refatoracao-Arquitetural-Skills--worktrees-spec-0007-run-skill-on-code-smells-project-code-smells-project/fac2c069-c7bf-4aee-a9de-36dad76607ca/scratchpad; BASE=$SCR/baseline.nnXQkl PORT=$(python3 -c "import socket;s=socke ...

The baseline is recorded (19/19 endpoints) and the server is stopped. Now Step 3, the refactor. First, config and the database:

> `Write` /Users/ricardorauberpereira/Downloads/MBA-Desafios/Refatoracao_Arquitetural-Skills/.worktrees/spec-0007-run-skill-on-code-smells-project/code-smells-project/config/__init__.py

> `Write` /Users/ricardorauberpereira/Downloads/MBA-Desafios/Refatoracao_Arquitetural-Skills/.worktrees/spec-0007-run-skill-on-code-smells-project/code-smells-project/config/settings.py

> `Write` /Users/ricardorauberpereira/Downloads/MBA-Desafios/Refatoracao_Arquitetural-Skills/.worktrees/spec-0007-run-skill-on-code-smells-project/code-smells-project/services/password_service.py

> `Write` /Users/ricardorauberpereira/Downloads/MBA-Desafios/Refatoracao_Arquitetural-Skills/.worktrees/spec-0007-run-skill-on-code-smells-project/code-smells-project/services/notification_service.py

> `Write` /Users/ricardorauberpereira/Downloads/MBA-Desafios/Refatoracao_Arquitetural-Skills/.worktrees/spec-0007-run-skill-on-code-smells-project/code-smells-project/services/__init__.py

> `Write` /Users/ricardorauberpereira/Downloads/MBA-Desafios/Refatoracao_Arquitetural-Skills/.worktrees/spec-0007-run-skill-on-code-smells-project/code-smells-project/database.py

> `Write` /Users/ricardorauberpereira/Downloads/MBA-Desafios/Refatoracao_Arquitetural-Skills/.worktrees/spec-0007-run-skill-on-code-smells-project/code-smells-project/middlewares/errors.py

> `Write` /Users/ricardorauberpereira/Downloads/MBA-Desafios/Refatoracao_Arquitetural-Skills/.worktrees/spec-0007-run-skill-on-code-smells-project/code-smells-project/middlewares/error_handler.py

> `Write` /Users/ricardorauberpereira/Downloads/MBA-Desafios/Refatoracao_Arquitetural-Skills/.worktrees/spec-0007-run-skill-on-code-smells-project/code-smells-project/middlewares/auth.py

> `Write` /Users/ricardorauberpereira/Downloads/MBA-Desafios/Refatoracao_Arquitetural-Skills/.worktrees/spec-0007-run-skill-on-code-smells-project/code-smells-project/middlewares/__init__.py

Now the models:

> `Edit` /Users/ricardorauberpereira/Downloads/MBA-Desafios/Refatoracao_Arquitetural-Skills/.worktrees/spec-0007-run-skill-on-code-smells-project/code-smells-project/database.py

> `Write` /Users/ricardorauberpereira/Downloads/MBA-Desafios/Refatoracao_Arquitetural-Skills/.worktrees/spec-0007-run-skill-on-code-smells-project/code-smells-project/models/produto_model.py

> `Write` /Users/ricardorauberpereira/Downloads/MBA-Desafios/Refatoracao_Arquitetural-Skills/.worktrees/spec-0007-run-skill-on-code-smells-project/code-smells-project/models/usuario_model.py

> `Write` /Users/ricardorauberpereira/Downloads/MBA-Desafios/Refatoracao_Arquitetural-Skills/.worktrees/spec-0007-run-skill-on-code-smells-project/code-smells-project/models/pedido_model.py

> `Write` /Users/ricardorauberpereira/Downloads/MBA-Desafios/Refatoracao_Arquitetural-Skills/.worktrees/spec-0007-run-skill-on-code-smells-project/code-smells-project/models/relatorio_model.py

> `Write` /Users/ricardorauberpereira/Downloads/MBA-Desafios/Refatoracao_Arquitetural-Skills/.worktrees/spec-0007-run-skill-on-code-smells-project/code-smells-project/models/sistema_model.py

> `Write` /Users/ricardorauberpereira/Downloads/MBA-Desafios/Refatoracao_Arquitetural-Skills/.worktrees/spec-0007-run-skill-on-code-smells-project/code-smells-project/models/__init__.py

Controllers and validators:

> `Write` /Users/ricardorauberpereira/Downloads/MBA-Desafios/Refatoracao_Arquitetural-Skills/.worktrees/spec-0007-run-skill-on-code-smells-project/code-smells-project/controllers/validators.py

> `Write` /Users/ricardorauberpereira/Downloads/MBA-Desafios/Refatoracao_Arquitetural-Skills/.worktrees/spec-0007-run-skill-on-code-smells-project/code-smells-project/controllers/produto_controller.py

> `Write` /Users/ricardorauberpereira/Downloads/MBA-Desafios/Refatoracao_Arquitetural-Skills/.worktrees/spec-0007-run-skill-on-code-smells-project/code-smells-project/controllers/usuario_controller.py

> `Write` /Users/ricardorauberpereira/Downloads/MBA-Desafios/Refatoracao_Arquitetural-Skills/.worktrees/spec-0007-run-skill-on-code-smells-project/code-smells-project/controllers/pedido_controller.py

> `Write` /Users/ricardorauberpereira/Downloads/MBA-Desafios/Refatoracao_Arquitetural-Skills/.worktrees/spec-0007-run-skill-on-code-smells-project/code-smells-project/controllers/relatorio_controller.py

> `Write` /Users/ricardorauberpereira/Downloads/MBA-Desafios/Refatoracao_Arquitetural-Skills/.worktrees/spec-0007-run-skill-on-code-smells-project/code-smells-project/controllers/sistema_controller.py

> `Write` /Users/ricardorauberpereira/Downloads/MBA-Desafios/Refatoracao_Arquitetural-Skills/.worktrees/spec-0007-run-skill-on-code-smells-project/code-smells-project/controllers/admin_controller.py

> `Write` /Users/ricardorauberpereira/Downloads/MBA-Desafios/Refatoracao_Arquitetural-Skills/.worktrees/spec-0007-run-skill-on-code-smells-project/code-smells-project/controllers/__init__.py

Views (Blueprints), the composition root, `.env.example` and the README:

> `Write` /Users/ricardorauberpereira/Downloads/MBA-Desafios/Refatoracao_Arquitetural-Skills/.worktrees/spec-0007-run-skill-on-code-smells-project/code-smells-project/views/produto_routes.py

> `Write` /Users/ricardorauberpereira/Downloads/MBA-Desafios/Refatoracao_Arquitetural-Skills/.worktrees/spec-0007-run-skill-on-code-smells-project/code-smells-project/views/usuario_routes.py

> `Write` /Users/ricardorauberpereira/Downloads/MBA-Desafios/Refatoracao_Arquitetural-Skills/.worktrees/spec-0007-run-skill-on-code-smells-project/code-smells-project/views/pedido_routes.py

> `Write` /Users/ricardorauberpereira/Downloads/MBA-Desafios/Refatoracao_Arquitetural-Skills/.worktrees/spec-0007-run-skill-on-code-smells-project/code-smells-project/views/relatorio_routes.py

> `Write` /Users/ricardorauberpereira/Downloads/MBA-Desafios/Refatoracao_Arquitetural-Skills/.worktrees/spec-0007-run-skill-on-code-smells-project/code-smells-project/views/sistema_routes.py

> `Write` /Users/ricardorauberpereira/Downloads/MBA-Desafios/Refatoracao_Arquitetural-Skills/.worktrees/spec-0007-run-skill-on-code-smells-project/code-smells-project/views/admin_routes.py

> `Write` /Users/ricardorauberpereira/Downloads/MBA-Desafios/Refatoracao_Arquitetural-Skills/.worktrees/spec-0007-run-skill-on-code-smells-project/code-smells-project/views/__init__.py

> `Write` /Users/ricardorauberpereira/Downloads/MBA-Desafios/Refatoracao_Arquitetural-Skills/.worktrees/spec-0007-run-skill-on-code-smells-project/code-smells-project/app.py

> `Write` /Users/ricardorauberpereira/Downloads/MBA-Desafios/Refatoracao_Arquitetural-Skills/.worktrees/spec-0007-run-skill-on-code-smells-project/code-smells-project/.env.example

> `Write` /Users/ricardorauberpereira/Downloads/MBA-Desafios/Refatoracao_Arquitetural-Skills/.worktrees/spec-0007-run-skill-on-code-smells-project/code-smells-project/README.md

Next, deleting the god files that have been fully replaced (`controllers.py` and `models.py`, now packages) and writing the smoke test:

> `Bash` rm controllers.py models.py && ls

> `Write` /Users/ricardorauberpereira/Downloads/MBA-Desafios/Refatoracao_Arquitetural-Skills/.worktrees/spec-0007-run-skill-on-code-smells-project/code-smells-project/tests/smoke_test.py

Step 5, validation: install the dependencies in the project `.venv`, boot with the documented start command, and compare against the baseline without an admin token.

> `Bash` .venv/bin/pip install -q -r requirements.txt 2>&1 | grep -v notice SCR=/private/tmp/claude-501/-Users-ricardorauberpereira-Downloads-MBA-Desafios-Refatoracao-Arquitetural-Skills--worktrees-spec-0007-run-skill-on-code-smells-project-code-smells-project/fac2c069-c7bf-4aee-a9de-36dad76607ca/scratchpad  ...

> `Bash` SCR=/private/tmp/claude-501/-Users-ricardorauberpereira-Downloads-MBA-Desafios-Refatoracao-Arquitetural-Skills--worktrees-spec-0007-run-skill-on-code-smells-project-code-smells-project/fac2c069-c7bf-4aee-a9de-36dad76607ca/scratchpad pgrep -fl "app.py"; pkill -f "bin/python app.py"; sleep 0.5; pgrep  ...

> `Bash` SCR=/private/tmp/claude-501/-Users-ricardorauberpereira-Downloads-MBA-Desafios-Refatoracao-Arquitetural-Skills--worktrees-spec-0007-run-skill-on-code-smells-project-code-smells-project/fac2c069-c7bf-4aee-a9de-36dad76607ca/scratchpad kill 82029; sleep 0.5; pgrep -fl "app.py" || echo "no app.py proces ...

The only body difference is `senha`, which was removed on purpose; the earlier list-shape gap came from my probe truncating bodies at 300 chars. Next, the smoke test:

> `Bash` .venv/bin/python tests/smoke_test.py; echo "exit=$?"; pgrep -fl "app.py" || echo "no app.py process left"

> `Bash` SCR=/private/tmp/claude-501/-Users-ricardorauberpereira-Downloads-MBA-Desafios-Refatoracao-Arquitetural-Skills--worktrees-spec-0007-run-skill-on-code-smells-project-code-smells-project/fac2c069-c7bf-4aee-a9de-36dad76607ca/scratchpad && D=$(mktemp -d "$SCR/edge.XXXXXX") && DATABASE_PATH=$D/e.db SECRE ...

Every edge check behaves as intended. Last check is the re-scan of the new code with the catalog's greppable signals:

> `Bash` F=$(find . -name "*.py" -not -path "./.venv/*" -not -path "./.claude/*" -not -path "*/__pycache__/*" | sort) echo "== print (excl. smoke test)"; grep -n "print(" $F | grep -v tests/ echo "== execute with f-string/concat"; grep -nE "execute(many)?\(\s*f?[\"'].*(\+|\{)" $F; grep -nE "f\"\"\"SELECT|f\" ...

zsh doesn't word-split `$F`, so that scan never ran. Rerunning it with recursive grep:

> `Bash` G="grep -rnE --include=*.py --exclude-dir=.venv --exclude-dir=.claude --exclude-dir=__pycache__" echo "== print (excl. tests)"; $G "print\(" . | grep -v "^./tests/" echo "== SQL built with f-string/concat"; $G "execute(many)?\(" . | grep -E "\+ *[a-z]|f\"|f'" ; $G "f\"\"\"SELECT|f\"SELECT|f\"DELETE" ...

Same word-splitting issue. Running the scan under bash:

> `Bash` bash -c ' G() { grep -rnE --include="*.py" --exclude-dir=.venv --exclude-dir=.claude --exclude-dir=__pycache__ "$@"; } echo "== print (excl. tests)"; G "print\(" . | grep -v "^./tests/" echo "== SQL built with f-string/concat"; G "execute(many)?\(" . | grep -E "\+ *[a-z]|f\"|f'"'"'"; G "f\"\"\"SELEC ...

> `Bash` SCR=/private/tmp/claude-501/-Users-ricardorauberpereira-Downloads-MBA-Desafios-Refatoracao-Arquitetural-Skills--worktrees-spec-0007-run-skill-on-code-smells-project-code-smells-project/fac2c069-c7bf-4aee-a9de-36dad76607ca/scratchpad rm -rf "$SCR"/baseline.* "$SCR"/after.* ; ls "$SCR" find . -name __ ...

================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
```
code-smells-project/
├── app.py                         # composition root: create_app(settings) + __main__
├── .env.example
├── README.md
├── requirements.txt               # unchanged (flask, flask-cors)
├── config/
│   ├── __init__.py
│   └── settings.py                # HOST, PORT, FLASK_DEBUG, DATABASE_PATH, APP_ENV, LOG_LEVEL, SECRET_KEY, ADMIN_TOKEN
├── database.py                    # per-request connection (flask.g), read-only connection, schema, seed
├── models/
│   ├── __init__.py
│   ├── produto_model.py
│   ├── usuario_model.py
│   ├── pedido_model.py
│   ├── relatorio_model.py
│   └── sistema_model.py
├── controllers/
│   ├── __init__.py
│   ├── validators.py
│   ├── produto_controller.py
│   ├── usuario_controller.py
│   ├── pedido_controller.py
│   ├── relatorio_controller.py
│   ├── sistema_controller.py
│   └── admin_controller.py
├── views/
│   ├── __init__.py                # BLUEPRINTS
│   ├── produto_routes.py
│   ├── usuario_routes.py
│   ├── pedido_routes.py
│   ├── relatorio_routes.py
│   ├── sistema_routes.py
│   └── admin_routes.py
├── services/
│   ├── __init__.py
│   ├── notification_service.py
│   └── password_service.py
├── middlewares/
│   ├── __init__.py
│   ├── errors.py
│   ├── error_handler.py
│   └── auth.py
└── tests/
    └── smoke_test.py
```

## Findings Addressed
- CRITICAL AP-03 God Class / God File → PB-03 (`controllers.py` and `models.py` deleted; split into `models/`, `controllers/`, `views/`, `services/`, `middlewares/`)
- CRITICAL AP-01 Hardcoded Credentials → PB-01 (`config/settings.py`, `app.py`, `.env.example`)
- CRITICAL AP-04 Unprotected Dangerous Endpoint → PB-04 (`middlewares/auth.py`, `views/admin_routes.py`, `controllers/admin_controller.py`: only one `SELECT`, run on a `query_only` connection)
- CRITICAL AP-05 Sensitive Data Exposure → PB-05 (`models/usuario_model.py`, `controllers/sistema_controller.py`)
- CRITICAL AP-18 Weak Password Hashing → PB-18 (`services/password_service.py`, `database.py`, `controllers/usuario_controller.py`: plain-text legacy rows are re-hashed on the next successful login)
- CRITICAL AP-02 SQL Injection → PB-02 (all of `models/*`)
- HIGH AP-08 Tight Coupling → PB-08 (`app.py` with `create_app`, `views/__init__.py`)
- HIGH AP-19 Debug Mode in Production → PB-19 (`config/settings.py`, `app.py`)
- HIGH AP-22 Missing Authentication → PB-04 (applied to the `/admin/*` routes only; see Remaining Findings)
- HIGH AP-06 Business Logic in Controller → PB-06 (`controllers/validators.py`, `models/pedido_model.py`, `services/notification_service.py`)
- HIGH AP-07 Mutable Global State → PB-07 (`database.py`)
- MEDIUM AP-10 Missing Input Validation → PB-10 (`controllers/validators.py`)
- MEDIUM AP-11 Broad Exception Handling → PB-11 (`middlewares/errors.py`, `middlewares/error_handler.py`)
- MEDIUM AP-13 Duplicated Logic → PB-13 (`models/*` serializers, `pedido_model.listar`, `validar_produto`)
- MEDIUM AP-12 Missing Transaction → PB-12 (`models/pedido_model.py`; `models/produto_model.py` uses a soft delete through `ativo`)
- MEDIUM AP-09 N+1 Queries → PB-09 (`models/pedido_model.py`, `models/relatorio_model.py`)
- LOW AP-15 Magic Numbers / Strings → PB-15 (`models/*`, `config/settings.py`)
- LOW AP-14 Print as Logging → PB-14 (all modules; logs no longer contain e-mail addresses)
- LOW AP-16 Poor Naming → PB-16 (`models/pedido_model.py`, `views/*`)
- LOW AP-17 Unused Imports → PB-17 (`database.py`; `models.py` removed)

## Baseline vs After
| Method | Path | Baseline | After | Note |
|---|---|---|---|---|
| GET | / | 200 | 200 | |
| GET | /produtos | 200 | 200 | |
| GET | /produtos/busca?q=Mouse | 200 | 200 | |
| GET | /produtos/1 | 200 | 200 | |
| GET | /usuarios | 200 | 200 | `senha` removed from each record |
| GET | /usuarios/1 | 200 | 200 | `senha` removed |
| GET | /pedidos | 200 | 200 | |
| GET | /pedidos/usuario/2 | 200 | 200 | |
| GET | /relatorios/vendas | 200 | 200 | identical body |
| GET | /health | 200 | 200 | `secret_key`, `db_path`, `debug` removed |
| POST | /produtos | 201 | 201 | |
| PUT | /produtos/11 | 200 | 200 | |
| POST | /usuarios | 201 | 201 | |
| POST | /login | 200 | 200 | seed login unchanged, identical body |
| POST | /pedidos | 201 | 201 | |
| PUT | /pedidos/1/status | 200 | 200 | |
| DELETE | /produtos/11 | 200 | 200 | |
| POST | /admin/query | 200 | 401 without token / 200 with token | protected admin route |
| POST | /admin/reset-db | 200 | 401 without token / 200 with token | protected admin route |

## Validation
  ✓ Application boots without errors (`python app.py`, port 5000 by default; validated with `PORT=50801` because macOS ControlCenter holds port 5000 on this machine)
  ✓ Smoke test passes (`python tests/smoke_test.py`: 29 checks)
  ✓ All original endpoints respond with the baseline status codes (17/17 public routes identical; the 2 admin routes return 401 without the token, as the guidelines require)
  ✓ Configuration extracted (no hardcoded secrets)
  ✓ Centralized error handling
  ✓ Zero CRITICAL/HIGH anti-patterns remaining (only the AP-22 exception below, which the guidelines require me to leave)

## Remaining Findings
- HIGH AP-22 Missing Authentication — `views/produto_routes.py` (POST/PUT/DELETE), `views/usuario_routes.py` (GET /usuarios), `views/pedido_routes.py` (GET /pedidos, PUT status) and `views/relatorio_routes.py` stay public, and `/login` still issues no token. Adding end-user authentication changes the API contract, so it needs a product decision (guidelines, rule 5).
- MEDIUM AP-11 (accepted) — `controllers/sistema_controller.py:26` keeps one `except Exception` on purpose, so `/health` can report `status: "erro"`. It logs the stack trace and returns a generic message without internal details.
================================

All 20 approved findings were addressed; only AP-22 on the public routes remains, as above. A few behavior changes that are allowed by the guidelines but worth knowing:

- **Inputs that used to crash with 500 now return 400:** a missing body on login or status update, a non-numeric price or price filter, and malformed order items.
- **Tighter rules the original accepted:**
  - Updating a product now checks name length and category, the same rules as creation.
  - New users need a valid e-mail format.
  - Orders reject a quantity of zero or less. A negative quantity used to *increase* stock.
- **Deleting a product is now a soft delete** (`ativo = 0`). The product disappears from the list, lookup, search and the health count exactly as before. Orders that contain it now show its real name instead of "Desconhecido".
- **Admin routes need `ADMIN_TOKEN` set in the environment.** Without it they return 403 even when a token is sent.

Nothing was committed or added to git, and no new dependency was added (password hashing uses `werkzeug.security`, which comes with Flask). The project `.venv` was already there; I only ran `pip install -r requirements.txt` in it. All servers are stopped, and the temporary baseline and validation directories are deleted. The changes to `.claude/skills/refactor-arch/*` in `git status` were already there before this run.

---
Result: success | turns: 54 | duration: 483s
