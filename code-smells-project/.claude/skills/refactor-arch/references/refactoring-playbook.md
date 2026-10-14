# Refactoring Playbook

Knowledge for **Phase 3**: one transformation pattern per anti-pattern of `references/anti-patterns.md`, with steps and before/after code. Python examples use Flask; JavaScript examples use Express with the `sqlite3` driver. Adapt names to the project, keep the behavior-preservation rules of `references/mvc-guidelines.md`.

| Pattern | Fixes |
|---|---|
| PB-01 Extract configuration to the environment | AP-01 |
| PB-02 Parameterized queries | AP-02 |
| PB-03 Split the god class into MVC layers | AP-03 |
| PB-04 Admin-token guard | AP-04, AP-22 |
| PB-05 Safe serializers and redacted logs | AP-05 |
| PB-06 Move business logic out of controllers/routes | AP-06 |
| PB-07 Replace mutable global state | AP-07 |
| PB-08 App factory and dependency injection | AP-08 |
| PB-09 Remove N+1 queries | AP-09 |
| PB-10 Validate input at the boundary | AP-10 |
| PB-11 Centralized error handler | AP-11 |
| PB-12 Wrap multi-write operations in a transaction | AP-12 |
| PB-13 Extract the duplicated rule | AP-13 |
| PB-14 Logging instead of print/console.log | AP-14 |
| PB-15 Named constants | AP-15 |
| PB-16 Intention-revealing names | AP-16 |
| PB-17 Remove unused imports and dead code | AP-17 |
| PB-18 Real password hashing with legacy migration | AP-18 |
| PB-19 Debug flag from configuration | AP-19 |
| PB-20 Replace deprecated APIs | AP-20 |
| PB-21 Flatten callbacks with async/await | AP-21 |
| PB-22 Smoke test template | validation of every pattern |

---

### PB-01 — Extract configuration to the environment
Fixes: AP-01

1. Create `config/settings.*` reading every setting from the environment, with the original value as default for non-secrets (port, database path).
2. Secrets get no literal default: generate an ephemeral value and warn when missing.
3. Replace every literal in the code with the setting; add `.env.example`.

**Before**
```python
app = Flask(__name__)
app.config["SECRET_KEY"] = "my-super-secret-123"
app.run(host="0.0.0.0", port=5000, debug=True)
```

**After**
```python
# config/settings.py
import logging
import os
import secrets


class Settings:
    def __init__(self, env=os.environ):
        self.host = env.get("HOST", "0.0.0.0")
        self.port = int(env.get("PORT", "5000"))
        self.debug = env.get("FLASK_DEBUG", "0") == "1"
        self.database_path = env.get("DATABASE_PATH", "app.db")
        self.admin_token = env.get("ADMIN_TOKEN", "")
        self.secret_key = env.get("SECRET_KEY") or self._ephemeral("SECRET_KEY")

    @staticmethod
    def _ephemeral(name):
        logging.getLogger(__name__).warning("%s is not set; using an ephemeral value", name)
        return secrets.token_hex(32)
```

**Before**
```javascript
const config = { dbPass: "prod_password_123", paymentGatewayKey: "pk_live_123", port: 3000 };
```

**After**
```javascript
// src/config/settings.js
const crypto = require('node:crypto');

function secret(name) {
  if (process.env[name]) return process.env[name];
  console.warn(`${name} is not set; using an ephemeral value`);
  return crypto.randomBytes(32).toString('hex');
}

module.exports = {
  port: Number(process.env.PORT || 3000),
  databasePath: process.env.DATABASE_PATH || ':memory:',
  paymentGatewayKey: secret('PAYMENT_GATEWAY_KEY'),
  adminToken: process.env.ADMIN_TOKEN || '',
};
```

---

### PB-02 — Parameterized queries
Fixes: AP-02

1. Replace every concatenated/interpolated value with the driver placeholder (`?` for sqlite3, `%s` for psycopg2, `:name` for SQLAlchemy `text()`).
2. For dynamic filters, build the SQL from fixed fragments and append values to a parameter list.
3. For `LIKE`, put the wildcards in the parameter, not in the SQL.

**Before**
```python
cursor.execute("SELECT * FROM users WHERE email = '" + email + "' AND password = '" + pwd + "'")

query = "SELECT * FROM products WHERE 1=1"
if term:
    query += " AND name LIKE '%" + term + "%'"
```

