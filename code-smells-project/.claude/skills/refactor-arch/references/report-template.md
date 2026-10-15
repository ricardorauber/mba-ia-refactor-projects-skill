# Audit Report Template

Fixed output formats for the three phases. Print them inside a fenced block only if the user asks; by default print them as plain Markdown so they can be copied into a `.md` file as-is.

## Language and formatting rules

- Banners, headings, field labels and severity names stay **in English** exactly as below (`PHASE 1: PROJECT ANALYSIS`, `## Summary`, `File:`, `Description:`, `Impact:`, `Recommendation:`).
- Free text — the domain line, descriptions, impacts and recommendations — is written **in Brazilian Portuguese**.
- Paths are **relative to the project root**. Lines are `path:line` or `path:start-end`; several locations are separated by `, `. Never write a line you did not verify by reading the file. A range that runs to the end of a file ends at the file's **last line number** (check with `awk 'END { print NR }' <file>`), never one past it.
- Banners are lines of exactly 32 `=` characters.

## Phase 1 block

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <language and version when declared>
Framework:     <framework> <version from the manifest>
Dependencies:  <runtime dependencies, comma-separated>
Domain:        <one-line domain description>
Architecture:  <classification> — <one-line evidence>
Source files:  <N> files analyzed (~<LOC> lines of code)
Database:      <engine> (<file path | in-memory | server>) via <driver/ORM>
DB tables:     <table1>, <table2>, ...
Entry point:   <file> (<start command>, default port <port>)
================================
```

Then the endpoint inventory:

```
## Endpoints (<N>)
| Method | Path | Handler |
|---|---|---|
| GET | /items | controllers.py:5 |
```

## Phase 2 — audit report

### Structure

1. Header banner with project, stack and size.
2. `## Summary` with the count per severity, in the order CRITICAL, HIGH, MEDIUM, LOW.
3. `## Findings`, one `###` entry per finding, sorted **CRITICAL → HIGH → MEDIUM → LOW**, and inside the same severity by the first file path and line.
4. Footer banner with the total.
5. The confirmation question as the very last line.

### Finding entry

```
### [<SEVERITY>] <Title> (<AP-NN>)
File: <path:line or path:start-end>[, <more locations>]
Description: <what is wrong, citing the code>
Impact: <what can go wrong because of it>
Recommendation: <how to fix it, naming the playbook pattern PB-NN>
```

Rules:

- `<SEVERITY>` is one of `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` — the catalog severity of the anti-pattern.
- The title is the catalog name, optionally specialized (`Hardcoded Credentials`, `SQL Injection`, `Deprecated API: Query.get()`).
- Repeated occurrences of the same anti-pattern are **one finding** with every location listed in `File:` (cap the list at 10 locations and add `(+N more)` if needed).
- Deprecated-API findings use the title prefix `Deprecated API:` and the recommendation names the modern replacement.
- The `## Summary` counts must equal the number of `###` entries per severity, and `Total` must equal their sum.

### Full example

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: sample-shop-api
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~810 lines of code

## Summary
CRITICAL: 2 | HIGH: 1 | MEDIUM: 1 | LOW: 1

## Findings

### [CRITICAL] SQL Injection (AP-02)
File: models.py:28, models.py:109-111
Description: As queries são montadas concatenando valores vindos da requisição, como em "SELECT * FROM users WHERE email = '" + email + "'".
Impact: Um atacante autentica sem senha ou lê/apaga tabelas inteiras com um payload como ' OR '1'='1.
Recommendation: Usar queries parametrizadas com placeholders do driver (PB-02).

### [CRITICAL] Hardcoded Credentials (AP-01)
File: app.py:7
Description: SECRET_KEY definida no código como 'my-secret-123'.
Impact: Qualquer pessoa com acesso ao repositório pode forjar sessões e tokens.
Recommendation: Ler segredos de variáveis de ambiente em um módulo de configuração (PB-01).

### [HIGH] Business Logic in Controller (AP-06)
File: controllers.py:24-62
Description: O handler valida regras de domínio, calcula valores e dispara notificações.
Impact: A regra não pode ser reutilizada nem testada sem o framework HTTP.
Recommendation: Mover regras para o model/serviço e deixar o controller só orquestrar (PB-06).

### [MEDIUM] N+1 Queries (AP-09)
File: models.py:177-200
Description: Para cada pedido é executada uma query de itens e, para cada item, outra de produto.
Impact: O número de queries cresce com pedidos × itens e degrada a listagem.
Recommendation: Buscar tudo com um JOIN ou carregamento antecipado (PB-09).

### [LOW] Magic Numbers (AP-15)
File: models.py:256-262
Description: Faixas de desconto 10000, 5000 e 1000 e percentuais soltos no código.
Impact: Regras de negócio sem nome nem fonte única, fáceis de divergir.
Recommendation: Extrair constantes nomeadas no módulo de domínio (PB-15).

================================
Total: 5 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

## Phase 3 block

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<tree of the project after the refactor, excluding the exclusions of the scan>

## Findings Addressed
<SEVERITY> <AP-NN> <title> → <PB-NN> (<file(s) changed>)
...

## Baseline vs After
| Method | Path | Baseline | After | Note |
|---|---|---|---|---|
| GET | /items | 200 | 200 | |
| POST | /admin/query | 200 | 401 without token / 200 with token | protected admin route |

## Validation
  ✓ Application boots without errors (<start command>, port <port>)
  ✓ Smoke test passes (<command>: <N> checks)
  ✓ All original endpoints respond with the baseline status codes
  ✓ Configuration extracted (no hardcoded secrets)
  ✓ Centralized error handling
  ✓ Zero CRITICAL/HIGH anti-patterns remaining

## Remaining Findings
<"none", or one line per remaining finding with the reason>
================================
```

Use `✗` instead of `✓` for every check that did not pass and add one line under it explaining what failed. Never print `✓` for a check you did not run.
