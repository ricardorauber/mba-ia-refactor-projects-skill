# Skill run transcript

- Session: `261140b7-f40a-4ca0-a2b5-3c680f5049d2`
- Model: `claude-opus-5-5`

> `Bash` ls -la && find . -path ./.claude -prune -o -path ./.git -prune -o -path ./node_modules -prune -o -type f -print | xargs wc -l

> `Read` /Users/ricardorauberpereira/Downloads/MBA-Desafios/Refatoracao_Arquitetural-Skills/.worktrees/spec-0008-run-skill-on-ecommerce-api-legacy/ecommerce-api-legacy/.claude/skills/refactor-arch/references/project-analysis.md

> `Read` /Users/ricardorauberpereira/Downloads/MBA-Desafios/Refatoracao_Arquitetural-Skills/.worktrees/spec-0008-run-skill-on-ecommerce-api-legacy/ecommerce-api-legacy/.claude/skills/refactor-arch/references/report-template.md

> `Bash` cat -n package.json README.md api.http src/app.js src/utils.js src/AppManager.js

> `Read` /Users/ricardorauberpereira/Downloads/MBA-Desafios/Refatoracao_Arquitetural-Skills/.worktrees/spec-0008-run-skill-on-ecommerce-api-legacy/ecommerce-api-legacy/.claude/skills/refactor-arch/references/anti-patterns.md

> `Bash` node --version; ls package-lock.json && grep -n '"node_modules/express"' -A2 package-lock.json; grep -n '"node_modules/sqlite3"' -A2 package-lock.json

================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      JavaScript (Node.js; no `engines` field declared)
Framework:     Express ^4.18.2 (4.22.1 in package-lock.json)
Dependencies:  express ^4.18.2, sqlite3 ^5.1.6
Domain:        API de LMS com checkout de cursos (users, courses, enrollments, payments, audit_logs)
Architecture:  Monolithic — `src/AppManager.js` abre o banco, roda DDL e seed, registra as rotas e guarda as regras de pagamento/matrícula; `src/utils.js` mistura config com segredos, cache global e "crypto"
Source files:  3 files analyzed (~180 lines of code)
Database:      SQLite (in-memory) via sqlite3 (raw driver)
DB tables:     users, courses, enrollments, payments, audit_logs
Entry point:   src/app.js (npm start → node src/app.js, default port 3000)
================================

Boot notes: the port 3000 is hardcoded in `src/utils.js:6`. No environment variables are read. Seed data loads at every boot through `initDb()` (`src/AppManager.js:10-23`), and because the database is in-memory it is wiped on every restart. There is no debug flag and `NODE_ENV` is never checked.

## Endpoints (3)
| Method | Path | Handler |
|---|---|---|
| POST | /api/checkout | src/AppManager.js:28 |
| GET | /api/admin/financial-report | src/AppManager.js:80 |
| DELETE | /api/users/:id | src/AppManager.js:131 |

================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   Node.js + Express 4.22.1 (sqlite3 5.1.7)
Files:   3 analyzed | ~180 lines of code

## Summary
CRITICAL: 5 | HIGH: 5 | MEDIUM: 5 | LOW: 4

## Findings

### [CRITICAL] God Class (AP-03)
File: src/AppManager.js:4-139
Description: A classe `AppManager` cria a conexão (`new sqlite3.Database(':memory:')`), executa o DDL e o seed em `initDb()`, registra as três rotas em `setupRoutes(app)` e implementa nos handlers a aprovação de pagamento, a criação de usuário, a matrícula, a auditoria e a agregação do relatório financeiro.
Impact: Nada pode ser testado ou alterado isoladamente; qualquer mudança no checkout, no relatório ou no schema mexe no mesmo arquivo e arrisca todas as funcionalidades.
Recommendation: Dividir em config, models (acesso a dados), services (regras de checkout/relatório), controllers, rotas e composition root (PB-03).

### [CRITICAL] Weak Password Hashing (AP-18)
File: src/AppManager.js:18, src/AppManager.js:68, src/utils.js:17-23
Description: `badCrypto` repete os 2 primeiros caracteres do base64 da senha e trunca em 10 caracteres, sem sal e de forma reversível/colidente (senhas com o mesmo prefixo geram o mesmo "hash"); o usuário do seed é gravado com a senha em texto puro `'123'`.
Impact: Um vazamento do banco revela ou permite forjar as senhas imediatamente; senhas diferentes colidem no mesmo valor.
Recommendation: Usar `crypto.scrypt` com sal aleatório (stdlib do Node) e gravar o seed já com hash (PB-18).

### [CRITICAL] Sensitive Data Exposure (AP-05)
File: src/AppManager.js:45
Description: O checkout faz `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)`, imprimindo o número completo do cartão e a chave do gateway de pagamento.
Impact: Qualquer pessoa com acesso aos logs obtém números de cartão e a chave live do gateway (violação direta de PCI-DSS).
Recommendation: Remover o cartão e a chave dos logs; registrar no máximo os últimos 4 dígitos via logger estruturado (PB-05).

