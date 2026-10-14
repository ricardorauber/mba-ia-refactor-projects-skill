# Anti-Pattern Catalog

Knowledge for **Phase 2**. Each entry has a stable ID, a fixed severity, concrete detection signals, an example, why it matters and the playbook pattern that fixes it (`references/refactoring-playbook.md`).

## Severity scale

- **CRITICAL** — Severe architecture or security flaws that prevent correct operation, expose sensitive data (e.g. hardcoded credentials, SQL injection) or completely violate separation of concerns (e.g. a "God Class" holding database access, complex logic and routing in the same file).
- **HIGH** — Strong violations of MVC or SOLID that make maintenance and testing very hard (e.g. heavy business logic inside controllers, tight coupling without dependency injection, mutable global state used across the application).
- **MEDIUM** — Standardization problems, code duplication or moderate performance bottlenecks (e.g. N+1 queries, improper middleware use, missing validation on routes).
- **LOW** — Readability improvements, poor variable names, loose "magic numbers".

## How to apply the catalog

1. For every entry, run the greppable signals over the whole project (respecting the scan exclusions) and **read each hit** to confirm it; a grep hit alone is not a finding.
2. **One finding per anti-pattern**, listing every confirmed location. Split into separate findings only when the same anti-pattern has clearly different impacts (e.g. SQL injection in login vs in a search).
3. **Multiple matches:** when one piece of code matches several entries (e.g. a god file that also concatenates SQL), report each anti-pattern separately; when choosing the severity of a single finding that fits several entries, **the highest severity wins**.
4. Do not report an entry when the signal is a false positive (e.g. a `?` placeholder query is not SQL injection; a secret read from `os.environ` with no literal fallback is not hardcoded).
5. Check the **Deprecated APIs** table against the versions found in Phase 1.

## Summary

| ID | Name | Severity | Fix |
|---|---|---|---|
| AP-01 | Hardcoded Credentials / Secrets | CRITICAL | PB-01 |
| AP-02 | SQL Injection | CRITICAL | PB-02 |
| AP-03 | God Class / God File | CRITICAL | PB-03 |
| AP-04 | Unprotected Dangerous Endpoint | CRITICAL | PB-04 |
| AP-05 | Sensitive Data Exposure | CRITICAL | PB-05 |
| AP-06 | Business Logic in Controller / Route | HIGH | PB-06 |
| AP-07 | Mutable Global State | HIGH | PB-07 |
| AP-08 | Tight Coupling / Missing Dependency Injection | HIGH | PB-08 |
| AP-09 | N+1 Queries | MEDIUM | PB-09 |
| AP-10 | Missing Input Validation | MEDIUM | PB-10 |
| AP-11 | Broad Exception Handling / Leaked Error Details | MEDIUM | PB-11 |
| AP-12 | Missing Transaction / Inconsistent Writes | MEDIUM | PB-12 |
| AP-13 | Duplicated Logic | MEDIUM | PB-13 |
| AP-14 | Print / console.log as Logging | LOW | PB-14 |
| AP-15 | Magic Numbers / Strings | LOW | PB-15 |
| AP-16 | Poor Naming | LOW | PB-16 |
| AP-17 | Unused Imports / Dead Code | LOW | PB-17 |
| AP-18 | Weak Password Hashing | CRITICAL | PB-18 |
| AP-19 | Debug Mode in Production | HIGH | PB-19 |
| AP-20 | Deprecated APIs | MEDIUM | PB-20 |
| AP-21 | Callback Pyramid / Deep Nesting | MEDIUM | PB-21 |
| AP-22 | Missing Authentication / Authorization | HIGH | PB-04 |

---

### AP-01 — Hardcoded Credentials / Secrets
- Severity: CRITICAL
- Fix: PB-01