**After**
```python
cursor.execute("SELECT * FROM users WHERE email = ?", (email,))

clauses, params = [], []
if term:
    clauses.append("(name LIKE ? OR description LIKE ?)")
    params += [f"%{term}%", f"%{term}%"]
sql = "SELECT * FROM products" + (" WHERE " + " AND ".join(clauses) if clauses else "")
cursor.execute(sql, params)
```

**Before**
```javascript
db.all(`SELECT * FROM courses WHERE id = ${req.params.id}`, cb);
```

**After**
```javascript
db.all('SELECT * FROM courses WHERE id = ?', [req.params.id], cb);
```

---

### PB-03 — Split the god class into MVC layers
Fixes: AP-03

1. List every responsibility of the god class/file (schema, seed, data access, rules, routes, formatting, side effects).
2. Move schema + seed to the database module, data access to one model per entity, the use-case flow to one controller per domain, HTTP mapping to routes, side effects to services.
3. Wire everything in the composition root; delete the god file.

**Before**
```javascript
class AppManager {
  constructor() { this.db = new sqlite3.Database(':memory:'); }
  initDb() { this.db.run('CREATE TABLE courses (...)'); }
  setupRoutes(app) {
    app.post('/api/checkout', (req, res) => { /* SQL + payment + enrollment + response */ });
  }
}
```

**After**
```javascript
// src/app.js — composition root
function createApp(config) {
  const db = createDatabase(config.databasePath);           // database/connection.js
  const courseModel = new CourseModel(db);                   // models/
  const enrollmentModel = new EnrollmentModel(db);
  const paymentService = new PaymentService(config);         // services/
  const checkoutController = new CheckoutController({ courseModel, enrollmentModel, paymentService });
  const app = express();
  app.use(express.json());
  app.use('/api', checkoutRoutes(checkoutController));       // routes/
  app.use(errorHandler);                                     // middlewares/
  return { app, db };
}
```

**Before**
```python
# models.py — every domain, SQL, rules and formatting in one module
def criar_pedido(usuario_id, itens): ...
def relatorio_vendas(): ...
def login_usuario(email, senha): ...
```

**After**
```python
# models/order_model.py      -> data access for orders and items
# models/user_model.py       -> data access for users
# controllers/order_controller.py -> create order flow (validate, check stock, persist, notify)
# controllers/report_controller.py -> sales report
# views/order_routes.py      -> Blueprint mapping /pedidos to the controller
```

---

### PB-04 — Admin-token guard
Fixes: AP-04, AP-22

1. Add `ADMIN_TOKEN` to the config (no default).
2. Create an auth middleware/decorator comparing the `X-Admin-Token` header with a constant-time comparison; `401` when missing, `403` when wrong or when no token is configured.
3. Apply it to dangerous/private routes. Narrow arbitrary execution to the safe subset (single read-only `SELECT`).

**Before**
```python
@app.route("/admin/query", methods=["POST"])
def run_query():
    cursor.execute(request.get_json()["sql"])
```

**After**
```python
# middlewares/auth.py
import hmac
from functools import wraps

from flask import current_app, request

from middlewares.errors import ForbiddenError, UnauthorizedError


def require_admin_token(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        expected = current_app.config.get("ADMIN_TOKEN", "")
        received = request.headers.get("X-Admin-Token", "")
        if not received:
            raise UnauthorizedError("Token de administrador ausente")
        if not expected or not hmac.compare_digest(received, expected):
            raise ForbiddenError("Token de administrador inválido")
        return view(*args, **kwargs)
    return wrapper


# controllers/admin_controller.py
def run_read_only_query(sql):
    statement = sql.strip().rstrip(";")
    if not statement.upper().startswith("SELECT") or ";" in statement:
        raise ValidationError("Apenas uma consulta SELECT é permitida")
    return admin_model.select(statement)
```

**Before**
```javascript
app.delete('/api/users/:id', (req, res) => { db.run('DELETE FROM users WHERE id = ?', [req.params.id]); });
```

**After**
```javascript
// src/middlewares/adminAuth.js
const crypto = require('node:crypto');

function adminAuth(config) {
  return (req, res, next) => {
    const received = req.get('X-Admin-Token') || '';
    if (!received) return res.status(401).json({ error: 'Admin token missing' });
    const expected = config.adminToken || '';
    const ok = expected.length === received.length &&
      crypto.timingSafeEqual(Buffer.from(received), Buffer.from(expected));
    if (!ok) return res.status(403).json({ error: 'Invalid admin token' });
    next();
  };
}

router.delete('/users/:id', adminAuth(config), asyncHandler(controller.deleteUser));
```