### [CRITICAL] Unprotected Dangerous Endpoint (AP-04)
File: src/AppManager.js:80-129
Description: `GET /api/admin/financial-report` devolve a receita por curso e a lista de alunos com o valor pago, sem nenhuma checagem de autenticação no handler nem em middleware.
Impact: Qualquer cliente anônimo lê os dados financeiros e a lista de alunos da plataforma.
Recommendation: Proteger as rotas administrativas com um middleware de token admin lido da configuração (PB-04).

### [CRITICAL] Hardcoded Credentials (AP-01)
File: src/utils.js:2-4
Description: O objeto `config` contém `dbUser: "admin_master"`, `dbPass: "senha_super_secreta_prod_123"` e `paymentGatewayKey: "pk_live_1234567890abcdef"` escritos no código.
Impact: Qualquer pessoa com acesso ao repositório tem a senha do banco e a chave live do gateway; rotacionar exige alterar código e fazer deploy.
Recommendation: Ler segredos de variáveis de ambiente em um módulo de configuração, sem fallback literal para segredos (PB-01).

### [HIGH] Tight Coupling / Missing Dependency Injection (AP-08)
File: src/AppManager.js:2, src/AppManager.js:7, src/app.js:8-12
Description: `AppManager` instancia a própria conexão no construtor (`this.db = new sqlite3.Database(':memory:')`) e importa `config` e helpers diretamente de `utils`; `app.js` monta o app e chama `app.listen` no mesmo módulo, sem uma fábrica que permita injetar o banco.
Impact: Não é possível trocar o banco (arquivo temporário em testes, outro ambiente) nem subir o app sem abrir a porta.
Recommendation: Criar uma composition root/fábrica `createApp({ db, config })` que injeta as dependências nos models/services (PB-08).

### [HIGH] Business Logic in Controller (AP-06)
File: src/AppManager.js:28-78, src/AppManager.js:80-129
Description: O handler de checkout (50 linhas) valida a entrada, aprova o pagamento por `cc.startsWith("4")`, cria o usuário com hash, matricula, grava o pagamento e a auditoria e formata a resposta; o handler do relatório calcula a receita somando os pagamentos `PAID`.
Impact: As regras de pagamento e de receita não podem ser reutilizadas nem testadas sem o Express e tendem a ser duplicadas.
Recommendation: Mover as regras para `services` (checkout e relatório) e deixar o controller só traduzir HTTP ↔ serviço (PB-06).

### [HIGH] Mutable Global State (AP-07)
File: src/AppManager.js:59, src/utils.js:9-15, src/utils.js:25
Description: `let globalCache = {}` e `let totalRevenue = 0` são variáveis de módulo exportadas; `logAndCache` muta `globalCache` a cada checkout e o cache vive pelo processo inteiro.
Impact: Estado compartilhado entre requisições e testes, crescimento de memória sem limite e acoplamento oculto entre módulos.
Recommendation: Eliminar o estado global; se o cache for necessário, encapsulá-lo em uma instância injetada (PB-07).

### [HIGH] Missing Authentication / Authorization (AP-22)
File: src/AppManager.js:131-137
Description: `DELETE /api/users/:id` apaga qualquer usuário pelo id sem nenhuma autenticação ou autorização.
Impact: Qualquer cliente anônimo pode apagar contas de usuários.
Recommendation: Exigir o token admin no middleware de autenticação para a rota destrutiva (PB-04).

### [HIGH] Debug Mode in Production (AP-19)
File: src/app.js:5-6
Description: O app não tem middleware de erro e nunca verifica `NODE_ENV`, então erros (por exemplo, JSON malformado em `express.json()`) caem no handler padrão do Express, que devolve o stack trace ao cliente fora de produção.
Impact: Stack traces com caminhos internos e versões vazam para qualquer cliente.
Recommendation: Adicionar um middleware de erro centralizado que responde mensagens genéricas, sem stack (PB-19, junto com PB-11).

### [MEDIUM] Missing Input Validation (AP-10)
File: src/AppManager.js:29-35, src/AppManager.js:68, src/AppManager.js:132
Description: O checkout só testa se `usr`, `eml`, `c_id` e `card` são truthy: não valida tipo, formato de e-mail nem de cartão (um `card` numérico faz `cc.startsWith` lançar TypeError dentro do callback e derruba o processo); quando falta `pwd`, aplica a senha padrão `"123456"`; o `:id` do DELETE não é validado.
Impact: Entradas inválidas derrubam o servidor ou criam dados corrompidos e contas com senha previsível, em vez de um 400 claro.
Recommendation: Validar tipos e formatos na borda (controller/validator) e retornar 400 (PB-10).

### [MEDIUM] Callback Pyramid / Deep Nesting (AP-21)
File: src/AppManager.js:37-77, src/AppManager.js:83-128
Description: O checkout aninha cinco callbacks (`db.get` → `db.get` → `db.run` → `db.run` → `db.run`) e o relatório usa contadores manuais (`coursesPending--`, `enrPending--`) com o bloco de finalização copiado em 96-98 e 119-121.
Impact: Fica muito difícil seguir o fluxo e o tratamento de erros, o que favorece condições de corrida e erros não tratados.
Recommendation: Promisificar o driver (helpers `run/get/all` com `async/await`) e usar fluxo linear (PB-21).