**Detection signals**
- Python: `SECRET_KEY\s*=\s*['"]`, `app.config\[['"]SECRET_KEY['"]\]\s*=\s*['"]`, `password\s*=\s*['"]`, `api_key|token|secret\s*=\s*['"]`, `smtplib.SMTP(...).login(` with literals.
- JavaScript: object literals with `pass`, `password`, `secret`, `key`, `token` holding strings (`dbPass: "..."`, `paymentGatewayKey: "pk_live_..."`).
- Any value prefixed `pk_live_`, `sk_live_`, `AKIA`, `ghp_`, `xox`; connection strings with `user:password@`.
- The same literal returned by an endpoint (e.g. a health check echoing the secret key) — report it under AP-05 too.

**Example**
```python
app.config["SECRET_KEY"] = "my-super-secret-123"
```

**Why it matters:** anyone with repository access (or a leaked copy) owns the secret; rotating it requires a code change and a deploy.

---

### AP-02 — SQL Injection
- Severity: CRITICAL
- Fix: PB-02

**Detection signals**
- Python: `execute(` whose argument uses `+`, `%`, `.format(` or an f-string with request-derived values: `grep -nE "execute\(.*(\+|%|format\(|f['\"])"`; query strings built incrementally (`query += " AND name LIKE '%" + term`).
- JavaScript: `db.run|get|all|query(` with template literals `${...}` or `+` concatenation inside the SQL string.
- ORM escape hatches with interpolation: `text(f"...")`, `raw(`, `sequelize.query(\`...${}\`)`.

**Example**
```python
cursor.execute("SELECT * FROM users WHERE email = '" + email + "' AND password = '" + pwd + "'")
```

**Why it matters:** an input like `' OR '1'='1` bypasses login; any input can read, change or drop tables.

---

### AP-03 — God Class / God File
- Severity: CRITICAL
- Fix: PB-03

**Detection signals**
- One class or module that does **three or more** of: opens the database / runs DDL, seeds data, registers routes, holds business rules, formats responses, sends notifications.
- A file named `models.*`, `utils.*`, `manager.*`, `*Manager.*`, `app.*` spanning several domains (functions for products *and* users *and* orders *and* reports).
- A class with a `setupRoutes(app)` / `register(app)` method *and* SQL strings.
- Files over ~300 lines mixing layers.

**Example**
```javascript
class AppManager {
  initDb() { this.db.run("CREATE TABLE ...") }
  setupRoutes(app) { app.post('/api/checkout', (req, res) => { /* SQL + payment + response */ }) }
}
```

**Why it matters:** nothing can be tested or changed in isolation; every change risks every feature.

---

### AP-04 — Unprotected Dangerous Endpoint
- Severity: CRITICAL
- Fix: PB-04

**Detection signals**
- A route that executes SQL or code sent by the client: `execute(request...sql)`, `eval(`, `exec(`, `child_process.exec(req...)`.
- Destructive admin routes (`/admin/reset`, `DELETE FROM <table>` without `WHERE`, `/admin/*`, financial reports) with **no** authentication check in the handler or a middleware.

**Example**
```python
@app.route("/admin/query", methods=["POST"])
def run_query():
    cursor.execute(request.get_json()["sql"])
```

**Why it matters:** any anonymous client can read every table, wipe the database or take over the server.

---

### AP-05 — Sensitive Data Exposure
- Severity: CRITICAL
- Fix: PB-05

**Detection signals**
- Serializers / `to_dict()` / row-to-dict mappings that include `password`, `senha`, `pass`, `hash`, `secret`, `token`, card numbers.
- Endpoints returning configuration (`secret_key`, `db_path`, `debug`) — typical in health checks.
- Logs that print card numbers, passwords, keys or full e-mail lists: `print(... + senha)`, `` console.log(`... ${card} ... ${key}`) ``.

**Example**
```python
def to_dict(self):
    return {"id": self.id, "email": self.email, "password": self.password}
```

**Why it matters:** one compromised client, log file or proxy exposes every account or payment credential.

---

### AP-06 — Business Logic in Controller / Route
- Severity: HIGH
- Fix: PB-06

**Detection signals**
- Route handlers or controller functions longer than ~30 lines that contain domain rules: price/discount calculation, stock checks, status transitions, overdue/eligibility rules, payment approval (`card.startsWith("4")`).
- Handlers that build SQL, call the ORM in loops and also format the response.
- Side effects (e-mail, SMS, push, payment) triggered directly from the handler.

