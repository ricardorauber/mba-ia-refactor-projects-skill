# Project Analysis Heuristics

Knowledge for **Phase 1**. Every conclusion must be backed by a file you read; when two signals disagree, the dependency manifest wins over guesses from file names.

## 1. Scope of the scan

Count and scan only source files written by the project:

- **Include:** source code (`.py`, `.js`, `.mjs`, `.cjs`, `.ts`, `.java`, `.kt`, `.go`, `.php`, `.rb`, `.cs`, ...), SQL files, templates that contain logic.
- **Exclude:** `.claude/`, `.git/`, `node_modules/`, `.venv/`, `venv/`, `env/`, `vendor/`, `dist/`, `build/`, `target/`, `bin/`, `obj/`, `__pycache__/`, lock files (`package-lock.json`, `poetry.lock`, `yarn.lock`), database files (`*.db`, `*.sqlite`, `*.sqlite3`), and documentation/request files (`*.md`, `*.http`), which are inputs for the analysis but not source files.
- Count `__init__.py` and other package markers as source files (state that in the block when they are empty).

Useful commands (read-only):

```bash
find . -type f \( -name "*.py" -o -name "*.js" -o -name "*.ts" \) \
  -not -path "./.claude/*" -not -path "./.git/*" -not -path "*/node_modules/*" \
  -not -path "*/.venv/*" -not -path "*/venv/*" -not -path "*/__pycache__/*" | sort
wc -l <files...>          # lines of code per file and total
```

Report the file count exactly and the line total rounded to the nearest 10 with a `~` prefix (for example `~810 lines of code`).

## 2. Language and framework detection

Read the manifest first, then confirm with imports in the entry point.

### Python

| Signal | Conclusion |
|---|---|
| `requirements.txt`, `pyproject.toml`, `setup.py`, `Pipfile` | Python project; pinned versions come from these files |
| `flask==X` in the manifest, `from flask import Flask`, `app = Flask(__name__)`, `Blueprint(` | **Flask X** |
| `flask-sqlalchemy`, `from flask_sqlalchemy import SQLAlchemy`, `db.Model` | Flask-SQLAlchemy ORM |
| `django` in the manifest, `manage.py`, `settings.py`, `urls.py`, `INSTALLED_APPS` | **Django** |
| `fastapi` in the manifest, `FastAPI()`, `@app.get(`, `APIRouter` | **FastAPI** |
| `flask-cors` / `CORS(app)` | CORS middleware |
| `marshmallow`, `pydantic` | Schema validation library (note whether it is actually used) |

### Node.js / JavaScript / TypeScript

| Signal | Conclusion |
|---|---|
| `package.json` | Node.js project; versions from `dependencies` (a `^4.18.2` range means "Express 4.x, ≥4.18.2") |
| `tsconfig.json`, `.ts` files | TypeScript |
| `express` dependency, `require('express')` / `import express`, `app.get(`, `express.Router()` | **Express** |
| `@nestjs/core`, `@Controller(`, `@Module(` | **NestJS** |
| `fastify` dependency, `fastify()`, `fastify.register(` | **Fastify** |
| `sqlite3`, `better-sqlite3`, `pg`, `mysql2`, `mongoose`, `sequelize`, `prisma`, `typeorm` | Database driver / ORM |
| `"main"` and `"scripts.start"` in `package.json` | Entry point and start command |

### Other stacks (generic fallback)

| Manifest | Language / usual frameworks |
|---|---|
| `pom.xml`, `build.gradle`, `build.gradle.kts` | Java/Kotlin — Spring Boot (`spring-boot-starter-web`, `@RestController`) |
| `go.mod` | Go — `net/http`, Gin (`gin.Default()`), Echo, Fiber |
| `composer.json` | PHP — Laravel (`artisan`, `routes/web.php`), Symfony |
| `Gemfile` | Ruby — Rails (`config/routes.rb`), Sinatra |
| `*.csproj`, `*.sln` | C# — ASP.NET Core (`[ApiController]`, `app.MapGet(`) |

