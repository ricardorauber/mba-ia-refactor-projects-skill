# 0005 - Reference: anti-pattern catalog

## Goal
Give Phase 2 an actionable catalog of anti-patterns with concrete detection signals and a fixed severity, covering everything found in the manual analysis plus deprecated APIs.

## Scope
- In: `code-smells-project/.claude/skills/refactor-arch/references/anti-patterns.md`.
- Out: transformations to fix each anti-pattern (0006).

## Requirements
- R1: The catalog SHALL contain at least 14 anti-patterns, each with: stable ID (`AP-NN`), name, severity, detection signals (concrete, greppable where possible, for Python and JavaScript at least), example snippet, why it matters, and the playbook pattern ID that fixes it.
- R2: Severities SHALL be distributed, with at least 3 CRITICAL, 3 HIGH, 3 MEDIUM and 3 LOW entries, following the challenge's severity definitions (reproduced at the top of the file).
- R3: The catalog SHALL cover, at minimum: hardcoded credentials/secrets, SQL injection by string concatenation, god class/god file, arbitrary code/SQL execution endpoints and sensitive-data exposure (passwords/secrets in responses or logs), weak password hashing (plain text, MD5, base64-like), business logic in routes/controllers, mutable global state, missing dependency injection, N+1 queries, missing input validation, duplicated logic, broad/bare exception handling and leaked error details, missing transactions / inconsistent writes, `print`/`console.log` used as logging, magic numbers/strings, poor naming, unused imports, and debug mode on in production.
- R4: The catalog SHALL include a "Deprecated APIs" entry with a lookup table (deprecated → modern) covering at least: SQLAlchemy `Query.get()` → `db.session.get()`, Python `datetime.utcnow()` → `datetime.now(timezone.utc)`, Node `new Buffer()` → `Buffer.from()`, Express `bodyParser` standalone → `express.json()`, `req.param()` → `req.params/query/body`, Flask `before_first_request`, and Python `hashlib.md5` for passwords → `werkzeug.security`/`bcrypt`.
- R5: The catalog SHALL tell the agent how to assign severity when a finding matches several entries (highest wins) and how to group repeated occurrences into one finding listing every location.

## Acceptance criteria
- [ ] AC1: Counting `AP-NN` entries gives ≥14, with ≥3 per severity. (R1, R2)
- [ ] AC2: Every topic in R3 maps to at least one entry. (R3)
- [ ] AC3: The deprecated-API table has every pair listed in R4. (R4)
- [ ] AC4: Every entry names a playbook pattern ID. (R1)

## Unit tests
- T1: `tests/test_skill_structure.py` — parse `### AP-NN` headings and their `Severity:` lines; assert ≥14 entries and ≥3 of each severity (AC1).
- T2: `tests/test_skill_structure.py` — the deprecated section contains `Query.get`, `utcnow`, `new Buffer`, `bodyParser`, `req.param`, `before_first_request`, `md5` (AC3).
- T3: `tests/test_skill_structure.py` — every `AP-NN` entry has a `Fix:` line naming a `PB-NN` that exists in `refactoring-playbook.md` (AC4; runs after 0006).
