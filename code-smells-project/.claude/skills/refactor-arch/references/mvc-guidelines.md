# MVC Architecture Guidelines

Knowledge for **Phase 3**: the target architecture, the layout per stack, the rules that preserve behavior, and how to adapt to the starting point.

## Layers and responsibilities

### Config
- One module (`config/settings.*`) reads **every** setting from the environment with a safe default: port, host, debug flag, database path/URL, secret key, admin token, external service credentials.
- Secrets have **no literal default** in code. When a secret is missing, generate an ephemeral random value at startup (e.g. `secrets.token_hex(32)`, `crypto.randomBytes(32)`) and log a warning, so the app still boots in development but nothing secret is committed.
- Debug is **off** unless an environment variable turns it on.
- Ship a `.env.example` listing every variable with an empty or harmless value; never create a real `.env`.

### Models
- Own the data: table definitions/ORM models, data-access functions or repositories, and **domain rules** that depend only on the data (e.g. "is overdue", "order total", "discount tier").
- One module per domain entity (`models/product_model.py`, `models/user.js`).
- No HTTP: never import `request`, `req`, `res`, `jsonify` or status codes.
- Use parameterized queries or the ORM; never build SQL with string concatenation.
- Expose safe serializers (`to_dict()` / `toJSON()`) that never include passwords, hashes or secrets.

### Views / Routes
- Map HTTP to controllers: path, method, request parsing, response serialization and status codes.
- One module per resource or a single `routes` module for small APIs (`views/routes.py`, `routes/index.js`).
- No SQL, no business rules, no try/except per handler (errors go to the error middleware).
- In an API without templates, the JSON serialization **is** the view; keep it here or in model serializers.

### Controllers
- Own the **application flow** of each use case: validate input (through the validation helpers/schemas), call models and services in the right order, decide the result.
- Receive plain data (dicts/objects) from the route and return plain data or raise domain errors; they do not touch the framework's request/response objects.
- No SQL and no direct database driver calls.
- One module per domain (`controllers/order_controller.py`, `controllers/checkoutController.js`).

### Services (optional)
- Side effects and integrations: notifications (e-mail/SMS/push), payment gateway, external APIs, password hashing helpers.
- Receive their configuration from config (injected), never hardcoded.
- Create them only when the project has such side effects.

### Middlewares
- **Centralized error handling:** one handler that turns domain errors (`NotFoundError`, `ValidationError`, `ConflictError`, `UnauthorizedError`) into JSON responses with the right status code, and unexpected errors into a generic 500 **without internal details**, logging the stack trace server-side.
- **Auth guard:** the admin-token check for protected routes.
- Request logging when useful.

### Composition root / entry point
- `app.py` / `src/app.js` (or the original entry file name) creates the app through a factory (`create_app(config)` / `createApp(config)`), wires config → database → models → services → controllers → routes → middlewares, and starts the server only when run directly.
- It is the **only** place that knows every concrete implementation.
- Keep the original start command working (`python app.py`, `npm start`).

## Dependency direction

```
routes/views ──▶ controllers ──▶ models
      │               │            ▲
      │               └──▶ services┘ (services may read models)
      └──▶ middlewares
config ◀── everyone (read-only)        composition root ──▶ everything
```

- Models import nothing from controllers, routes or the web framework.
- Controllers never import routes.
- Nothing imports the composition root (avoid import cycles: scripts such as a seed import the factory, not a module-level app with side effects).

## Target layouts

### Python / Flask

```
<project>/
├── app.py                      # composition root: create_app() + if __name__ == "__main__"
├── config/
│   ├── __init__.py
│   └── settings.py             # Settings read from os.environ
├── database.py | models/db.py  # connection / SQLAlchemy instance, schema + seed helpers
├── models/
│   ├── __init__.py
│   └── <entity>_model.py
├── controllers/
│   ├── __init__.py
│   └── <domain>_controller.py
├── views/ (or routes/)
│   ├── __init__.py
│   └── <domain>_routes.py      # Blueprints
├── services/                   # only when there are side effects
├── middlewares/
│   ├── __init__.py
│   ├── error_handler.py
│   └── auth.py
├── tests/smoke_test.py
├── .env.example
└── requirements.txt
```

- Keep `views/` for an unstructured project; when the project already has `routes/`, keep the name `routes/` (it is the view layer) instead of renaming.
- Use Flask Blueprints registered in `create_app()`. Register `@app.errorhandler(Exception)` and domain-error handlers in `middlewares/error_handler.py`.
- Install dependencies in a project-local `.venv` (`python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`).

### Node.js / Express