For a fallback stack, say "generic heuristics" in the Architecture line and apply the generic layout of the MVC guidelines.

## 3. Database detection

1. **Engine and access style** — look for the driver/ORM import and the connection call:
   - Raw driver: `sqlite3.connect(`, `new sqlite3.Database(`, `psycopg2.connect(`, `mysql.createConnection(`, `new Pool(`.
   - ORM: `SQLAlchemy()`, `db.Model`, `models.Model` (Django), `mongoose.model(`, `sequelize.define(`, Prisma `schema.prisma`.
2. **Location** — a file path (`"app.db"`, `sqlite:///tasks.db`), `':memory:'` (in-memory, data is lost on restart and seeded at boot) or a server URL (`postgres://`, `DATABASE_URL`).
3. **Tables / entities** — collect from:
   - DDL strings: `CREATE TABLE [IF NOT EXISTS] <name>`.
   - ORM models: `__tablename__ = '<name>'`, class names extending `db.Model` / `Model`, `mongoose.model('<Name>'`.
   - Migrations: `migrations/`, `alembic/versions/`, `prisma/migrations/`.
4. **Seed** — inserts executed at boot, a `seed.py` / `seed.js` / `npm run seed` script, or fixtures. Note whether the seed must run before the first boot.
5. **Credentials** — note (without copying the value) whether connection credentials are hardcoded or read from the environment.

## 4. Architecture classification

| Classification | Evidence |
|---|---|
| **Monolith / god file** | One or a few files mix routing, SQL/data access, business rules, validation and formatting; a "manager"/"utils" class owns the database *and* registers routes; files named `controllers.py`/`models.py` exist but each one spans every domain |
| **Partially layered** | Folders such as `models/`, `routes/`, `services/`, `utils/` exist, but routes still hold business rules or queries, helpers are unused, layers import across in any direction, and there is no config module or centralized error handling |
| **Layered MVC** | Config, models, views/routes, controllers (and services/middlewares) with one-way dependencies and a composition root |

Write the Architecture line as `<classification> — <one-line evidence>`, for example: `Monolithic — routing, SQL and business rules spread over 4 files with no layer boundaries`.

## 5. Endpoint inventory

Build a table `Method | Path | Handler (file:line)`; it is the validation contract for Phase 3.

| Stack | How to find routes |
|---|---|
| Flask | `@app.route(`, `@<bp>.route(`, `app.add_url_rule(`; the default method is `GET`; `methods=[...]` lists the others; collect the blueprint `url_prefix` from `Blueprint(...)` and `register_blueprint(..., url_prefix=...)` |
| Express | `app.<method>(`, `router.<method>(`, `app.use('<prefix>', router)`; methods are `get`, `post`, `put`, `patch`, `delete`, `all` |
| FastAPI | `@app.<method>(`, `@router.<method>(`, `include_router(..., prefix=...)` |
| Django | `urls.py` `path(` / `re_path(` plus the view's allowed methods |
| Generic | grep for the HTTP verbs next to a path string: `grep -nE "(get|post|put|patch|delete)\s*\(\s*['\"]/"` |

Also read request examples shipped with the project (`*.http`, Postman collections, README `curl` examples, tests): they give the payloads Phase 3 needs for the baseline.

## 6. Domain inference

Combine table names, model classes and route prefixes into one line: name the business (e-commerce, learning platform, task management, ...) and list the main entities in the language the code uses. Examples:

- tables `products`, `orders`, `order_items`, `users` + routes `/orders` → "E-commerce API (products, orders, users)".
- tables `courses`, `enrollments`, `payments` + route `/checkout` → "LMS API with course checkout (users, courses, enrollments, payments)".
- tables `tasks`, `categories`, `users` + routes `/reports` → "Task Manager API (tasks, users, categories, reports)".

## 7. Boot information

Record for Phase 3: entry point file, start command (`python app.py`, `flask run`, `npm start`, ...), default host/port (and whether it is hardcoded), required environment variables, seed command, and whether debug mode is on.