---

### PB-05 — Safe serializers and redacted logs
Fixes: AP-05

1. Give each model one public serializer that whitelists fields; never include password/hash/secret.
2. Remove configuration values from responses (health checks report status only).
3. Never log card numbers, passwords or keys; mask them (`**** 4444`).

**Before**
```python
def to_dict(self):
    return {"id": self.id, "email": self.email, "password": self.password}

return jsonify({"status": "ok", "secret_key": app.config["SECRET_KEY"], "db_path": "app.db"})
```

**After**
```python
PUBLIC_FIELDS = ("id", "name", "email", "role", "active", "created_at")

def to_dict(self):
    return {field: getattr(self, field) for field in PUBLIC_FIELDS}

return jsonify({"status": "ok", "database": "connected", "counts": counts})
```

**Before**
```javascript
console.log(`Processing card ${card} with key ${config.paymentGatewayKey}`);
```

**After**
```javascript
const masked = `**** ${String(card).slice(-4)}`;
logger.info(`Processing payment for card ${masked}`);
```

---

### PB-06 — Move business logic out of controllers/routes
Fixes: AP-06

1. Identify domain rules in the handler (calculations, state transitions, eligibility, side effects).
2. Move data-only rules to the model (methods or pure functions) and side effects to services.
3. Leave the controller with the flow: validate → call model/services → return result. Leave the route with HTTP only.

**Before**
```python
@app.route("/orders", methods=["POST"])
def create_order():
    data = request.get_json()
    total = 0
    for item in data["items"]:
        product = cursor.execute("SELECT * FROM products WHERE id = ?", (item["product_id"],)).fetchone()
        if product["stock"] < item["quantity"]:
            return jsonify({"error": "Insufficient stock"}), 400
        total += product["price"] * item["quantity"]
    print("SENDING EMAIL ...")
```

**After**
```python
# views/order_routes.py
@bp.post("/orders")
def create_order():
    result = order_controller.create_order(request.get_json(silent=True))
    return jsonify({"data": result, "success": True}), 201

# controllers/order_controller.py
def create_order(payload):
    order_input = validate_order(payload)                       # raises ValidationError
    products = product_model.get_many([i.product_id for i in order_input.items])
    order = order_model.create(order_input, products)          # stock check + total inside the model/transaction
    notification_service.order_created(order)
    return order
```

**Before**
```javascript
app.post('/api/checkout', (req, res) => {
  let status = req.body.card.startsWith('4') ? 'PAID' : 'DENIED';
  if (status === 'DENIED') return res.status(400).send('Payment denied');
  // ... SQL inserts ...
});
```

**After**
```javascript
// src/services/paymentService.js
class PaymentService {
  charge({ cardNumber }) {
    return cardNumber.startsWith(APPROVED_CARD_PREFIX) ? PaymentStatus.PAID : PaymentStatus.DENIED;
  }
}

// src/controllers/checkoutController.js
async checkout(input) {
  const course = await this.courseModel.findActive(input.courseId);
  if (!course) throw new NotFoundError('Curso não encontrado');
  if (this.paymentService.charge(input) === PaymentStatus.DENIED) throw new PaymentDeniedError('Pagamento recusado');
  return this.enrollmentModel.enrollWithPayment(input, course);
}
```

---

### PB-07 — Replace mutable global state
Fixes: AP-07

1. Move the state into an object with a clear owner and lifecycle (a cache class, a connection per request/app).
2. Create it in the composition root and inject it where needed.
3. For database connections: one connection per request (Flask `g` + teardown) or a pool/app-scoped object, never a mutable module global.

**Before**
```python
db_connection = None

def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect("app.db", check_same_thread=False)
    return db_connection
```

**After**
```python
# database.py
import sqlite3

from flask import current_app, g


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE_PATH"])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

# app.py: app.teardown_appcontext(close_db)
```

**Before**
```javascript
let globalCache = {};
function logAndCache(key, data) { globalCache[key] = data; }
module.exports = { globalCache, logAndCache };
```

**After**
```javascript
// src/services/cache.js
class MemoryCache {
  #entries = new Map();
  set(key, value) { this.#entries.set(key, value); }
  get(key) { return this.#entries.get(key); }
}
module.exports = { MemoryCache };

// src/app.js: const cache = new MemoryCache(); new CheckoutController({ ..., cache });
```