```
<project>/
├── package.json                # "start" still points to the entry point
├── src/
│   ├── app.js                  # composition root: createApp() + listen when run directly
│   ├── config/settings.js      # process.env with defaults
│   ├── database/               # connection, schema, seed, promisified helpers
│   ├── models/                 # <entity>Model.js (repositories, parameterized SQL)
│   ├── controllers/            # <domain>Controller.js (use-case flow)
│   ├── routes/                 # express.Router() per domain (the view layer)
│   ├── services/               # payment, password hashing, notifications
│   └── middlewares/            # errorHandler.js, adminAuth.js, asyncHandler.js
├── tests/smoke.test.js
└── .env.example
```

- Use `async/await` over promisified database calls; wrap async handlers so rejections reach the error middleware (Express 4 does not do it by itself).
- The error middleware has four parameters `(err, req, res, next)` and is registered **after** the routes.
- Use `node:crypto` (`scrypt` + random salt + `timingSafeEqual`) for passwords: no new dependency.

### Other stacks (generic mapping)

| Layer | Spring Boot | Laravel | Rails | ASP.NET Core | Go |
|---|---|---|---|---|---|
| Config | `application.yml` + env | `.env` + `config/` | `config/credentials`, ENV | `appsettings.json` + env | env + `config` pkg |
| Models | `@Entity` + `Repository` | Eloquent models | ActiveRecord models | EF Core entities + repositories | `internal/models` + repo pkg |
| Views/Routes | `@RestController` mappings | `routes/api.php` | `config/routes.rb` | Controllers' route attributes / minimal API | `internal/http` handlers |
| Controllers | `@Service` use cases | Controllers + Actions | Controllers + service objects | Application services | `internal/service` |
| Middlewares | `@ControllerAdvice`, filters | Middleware | `rescue_from`, Rack middleware | Exception middleware | `http.Handler` wrappers |

## Behavior-preservation rules

These rules are mandatory; validation in Phase 3 checks them.

1. **Every original route stays** with the same path and method, and returns the **same status code** for the same request as in the baseline. The only status-code changes allowed are: (a) the admin-token guard of rule 4, and (b) a request that crashed with `500` because of invalid input now answering `400`. Do **not** add new business restrictions that reject requests the original accepted (e.g. refusing to delete a record that has children); fix data consistency inside the operation instead (cascade or clean up in a transaction).
2. **Response bodies keep their shape** (same top-level keys and envelope). The only allowed changes are removing sensitive fields (passwords, hashes, secret keys, card numbers, internal paths) and replacing raw internal error messages with a generic message.
3. **Start command and default port stay.** Read the port from `PORT` (and host from `HOST`) with the original value as default, so the app can be validated on a free port.
4. **Dangerous admin routes stay but are protected:** require the header `X-Admin-Token` to match the `ADMIN_TOKEN` environment variable. Without a valid token return `401` (missing) or `403` (wrong); when `ADMIN_TOKEN` is not configured the route is disabled (`403`). With a valid token the route keeps its original behavior, narrowed to the safe subset when the original is arbitrary execution (e.g. an SQL console accepts only a single read-only `SELECT`).
5. **The admin-token guard is only for admin routes.** A route qualifies only when (a) its path is under an admin namespace (`/admin/...`, `/api/admin/...`), or (b) it executes client-supplied SQL/code or wipes whole tables. Every other route stays public with its original status codes, even when the audit reported it under AP-22 (Missing Authentication): introducing real end-user authentication changes the API contract and needs a product decision, so list those AP-22 locations under "Remaining Findings" with that reason instead of guarding them.
6. **Seed data and seed logins keep working with the same credentials.** Keep every seed user, product and record with the same values, including the same demo passwords (hash them on insert — do not move them to environment variables or randomize them), so the original logins still succeed; when an existing database may hold legacy plain-text or weak hashes, verify the legacy format once and re-hash on successful login (see PB-18).
7. **Database location stays the same by default** (same file name or in-memory), overridable through an environment variable (`DATABASE_PATH`, `DATABASE_URL`) so tests use a temporary database.
8. **Request field names stay** even when they are cryptic; rename the internal variables, not the public contract.

## Adapting to the starting point

### Monolith / god files
- Split by **layer first, then by domain**: one model and one controller per entity/domain, one route module per resource.
- Move code without changing behavior first, then apply the playbook fixes one finding at a time.
- Delete the old god files once nothing imports them.

### Partially layered project
- **Keep what is sound**: existing ORM models, blueprint names, URL structure, seed script, folder names such as `routes/` and `services/`.
- **Add what is missing**: config module, controllers, error middleware, auth guard, app factory.
- **Move misplaced logic**: business rules from routes into models/controllers; resources living in the wrong module (e.g. a CRUD inside a reports blueprint) into their own module — keeping the same URLs.
- **Wire unused helpers or delete them**: if a validator or constant already exists, use it instead of duplicating; delete what stays unused.

### Already layered MVC
- Do not restructure; fix the findings in place and add only the missing cross-cutting pieces.