**Example**
```python
def create_order():
    data = request.get_json()
    for item in data["items"]:
        if product["stock"] < item["qty"]: ...
    print("SENDING EMAIL ...")
```

**Why it matters:** rules cannot be reused or unit-tested without the HTTP framework and get duplicated across handlers.

---

### AP-07 — Mutable Global State
- Severity: HIGH
- Fix: PB-07

**Detection signals**
- Python: module-level variables reassigned through `global x`; a module-level DB connection shared by every request (`db_connection = None` + `global db_connection`, `check_same_thread=False`).
- JavaScript: module-level `let` objects mutated by functions and exported (`let globalCache = {}`, `let totalRevenue = 0`).
- Singletons that store per-request data in instance lists (`self.notifications.append(...)`) living for the whole process.

**Example**
```javascript
let globalCache = {};
function logAndCache(key, data) { globalCache[key] = data; }
module.exports = { globalCache };
```

**Why it matters:** hidden coupling between requests, race conditions, state that leaks between tests and cannot be replaced.

---

### AP-08 — Tight Coupling / Missing Dependency Injection
- Severity: HIGH
- Fix: PB-08

**Detection signals**
- Modules that import and call a concrete database/service directly everywhere (`from database import get_db` in every layer) instead of receiving it.
- Classes that `new` their own dependencies in the constructor (`this.db = new sqlite3.Database(...)`, `self.smtp = smtplib.SMTP(...)`).
- No composition root / app factory: the app object is created at import time with side effects (`db.create_all()` on import, `app.listen` in the same file that defines routes).

**Example**
```python
import models            # controller calls models.* and database.get_db() directly
from database import get_db
```

**Why it matters:** dependencies cannot be swapped for tests or other environments; the import order becomes the architecture.

---

### AP-09 — N+1 Queries
- Severity: MEDIUM
- Fix: PB-09

**Detection signals**
- A query (`execute(`, `db.get(`, `.query.get(`, `.filter_by(...).count()`) **inside a loop** over the result of another query.
- Lazy relationships accessed in a loop (`len(user.tasks)` for every user, `task.user.name` for every task) without eager loading.
- Nested callbacks issuing one query per row (`rows.forEach(r => db.get(...))`).

**Example**
```python
for order in orders:
    cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (order["id"],))
```

**Why it matters:** the number of queries grows with the data; list and report endpoints slow down linearly or worse.

---

### AP-10 — Missing Input Validation
- Severity: MEDIUM
- Fix: PB-10

**Detection signals**
- Request fields used without type/range checks (`if data["priority"] < 1` crashes with a string), `request.get_json()` used without checking for `None`, `req.body.x` used without validation.
- Create and update paths validating differently; validator helpers that exist but are never called.
- Missing format checks for e-mail, dates, card numbers, enums; default passwords assigned when missing.

**Example**
```python
data = request.get_json()
if "name" in data: ...          # TypeError when the body is empty
```

**Why it matters:** bad input turns into 500 errors or corrupt data instead of a clear 400.

---

### AP-11 — Broad Exception Handling / Leaked Error Details
- Severity: MEDIUM
- Fix: PB-11

**Detection signals**
- Python: bare `except:`; `except Exception as e: return jsonify({"error": str(e)}), 500` repeated in every handler.
- JavaScript: callbacks that ignore `err` (`(err, rows) => { rows.forEach(...) }`), `catch (e) {}` with an empty body, `res.status(500).send(e.message)`.
- No centralized error handler (`@app.errorhandler`, Express error middleware `(err, req, res, next)`).

**Example**
```python
except Exception as e:
    return jsonify({"error": str(e)}), 500
```

**Why it matters:** internal details (SQL, paths) leak to clients, real errors are swallowed, and the same try/except is copied everywhere.

---

### AP-12 — Missing Transaction / Inconsistent Writes
- Severity: MEDIUM
- Fix: PB-12