---

### PB-08 — App factory and dependency injection
Fixes: AP-08

1. Create `create_app(settings)` / `createApp(config)` that builds and wires every dependency.
2. Pass dependencies through constructors or function parameters (or Flask `current_app.extensions` / blueprint factories), never by importing concrete singletons inside the layers.
3. Start the server only under `if __name__ == "__main__"` / `require.main === module`.

**Before**
```python
app = Flask(__name__)
app.register_blueprint(task_bp)
with app.app_context():
    db.create_all()
if __name__ == "__main__":
    app.run(debug=True)
```

**After**
```python
def create_app(settings=None):
    settings = settings or Settings()
    app = Flask(__name__)
    app.config.update(SQLALCHEMY_DATABASE_URI=settings.database_url, SECRET_KEY=settings.secret_key,
                      ADMIN_TOKEN=settings.admin_token)
    db.init_app(app)
    register_error_handlers(app)
    for blueprint in (task_bp, user_bp, report_bp, category_bp):
        app.register_blueprint(blueprint)
    with app.app_context():
        db.create_all()
    return app


if __name__ == "__main__":
    settings = Settings()
    create_app(settings).run(host=settings.host, port=settings.port, debug=settings.debug)
```

**Before**
```javascript
const manager = new AppManager();
manager.initDb();
manager.setupRoutes(app);
app.listen(3000);
```

**After**
```javascript
function createApp(config) {
  const db = createDatabase(config.databasePath);
  const controllers = buildControllers({ db, config });
  const app = express();
  app.use(express.json());
  app.use('/api', buildRoutes(controllers, config));
  app.use(errorHandler);
  return { app, db };
}

if (require.main === module) {
  const { app } = createApp(config);
  app.listen(config.port, () => logger.info(`Listening on port ${config.port}`));
}

module.exports = { createApp };
```

---

### PB-09 — Remove N+1 queries
Fixes: AP-09

1. Replace the query-per-row loop with one query using `JOIN`/`IN (...)`, an aggregate (`GROUP BY`), or ORM eager loading.
2. Group the rows in memory to rebuild the nested response with the **same shape** as before.

**Before**
```python
for order in orders:
    items = cursor.execute("SELECT * FROM order_items WHERE order_id = " + str(order["id"])).fetchall()
    for item in items:
        product = cursor.execute("SELECT name FROM products WHERE id = " + str(item["product_id"])).fetchone()
```

**After**
```python
rows = cursor.execute(
    """SELECT i.order_id, i.product_id, i.quantity, i.unit_price, p.name AS product_name
       FROM order_items i LEFT JOIN products p ON p.id = i.product_id
       WHERE i.order_id IN (%s)""" % ",".join("?" * len(order_ids)),
    order_ids,
).fetchall()
items_by_order = defaultdict(list)
for row in rows:
    items_by_order[row["order_id"]].append({**dict(row), "product_name": row["product_name"] or "Unknown"})
```

```python
# SQLAlchemy: eager load relationships and aggregate counts in one query
tasks = Task.query.options(joinedload(Task.user), joinedload(Task.category)).all()
counts = dict(db.session.query(Task.category_id, func.count(Task.id)).group_by(Task.category_id).all())
```

**Before**
```javascript
courses.forEach(c => db.all('SELECT * FROM enrollments WHERE course_id = ?', [c.id], (err, enrollments) => {
  enrollments.forEach(e => db.get('SELECT name FROM users WHERE id = ?', [e.user_id], /* ... */));
}));
```

**After**
```javascript
const rows = await db.all(`
  SELECT c.id AS courseId, c.title, u.name AS student, p.amount, p.status
  FROM courses c
  LEFT JOIN enrollments e ON e.course_id = c.id
  LEFT JOIN users u ON u.id = e.user_id
  LEFT JOIN payments p ON p.enrollment_id = e.id
  ORDER BY c.id, e.id`);
// group rows by courseId to rebuild [{ course, revenue, students: [...] }]
```

---

### PB-10 — Validate input at the boundary
Fixes: AP-10

1. Create one validation function/schema per input (create and update share the rules; update allows partial fields).
2. Check presence, type, range, format and enums; raise a `ValidationError` with a clear message mapped to `400`.
3. Use the validators/constants that already exist in the project instead of re-writing them.