### [MEDIUM] Broad Exception Handling / Leaked Error Details (AP-11)
File: src/AppManager.js:38, src/AppManager.js:57, src/AppManager.js:92-93, src/AppManager.js:104, src/AppManager.js:106, src/AppManager.js:133, src/app.js:5-14
Description: Um erro de banco é mascarado como 404 em 38; os callbacks de 57, 92, 104, 106 e 133 ignoram `err` (em 93, `enrollments.length` lança se a query falhar); não existe middleware de erro `(err, req, res, next)`.
Impact: Falhas reais são engolidas ou derrubam o processo, e o cliente recebe respostas enganosas.
Recommendation: Propagar erros para um middleware de erro centralizado (PB-11).

### [MEDIUM] Missing Transaction / Inconsistent Writes (AP-12)
File: src/AppManager.js:50-61, src/AppManager.js:69-72, src/AppManager.js:133-135
Description: Usuário, matrícula, pagamento e auditoria são gravados em `INSERT`s encadeados sem `BEGIN/COMMIT/ROLLBACK`; o DELETE apaga o usuário e deixa matrículas e pagamentos órfãos, como a própria resposta admite.
Impact: Uma falha no meio deixa matrícula sem pagamento ou usuário sem matrícula; deletes geram dados órfãos que distorcem o relatório.
Recommendation: Envolver o checkout em uma transação e apagar os filhos (pagamentos, matrículas) na mesma transação do delete (PB-12).

### [MEDIUM] N+1 Queries (AP-09)
File: src/AppManager.js:89-125
Description: Para cada curso roda uma query de matrículas (92) e, para cada matrícula, uma query de usuário (104) e outra de pagamento (106).
Impact: O número de queries cresce com cursos × matrículas × 2 e o relatório degrada linearmente.
Recommendation: Buscar tudo com um único SELECT usando LEFT JOIN entre courses, enrollments, users e payments e agrupar em memória (PB-09).

### [LOW] Unused Imports / Dead Code (AP-17)
File: src/AppManager.js:2, src/utils.js:2-3, src/utils.js:5, src/utils.js:9-10, src/utils.js:25
Description: `totalRevenue` é importado e nunca usado e também nunca é alterado; `globalCache` é escrito e nunca lido; `config.dbUser`, `config.dbPass` e `config.smtpUser` nunca são lidos.
Impact: Ruído que esconde as dependências reais e induz o leitor a achar que existe controle de receita/SMTP.
Recommendation: Remover os bindings, exports e chaves de configuração sem uso (PB-17).

### [LOW] Poor Naming (AP-16)
File: src/AppManager.js:26, src/AppManager.js:29-33, src/utils.js:17
Description: Variáveis `u`, `e`, `p`, `cid` e `cc` para os dados do checkout, o alias `self` para `this` e a função `badCrypto`; os campos do request (`usr`, `eml`, `pwd`, `c_id`) também são crípticos.
Impact: O leitor precisa deduzir o significado e é fácil errar.
Recommendation: Usar nomes descritivos internamente e mapear os campos do request na borda, mantendo o contrato da API (PB-16).

### [LOW] Print / console.log as Logging (AP-14)
File: src/AppManager.js:45, src/app.js:13, src/utils.js:13
Description: `console.log` usado dentro do handler de checkout, no helper de cache e no banner de boot.
Impact: Sem níveis, sem como silenciar e com dados pessoais indo parar no stdout.
Recommendation: Criar um logger mínimo com níveis, silenciável por configuração (PB-14).

### [LOW] Magic Numbers / Strings (AP-15)
File: src/AppManager.js:46, src/AppManager.js:48, src/AppManager.js:68, src/AppManager.js:108, src/utils.js:6, src/utils.js:19, src/utils.js:22
Description: Os status `"PAID"`/`"DENIED"` são comparados em vários pontos, o prefixo de cartão `"4"` é a regra de aprovação, a senha padrão é `"123456"`, a porta `3000` está fixa e o loop `10000` e o corte `10` aparecem soltos.
Impact: As regras de negócio não têm nome nem fonte única e as cópias divergem facilmente.
Recommendation: Extrair constantes nomeadas (status de pagamento, prefixo aprovado) e levar a porta para a configuração (PB-15).

================================
Total: 19 findings
================================

Notes on what I checked and left out:
- **AP-02 (SQL Injection):** not reported. Every query uses `?` placeholders. The template literal at `src/AppManager.js:57` is passed as a bound parameter, so it is safe.
- **AP-20 (Deprecated APIs):** not reported. No API in the table matches Express 4.22.1 or this Node code. The code already uses `Buffer.from` and `express.json()`. The hand-nested sqlite3 callbacks are listed in the catalog as "not deprecated, superseded", so I reported them under AP-21 instead.
- **AP-13 (Duplicated Logic):** not reported separately. The only copied block is the counter finalization at lines 96-98 and 119-121, and it is listed under AP-21.

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]

---
Result: success | turns: 7 | duration: 98s