**Detection signals**
- Several dependent `INSERT`/`UPDATE`/`DELETE` statements (order + items + stock; enrollment + payment + audit) without `BEGIN`/`COMMIT`/`ROLLBACK` or an ORM session/transaction block.
- Deletes of a parent row without deleting or cascading its children (orphans).
- Early `return` in the middle of a multi-write operation.

**Example**
```javascript
db.run("INSERT INTO enrollments ...", () => db.run("INSERT INTO payments ...", () => ...));
```

**Why it matters:** a failure in the middle leaves the data inconsistent (payments without enrollment, orders without items, orphan rows).

---

### AP-13 — Duplicated Logic
- Severity: MEDIUM
- Fix: PB-13

**Detection signals**
- The same rule written in several places (e.g. an "is overdue" condition copied into many handlers while a model method exists).
- Copy-pasted row-to-dict mappings, validation blocks or status lists.
- Two endpoints computing the same statistics independently.

**Example**
```python
if t.due_date and t.due_date < now and t.status not in ("done", "cancelled"): overdue = True   # repeated 6 times
```

**Why it matters:** copies diverge; a fix applied in one place leaves the bug in the others.

---

### AP-14 — Print / console.log as Logging
- Severity: LOW
- Fix: PB-14

**Detection signals**
- `print(` in application code (outside CLI scripts), `console.log(` in request handlers, banners like `print("=" * 50)`.

**Example**
```python
print("Product created with ID: " + str(id))
```

**Why it matters:** no levels, no timestamps, no way to silence or route logs; personal data ends up in stdout.

---

### AP-15 — Magic Numbers / Strings
- Severity: LOW
- Fix: PB-15

**Detection signals**
- Numeric literals in business rules (`if revenue > 10000: discount = revenue * 0.1`), status/role/category lists written inline, literal ports, loop counts, string states (`"PAID"`, `"DENIED"`) compared in several places.
- Constants that exist but are not used.

**Example**
```javascript
let status = card.startsWith("4") ? "PAID" : "DENIED";
```

**Why it matters:** the meaning of the value is lost and changing a rule requires finding every copy.

---

### AP-16 — Poor Naming
- Severity: LOW
- Fix: PB-16

**Detection signals**
- One- or two-letter variables for domain data (`u`, `e`, `p`, `cc`, `cid`), cryptic request fields (`usr`, `eml`, `pwd`), misleading names (`badCrypto`, `processData`, `data2`, `cursor3`).

**Example**
```javascript
let u = req.body.usr; let e = req.body.eml; let cc = req.body.card;
```

**Why it matters:** readers must reverse-engineer the meaning; mistakes hide behind ambiguous names.

---

### AP-17 — Unused Imports / Dead Code
- Severity: LOW
- Fix: PB-17

**Detection signals**
- Python: imported names never referenced (`import os, sys, json` with no `os.`/`sys.`/`json.`), helper functions never called, constants never read.
- JavaScript: `require`/`import` bindings never used, exported values nobody imports.

**Example**
```python
import json, os, sys, time   # none of them used
```

**Why it matters:** noise hides the real dependencies and misleads readers about what the module does.

---

### AP-18 — Weak Password Hashing
- Severity: CRITICAL
- Fix: PB-18

**Detection signals**
- Passwords stored as plain text (`INSERT INTO users (..., password) VALUES (..., senha)` with the raw value; login comparing `password = '<input>'` in SQL).
- Fast or broken hashes: `hashlib.md5(`, `hashlib.sha1(`, `crypto.createHash('md5'|'sha1')`, unsalted `sha256`.
- Home-made "crypto": base64, string repetition, truncation (`Buffer.from(pwd).toString('base64')`).

**Example**
```python
self.password = hashlib.md5(pwd.encode()).hexdigest()
```

**Why it matters:** a database leak reveals every password (rainbow tables crack MD5 instantly); users reuse passwords elsewhere.

---

### AP-19 — Debug Mode in Production
- Severity: HIGH
- Fix: PB-19

**Detection signals**
- `app.run(debug=True)`, `app.config["DEBUG"] = True`, `DEBUG = True` hardcoded, especially with `host="0.0.0.0"`.
- Express: stack traces sent to clients, `NODE_ENV` never checked.