**Before**
```python
data = request.get_json()
if data["priority"] < 1 or data["priority"] > 5:
    return jsonify({"error": "Invalid priority"}), 400
```

**After**
```python
# controllers/validators.py
def require_json_object(payload):
    if not isinstance(payload, dict):
        raise ValidationError("Dados inválidos")
    return payload


def validate_priority(value):
    if isinstance(value, bool) or not isinstance(value, int) or not MIN_PRIORITY <= value <= MAX_PRIORITY:
        raise ValidationError(f"Prioridade deve ser entre {MIN_PRIORITY} e {MAX_PRIORITY}")
    return value
```

**Before**
```javascript
if (!u || !e || !cid || !cc) return res.status(400).send('Bad Request');
```

**After**
```javascript
// src/controllers/validators.js
function validateCheckout(body) {
  const { usr: name, eml: email, pwd: password, c_id: courseId, card: cardNumber } = body || {};
  if (!name || !email || !courseId || !cardNumber) throw new ValidationError('Bad Request');
  return { name, email, password, courseId: Number(courseId), cardNumber: String(cardNumber) };
}
```

---

### PB-11 — Centralized error handler
Fixes: AP-11

1. Define domain errors with a status code (`ValidationError` 400, `UnauthorizedError` 401, `ForbiddenError` 403, `NotFoundError` 404, `ConflictError` 409).
2. Register one error handler: domain errors → their status and message; anything else → log the stack trace and return a generic 500 without internal details.
3. Remove the per-handler try/except blocks and bare `except:`.

**Before**
```python
def list_products():
    try:
        ...
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

**After**
```python
# middlewares/error_handler.py
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


class AppError(Exception):
    status_code = 500

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class ValidationError(AppError):
    status_code = 400


class NotFoundError(AppError):
    status_code = 404


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(error):
        return jsonify({"erro": error.message, "sucesso": False}), error.status_code

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        return jsonify({"erro": error.description}), error.code

    @app.errorhandler(Exception)
    def handle_unexpected(error):
        logger.exception("Unhandled error")
        return jsonify({"erro": "Erro interno do servidor"}), 500
```

Keep the error key the project already uses (`erro`, `error`) so response bodies keep their shape.

**Before**
```javascript
db.get(sql, params, (err, row) => {
  if (err) return res.status(500).send(err.message);
});
```

**After**
```javascript
// src/middlewares/errorHandler.js
function errorHandler(err, req, res, next) {
  if (err instanceof AppError) return res.status(err.statusCode).send(err.message);
  logger.error(err.stack);
  return res.status(500).send('Internal Server Error');
}

// src/middlewares/asyncHandler.js
const asyncHandler = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);
```

Keep the response type the project uses (plain text `send` vs `json`) for each route.

---

### PB-12 — Wrap multi-write operations in a transaction
Fixes: AP-12

1. Group dependent writes in one transaction; roll back on any error.
2. For parent deletes, delete or cascade the children in the same transaction.

**Before**
```python
cursor.execute("INSERT INTO orders ...")
for item in items:
    cursor.execute("INSERT INTO order_items ...")
    cursor.execute("UPDATE products SET stock = stock - ? WHERE id = ?", ...)
db.commit()
```

**After**
```python
with db:                       # sqlite3: commits on success, rolls back on exception
    cursor = db.execute("INSERT INTO orders (user_id, status, total) VALUES (?, ?, ?)", (user_id, PENDING, total))
    order_id = cursor.lastrowid
    db.executemany("INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
                   [(order_id, i.product_id, i.quantity, prices[i.product_id]) for i in items])
    db.executemany("UPDATE products SET stock = stock - ? WHERE id = ?",
                   [(i.quantity, i.product_id) for i in items])
```

**Before**
```javascript
db.run('INSERT INTO enrollments ...', function () {
  db.run('INSERT INTO payments ...', function () { db.run('INSERT INTO audit_logs ...'); });
});
```

**After**
```javascript
async function inTransaction(db, work) {
  await db.run('BEGIN');
  try {
    const result = await work();
    await db.run('COMMIT');
    return result;
  } catch (error) {
    await db.run('ROLLBACK');
    throw error;
  }
}

const enrollmentId = await inTransaction(db, async () => {
  const { lastID } = await db.run('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [userId, courseId]);
  await db.run('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)', [lastID, price, status]);
  await db.run("INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))", [action]);
  return lastID;
});
```

---

### PB-13 — Extract the duplicated rule
Fixes: AP-13

1. Find every copy of the rule; pick (or create) one home in the model/domain module.
2. Replace every copy with a call; delete the copies.

**Before**
```python
if t.due_date:
    if t.due_date < datetime.utcnow():
        if t.status != "done" and t.status != "cancelled":
            overdue = True
```

**After**
```python
# models/task.py
def is_overdue(self, now=None):
    now = now or utc_now()
    return bool(self.due_date) and self.due_date < now and self.status not in CLOSED_STATUSES

# everywhere else
data["overdue"] = task.is_overdue()
```

**Before**
```javascript
const a = { id: row.id, title: row.title, price: row.price };   // copied in three handlers
```

**After**
```javascript
// src/models/courseModel.js
static toPublic(row) { return { id: row.id, title: row.title, price: row.price }; }
```

---

### PB-14 — Logging instead of print/console.log
Fixes: AP-14

1. Configure logging once in the composition root (level from config).
2. Replace prints with `logger.info/warning/error`; drop banners and personal data.

**Before**
```python
print("Product created with ID: " + str(id))
```

**After**
```python
logger = logging.getLogger(__name__)
logger.info("Product created: id=%s", product_id)
```

**Before**
```javascript
console.log(`[LOG] Saving to cache: ${key}`);
```

**After**
```javascript
// src/utils/logger.js — thin wrapper so the transport can change in one place
const logger = {
  info: (msg) => console.info(`[INFO] ${new Date().toISOString()} ${msg}`),
  error: (msg) => console.error(`[ERROR] ${new Date().toISOString()} ${msg}`),
};
logger.info(`Cache entry saved: ${key}`);
```

---

### PB-15 — Named constants
Fixes: AP-15

1. Move literals with business meaning to named constants (or enums) in the domain module that owns them.
2. Reuse constants that already exist in the project.

**Before**
```python
if revenue > 10000:
    discount = revenue * 0.1
elif revenue > 5000:
    discount = revenue * 0.05
```

**After**
```python
# models/report_model.py
DISCOUNT_TIERS = ((10000, 0.10), (5000, 0.05), (1000, 0.02))   # (minimum revenue, rate)


def discount_for(revenue):
    return next((revenue * rate for minimum, rate in DISCOUNT_TIERS if revenue > minimum), 0)
```

**Before**
```javascript
if (payment.status === 'PAID') revenue += payment.amount;
```

**After**
```javascript
const PaymentStatus = Object.freeze({ PAID: 'PAID', DENIED: 'DENIED' });
if (payment.status === PaymentStatus.PAID) revenue += payment.amount;
```

---

### PB-16 — Intention-revealing names
Fixes: AP-16

1. Rename internal variables, functions and classes to say what they hold or do.
2. Keep the public request/response field names (contract); map them once at the boundary.

**Before**
```javascript
let u = req.body.usr; let e = req.body.eml; let p = req.body.pwd; let cc = req.body.card;
```

**After**
```javascript
const { usr: name, eml: email, pwd: password, card: cardNumber } = req.body;
```

**Before**
```python
cursor3 = db.cursor()
prod = cursor3.fetchone()
```

**After**
```python
product = db.execute("SELECT name FROM products WHERE id = ?", (product_id,)).fetchone()
```

---

### PB-17 — Remove unused imports and dead code
Fixes: AP-17

1. Delete imports with no reference and helpers nobody calls (after confirming with a project-wide search).
2. Either wire an unused-but-useful helper (validator, constant) where the logic is duplicated, or delete it.

**Before**
```python
import os, sys, json, datetime
from utils.helpers import format_date, calculate_percentage   # never used
```

**After**
```python
from datetime import datetime, timezone
```

**Before**
```javascript
const { config, logAndCache, badCrypto, totalRevenue } = require('./utils');   // totalRevenue unused
```

**After**
```javascript
const config = require('./config/settings');
```

---

### PB-18 — Real password hashing with legacy migration
Fixes: AP-18

1. Hash with a slow, salted algorithm: Python `werkzeug.security` (ships with Flask, no new dependency) or `hashlib.scrypt`; Node `crypto.scrypt` + random salt + `timingSafeEqual`.
2. Hash in the seed so seed logins keep working with the same plain passwords.
3. Legacy data: when the stored value is not in the new format, verify it with the legacy rule once and re-hash on success.
4. Never select by `password = ?` in SQL; load by e-mail and verify in code.

**Before**
```python
self.password = hashlib.md5(pwd.encode()).hexdigest()

def check_password(self, pwd):
    return self.password == hashlib.md5(pwd.encode()).hexdigest()
```

**After**
```python
import hashlib
import hmac

from werkzeug.security import check_password_hash, generate_password_hash

HASH_PREFIXES = ("scrypt:", "pbkdf2:")


def set_password(self, raw):
    self.password = generate_password_hash(raw)


def check_password(self, raw):
    if self.password.startswith(HASH_PREFIXES):
        return check_password_hash(self.password, raw)
    legacy = hashlib.md5(raw.encode()).hexdigest()          # legacy rows only, upgraded on success
    if hmac.compare_digest(self.password, legacy):
        self.set_password(raw)
        return True
    return False
```

**Before**
```javascript
function badCrypto(pwd) {
  let hash = '';
  for (let i = 0; i < 10000; i++) hash += Buffer.from(pwd).toString('base64').substring(0, 2);
  return hash.substring(0, 10);
}
```

**After**
```javascript
// src/services/passwordHasher.js
const crypto = require('node:crypto');
const KEY_LENGTH = 64;

function hashPassword(password) {
  const salt = crypto.randomBytes(16).toString('hex');
  const derived = crypto.scryptSync(password, salt, KEY_LENGTH).toString('hex');
  return `scrypt$${salt}$${derived}`;
}

function verifyPassword(password, stored) {
  const [scheme, salt, expected] = String(stored).split('$');
  if (scheme !== 'scrypt') return false;
  const derived = crypto.scryptSync(password, salt, KEY_LENGTH);
  return crypto.timingSafeEqual(derived, Buffer.from(expected, 'hex'));
}

module.exports = { hashPassword, verifyPassword };
```

---

### PB-19 — Debug flag from configuration
Fixes: AP-19

1. Read debug from the environment, default off.
2. Never send stack traces to clients (PB-11).

**Before**
```python
app.config["DEBUG"] = True
app.run(host="0.0.0.0", port=5000, debug=True)
```

**After**
```python
settings = Settings()
app.run(host=settings.host, port=settings.port, debug=settings.debug)   # FLASK_DEBUG=1 to enable
```

**Before**
```javascript
res.status(500).send(err.stack);
```

**After**
```javascript
const body = config.env === 'development' ? err.stack : 'Internal Server Error';
res.status(500).send(body);
```

---

### PB-20 — Replace deprecated APIs
Fixes: AP-20

1. Replace each deprecated call with the modern equivalent from the catalog table.
2. Keep stored values compatible (e.g. naive UTC datetimes in SQLite: use a helper that returns `datetime.now(timezone.utc).replace(tzinfo=None)` when the column is naive).

**Before**
```python
task = Task.query.get(task_id)
created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

**After**
```python
# models/base.py
from datetime import datetime, timezone


def utc_now():
    # Naive UTC keeps the stored format of existing rows
    return datetime.now(timezone.utc).replace(tzinfo=None)

task = db.session.get(Task, task_id)
created_at = db.Column(db.DateTime, default=utc_now)
```

**Before**
```javascript
const encoded = new Buffer(password).toString('base64');
app.use(bodyParser.json());
const id = req.param('id');
```

**After**
```javascript
const encoded = Buffer.from(password).toString('base64');
app.use(express.json());
const id = req.params.id;
```

---

### PB-21 — Flatten callbacks with async/await
Fixes: AP-21

1. Promisify the callback API once (database helper).
2. Rewrite nested callbacks as sequential `await`s inside `try/catch` (or let `asyncHandler` forward errors).
3. Replace manual counters with `Promise.all` or a single query (PB-09).

**Before**
```javascript
db.get('SELECT * FROM courses WHERE id = ?', [id], (err, course) => {
  db.get('SELECT id FROM users WHERE email = ?', [email], (err, user) => {
    db.run('INSERT INTO enrollments ...', function (err) { /* ... */ });
  });
});
```

**After**
```javascript
// src/database/connection.js
function promisify(db) {
  return {
    get: (sql, params = []) => new Promise((ok, fail) => db.get(sql, params, (e, row) => (e ? fail(e) : ok(row)))),
    all: (sql, params = []) => new Promise((ok, fail) => db.all(sql, params, (e, rows) => (e ? fail(e) : ok(rows)))),
    run: (sql, params = []) => new Promise((ok, fail) => db.run(sql, params, function (e) { return e ? fail(e) : ok(this); })),
  };
}

const course = await db.get('SELECT * FROM courses WHERE id = ?', [id]);
const user = await db.get('SELECT id FROM users WHERE email = ?', [email]);
```

**Before**
```python
def is_overdue(self):
    if self.due_date:
        if self.due_date < datetime.utcnow():
            if self.status != "done" and self.status != "cancelled":
                return True
            else:
                return False
        else:
            return False
    else:
        return False
```

**After**
```python
def is_overdue(self, now=None):
    now = now or utc_now()
    return bool(self.due_date) and self.due_date < now and self.status not in CLOSED_STATUSES
```

---

### PB-22 — Smoke test template
Fixes: validation of every pattern (Phase 3, Step 4)

1. Use only the standard library / runtime built-ins.
2. Boot the app as a subprocess on a free port with a temporary database and `ADMIN_TOKEN` set; run the seed first when the project has one.
3. Call every endpoint of the inventory with the baseline requests; read-only first, destructive last; assert the status codes.
4. Always stop the server.

**Before**
```python
# no automated check: endpoints were tested by hand, if at all
```

**After**
```python
# tests/smoke_test.py
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADMIN_TOKEN = "smoke-test-token"


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def call(base, method, path, body=None, headers=None):
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(base + path, data=data, method=method,
                                     headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()


def wait_until_up(base, attempts=50):
    for _ in range(attempts):
        try:
            urllib.request.urlopen(base + "/", timeout=1)
            return
        except urllib.error.HTTPError:
            return                      # any HTTP answer means the server is up
        except OSError:
            time.sleep(0.2)
    raise RuntimeError("server did not start")


def main():
    port = free_port()
    workdir = tempfile.mkdtemp()
    env = {**os.environ, "PORT": str(port), "DATABASE_PATH": os.path.join(workdir, "smoke.db"),
           "ADMIN_TOKEN": ADMIN_TOKEN, "SECRET_KEY": "smoke-secret"}
    server = subprocess.Popen([sys.executable, "app.py"], cwd=ROOT, env=env,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    base = f"http://127.0.0.1:{port}"
    try:
        wait_until_up(base)
        checks = [
            ("GET", "/health", None, None, 200),
            ("POST", "/admin/query", {"sql": "SELECT 1"}, None, 401),
            ("POST", "/admin/query", {"sql": "SELECT 1"}, {"X-Admin-Token": ADMIN_TOKEN}, 200),
        ]
        failures = []
        for method, path, body, headers, expected in checks:
            status, _ = call(base, method, path, body, headers)
            mark = "✓" if status == expected else "✗"
            print(f"{mark} {method} {path} -> {status} (expected {expected})")
            if status != expected:
                failures.append(path)
        print(f"{len(checks) - len(failures)}/{len(checks)} checks passed")
        return 1 if failures else 0
    finally:
        server.terminate()
        server.wait(timeout=10)


if __name__ == "__main__":
    sys.exit(main())
```

**Before**
```javascript
// no automated check
```

**After**
```javascript
// tests/smoke.test.js — run with: node --test tests/
const { test, before, after } = require('node:test');
const assert = require('node:assert/strict');
const { spawn } = require('node:child_process');
const net = require('node:net');
const path = require('node:path');

const ADMIN_TOKEN = 'smoke-test-token';
let server;
let base;

function freePort() {
  return new Promise((resolve) => {
    const srv = net.createServer().listen(0, '127.0.0.1', () => {
      const { port } = srv.address();
      srv.close(() => resolve(port));
    });
  });
}

before(async () => {
  const port = await freePort();
  base = `http://127.0.0.1:${port}`;
  server = spawn(process.execPath, ['src/app.js'], {
    cwd: path.join(__dirname, '..'),
    env: { ...process.env, PORT: String(port), ADMIN_TOKEN },
    stdio: 'inherit',
  });
  for (let i = 0; i < 50; i++) {
    try { await fetch(base + '/'); return; } catch { await new Promise((r) => setTimeout(r, 200)); }  // any HTTP answer means up
  }
});

after(() => server.kill());

test('admin report requires the admin token', async () => {
  assert.equal((await fetch(base + '/api/admin/report')).status, 401);
  const res = await fetch(base + '/api/admin/report', { headers: { 'X-Admin-Token': ADMIN_TOKEN } });
  assert.equal(res.status, 200);
});
```

Replace the sample checks with the full endpoint inventory and the baseline requests of the project.