**Example**
```python
app.run(host="0.0.0.0", port=5000, debug=True)
```

**Why it matters:** the Werkzeug debugger allows remote code execution from any error page; stack traces leak internals.

---

### AP-20 — Deprecated APIs
- Severity: MEDIUM
- Fix: PB-20

**Detection signals:** grep for the deprecated column below and confirm the installed version is affected.

| Deprecated | Since / status | Modern replacement |
|---|---|---|
| SQLAlchemy `Model.query.get(id)` / `Query.get()` | Legacy in SQLAlchemy 2.0 (`LegacyAPIWarning`) | `db.session.get(Model, id)` |
| Python `datetime.utcnow()` / `datetime.utcfromtimestamp()` | Deprecated in Python 3.12 | `datetime.now(timezone.utc)` / `datetime.fromtimestamp(ts, timezone.utc)` |
| Python `hashlib.md5` / `sha1` for passwords | Insecure for passwords (OWASP) | `werkzeug.security.generate_password_hash` / `check_password_hash`, `bcrypt`, `hashlib.scrypt` |
| Flask `@app.before_first_request` | Removed in Flask 2.3 | Run the setup inside the app factory under `with app.app_context():` |
| Flask `flask.json.JSONEncoder` / `app.json_encoder` | Removed in Flask 2.3 | `app.json = CustomJSONProvider(app)` |
| SQLAlchemy `engine.execute()` / string SQL to `session.execute()` | Removed in SQLAlchemy 2.0 | `with engine.connect() as conn: conn.execute(text(...), params)` |
| Python `sqlite3` default datetime adapters | Deprecated in Python 3.12 | Store ISO strings explicitly or register adapters |
| Node `new Buffer(x)` | Deprecated since Node 6 (DEP0005) | `Buffer.from(x)` / `Buffer.alloc(n)` |
| Express `bodyParser()` / `body-parser` standalone for JSON | Bundled since Express 4.16 | `express.json()` / `express.urlencoded({ extended: true })` |
| Express `req.param(name)` | Deprecated in Express 4, removed in 5 | `req.params`, `req.query` or `req.body` explicitly |
| Express `res.send(status, body)` / `res.json(status, body)` | Removed in Express 5 | `res.status(status).send(body)` |
| Node `url.parse()` | Legacy (DEP0169) | `new URL(input, base)` |
| Node `crypto.createCipher()` | Removed (DEP0106) | `crypto.createCipheriv()` |
| `sqlite3` npm callback API nested by hand | Not deprecated, but superseded | Promisified helpers or `node:sqlite` / `better-sqlite3` |

**Example**
```python
task = Task.query.get(task_id)
created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

**Why it matters:** deprecated APIs emit warnings today and break on the next major upgrade; some (MD5 passwords) are already insecure.

---

### AP-21 — Callback Pyramid / Deep Nesting
- Severity: MEDIUM
- Fix: PB-21

**Detection signals**
- JavaScript: three or more nested callbacks (`db.get(..., (err, a) => { db.run(..., function (err) { db.run(... ) }) })`), manual counters to know when parallel callbacks finished (`pending--; if (pending === 0) res.json(...)`).
- Any language: `if` nesting four or more levels deep, `if cond: return True else: return False` chains.

**Example**
```javascript
courses.forEach(c => db.all(..., (err, rows) => rows.forEach(r => db.get(..., (err, u) => { if (--pending === 0) res.json(report) }))));
```

**Why it matters:** control flow and error handling become impossible to follow; it is the usual hiding place for unhandled errors and races.

---

### AP-22 — Missing Authentication / Authorization
- Severity: HIGH
- Fix: PB-04

**Detection signals**
- Destructive or private routes (`DELETE /users/:id`, user lists with e-mails, reports) with no auth check.
- Fake tokens (`'fake-jwt-token-' + id`) that nothing verifies; role fields (`is_admin()`) never checked.

**Example**
```python
return jsonify({"token": "fake-jwt-token-" + str(user.id)})
```

**Why it matters:** any client can impersonate users or delete data; roles exist on paper only.
