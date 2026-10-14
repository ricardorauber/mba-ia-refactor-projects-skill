# Refatoração Arquitetural Automatizada com a skill `refactor-arch`

Solução do desafio **"Criação de Skills — Refatoração Arquitetural Automatizada"** do MBA em Engenharia de Software com IA (Full Cycle). O enunciado completo está no [repositório base](https://github.com/devfullcycle/mba-ia-refactor-projects-skill).

A skill `refactor-arch` (Claude Code) analisa uma codebase, audita anti-patterns por severidade e refatora o projeto para o padrão MVC, validando que a aplicação continua funcionando. Ela foi construída com SDD: os requisitos estão em [`specs/`](specs/) e as decisões em [`adrs/`](adrs/).

## Análise Manual

Análise feita lendo o código original (commit `6d1ce62` do repositório base), antes de escrever a skill. As referências `arquivo:linha` apontam para esse código original. A escala de severidade é a do enunciado:

- **CRITICAL** — falha grave de arquitetura ou segurança (credenciais hardcoded, SQL Injection, God Class).
- **HIGH** — violação forte de MVC/SOLID (lógica de negócio em controllers/rotas, acoplamento sem DI, estado global mutável).
- **MEDIUM** — padronização, duplicação ou performance moderada (N+1, validação ausente, tratamento de erro inadequado).
- **LOW** — legibilidade, nomes ruins, magic numbers, imports não usados.

### code-smells-project (Python/Flask — API de E-commerce)

| Severidade | Problema | Arquivo:linha(s) | Justificativa |
|---|---|---|---|
| CRITICAL | SQL Injection por concatenação de strings | `models.py:28`, `models.py:47-50`, `models.py:57-61`, `models.py:109-111`, `models.py:126-129`, `models.py:280`, `models.py:289-297` | Entradas do usuário entram direto no SQL; no login (`109-111`) um `' OR '1'='1` autentica sem senha, e na busca (`291`) qualquer termo pode ler ou apagar tabelas. |
| CRITICAL | Endpoint que executa SQL arbitrário e reseta o banco sem autenticação | `app.py:47-57`, `app.py:59-78` | `POST /admin/query` executa qualquer SQL enviado no corpo e `POST /admin/reset-db` apaga todas as tabelas; qualquer cliente anônimo destrói ou exfiltra os dados. |
| CRITICAL | Credenciais hardcoded e expostas pela API | `app.py:7`, `controllers.py:285-289` | A `SECRET_KEY` está no código e ainda é devolvida em `GET /health`, junto com o caminho do banco e o modo debug; quem ler o repositório ou chamar o health check pode forjar sessões. |
| CRITICAL | Senhas em texto puro, gravadas e devolvidas nas respostas | `database.py:75-79`, `models.py:83`, `models.py:99`, `models.py:126-129` | As senhas são salvas sem hash e `GET /usuarios` devolve a senha de todos os usuários; um único vazamento expõe todas as contas. |
| CRITICAL | God module: `models.py` concentra os 4 domínios | `models.py:1-314` | Acesso a dados, regras de pedido, estoque, desconto e formatação de produtos, usuários, pedidos e relatórios no mesmo arquivo; impossível testar ou mudar uma parte isoladamente. |
| HIGH | Modo debug ligado e servidor exposto em `0.0.0.0` | `app.py:8`, `app.py:88` | O debugger do Werkzeug ativo em interface pública permite execução remota de código a partir de uma página de erro. |
| HIGH | Lógica de negócio e efeitos colaterais nos controllers | `controllers.py:28-54`, `controllers.py:208-210`, `controllers.py:242-250` | Validação de domínio, regras de status e "envio" de e-mail/SMS/push ficam no handler HTTP; a regra não pode ser reutilizada nem testada sem o Flask. |
| HIGH | Conexão global mutável compartilhada entre threads | `database.py:4-10` | Uma única conexão SQLite global com `check_same_thread=False` é usada por todas as requisições, sem injeção de dependência; concorrência gera corrupção de estado e o código fica acoplado ao módulo global. |
| MEDIUM | Criação de pedido sem transação | `models.py:139-168` | Pedido, itens e baixa de estoque são gravados em passos separados sem rollback; uma falha no meio deixa pedido sem itens ou estoque inconsistente. |
| MEDIUM | Queries N+1 na listagem de pedidos | `models.py:177-200`, `models.py:209-232` | Para cada pedido é feita uma query de itens e, para cada item, outra de produto; o número de queries cresce com pedidos × itens. |
| MEDIUM | Erros internos devolvidos ao cliente | `controllers.py:11-12`, `controllers.py:22`, `controllers.py:62`, `controllers.py:292` | `str(e)` vai na resposta 500, expondo detalhes de SQL e da implementação; o tratamento de erro é repetido em cada função em vez de centralizado. |
| MEDIUM | Validação duplicada e inconsistente entre criar e atualizar | `controllers.py:28-54`, `controllers.py:72-90` | O update não valida tamanho do nome nem categoria; a mesma regra escrita duas vezes já divergiu. |
| LOW | `print` usado como log | `controllers.py:8`, `controllers.py:57`, `controllers.py:161`, `controllers.py:179-182`, `app.py:56` | Sem níveis nem formato; e-mails de usuários vão para a saída padrão. |
| LOW | Magic numbers e listas literais | `models.py:256-262`, `controllers.py:52`, `controllers.py:242` | Faixas de desconto, categorias e status válidos estão soltos no código, sem nome nem fonte única. |
| LOW | Imports não usados | `models.py:2`, `database.py:2` | `sqlite3` em `models.py` e `os` em `database.py` não são usados; ruído que esconde dependências reais. |

### ecommerce-api-legacy (Node.js/Express — LMS API com checkout)

| Severidade | Problema | Arquivo:linha(s) | Justificativa |
|---|---|---|---|
| CRITICAL | Credenciais de produção hardcoded | `src/utils.js:1-7` | Senha do banco, chave `pk_live_` do gateway de pagamento e usuário SMTP estão no código-fonte versionado. |
| CRITICAL | God class `AppManager` | `src/AppManager.js:4-139` | Uma classe cria o banco, roda o seed, registra rotas, processa pagamento, matrícula e relatório; nenhuma camada pode ser testada ou trocada isoladamente. |
| CRITICAL | Número do cartão e chave do gateway em log | `src/AppManager.js:45` | O cartão completo e a chave de pagamento são impressos no console a cada checkout (violação de PCI-DSS). |
| CRITICAL | "Hash" de senha reversível | `src/utils.js:17-23`, `src/AppManager.js:68` | `badCrypto` só repete o início do base64 da senha (10 caracteres, sem salt); é trivial de reverter e colide entre senhas diferentes, e usuários sem senha recebem `"123456"`. |
| HIGH | Rotas administrativas sem autenticação | `src/AppManager.js:80`, `src/AppManager.js:131` | Qualquer cliente lê o relatório financeiro ou apaga usuários. |
| HIGH | Lógica de negócio dentro do handler, em callbacks aninhados | `src/AppManager.js:28-78` | Validação, criação de usuário, aprovação de pagamento (`cc.startsWith("4")`), matrícula e auditoria ficam em 5 níveis de callback na própria rota. |
| HIGH | Estado global mutável | `src/utils.js:9-15` | `globalCache` e `totalRevenue` são módulos mutáveis compartilhados e exportados, sem dono nem ciclo de vida. |
| MEDIUM | Queries N+1 no relatório financeiro | `src/AppManager.js:83-127` | Uma query de matrículas por curso e duas (usuário e pagamento) por matrícula, coordenadas por contadores manuais. |
| MEDIUM | Checkout sem transação e exclusão sem cascata | `src/AppManager.js:50-61`, `src/AppManager.js:131-136` | Matrícula, pagamento e auditoria são gravados sem transação; `DELETE /api/users/:id` deixa matrículas e pagamentos órfãos (a própria resposta admite isso). |
| MEDIUM | Erros ignorados e validação mínima | `src/AppManager.js:35`, `src/AppManager.js:57`, `src/AppManager.js:92-93`, `src/AppManager.js:133-135` | Erros de callback são descartados (em `92` um erro deixa `enrollments` indefinido e derruba o processo) e não há validação de e-mail nem de cartão. |
| LOW | Nomes crípticos | `src/AppManager.js:29-33` | `u`, `e`, `p`, `cid`, `cc` (e os campos `usr`, `eml`, `pwd`) escondem o significado dos dados. |
| LOW | Magic strings e números | `src/AppManager.js:46`, `src/AppManager.js:108`, `src/utils.js:6`, `src/utils.js:19` | `"PAID"`/`"DENIED"`, a porta `3000` e o laço de `10000` iterações aparecem soltos no código. |
| LOW | `console.log` como log e import não usado | `src/AppManager.js:2`, `src/utils.js:13`, `src/app.js:13` | Sem níveis nem estrutura; `totalRevenue` é importado e nunca usado. |

### task-manager-api (Python/Flask — API de Task Manager)

| Severidade | Problema | Arquivo:linha(s) | Justificativa |
|---|---|---|---|
| CRITICAL | Credenciais hardcoded | `app.py:13`, `services/notification_service.py:7-10` | `SECRET_KEY` e usuário/senha do SMTP estão no código versionado. |
| CRITICAL | Hash da senha devolvido pela API | `models/user.py:16-25`, `routes/user_routes.py:33`, `routes/user_routes.py:85`, `routes/user_routes.py:129`, `routes/user_routes.py:209` | `to_dict()` inclui `password`; o hash vai na resposta de consulta, criação, atualização e até do login. |
| CRITICAL | Senha com MD5 sem salt | `models/user.py:27-32` | MD5 é quebrado para senhas (rainbow tables); combinado com o hash exposto, as senhas do seed (`1234`, `abcd`) são recuperadas em segundos. |
| HIGH | Autenticação falsa e rotas sem proteção | `routes/user_routes.py:207-211`, `routes/user_routes.py:134-151` | O "token" é `fake-jwt-token-<id>` e nenhuma rota o verifica; qualquer cliente apaga usuários e tasks. |
| HIGH | Regras de negócio nas rotas, duplicadas | `routes/task_routes.py:30-39`, `routes/task_routes.py:71-80`, `routes/task_routes.py:283-287`, `routes/user_routes.py:171-180`, `routes/report_routes.py:33-43`, `routes/report_routes.py:132-135` | A regra de "task atrasada" é reescrita em 6 lugares enquanto `Task.is_overdue()` (`models/task.py:50-60`) existe; as rotas fazem papel de controller e de serviço. |
| HIGH | Debug ligado em `0.0.0.0` | `app.py:34` | O debugger do Werkzeug exposto permite execução remota de código. |
| MEDIUM | Queries N+1 | `routes/task_routes.py:41-57`, `routes/report_routes.py:55-57`, `routes/report_routes.py:161-163`, `routes/user_routes.py:22` | Usuário e categoria são buscados um a um por task, e contagens são feitas por usuário/categoria em laço. |
| MEDIUM | APIs deprecated: `Query.get()` e `datetime.utcnow()` **(API deprecated)** | `routes/task_routes.py:42`, `routes/user_routes.py:29`, `routes/report_routes.py:105`, `models/task.py:15-16`, `models/user.py:14`, `models/category.py:11` | `Query.get()` é legado no SQLAlchemy 2.x (usar `db.session.get()`) e `datetime.utcnow()` é deprecated desde o Python 3.12 (usar `datetime.now(timezone.utc)`); vão quebrar em upgrades. |
| MEDIUM | `except:` genérico engolindo erros | `routes/task_routes.py:62`, `routes/task_routes.py:137`, `routes/report_routes.py:186`, `routes/user_routes.py:130` | Captura até `KeyboardInterrupt`/`SystemExit`, esconde a causa e não registra nada; o tratamento não é centralizado. |
| MEDIUM | Validação ausente ou inconsistente | `routes/task_routes.py:113`, `routes/report_routes.py:196-197`, `utils/helpers.py:57-108` | `priority` em string gera erro 500, `PUT /categories/<id>` sem corpo quebra com `TypeError`, e o validador `process_task_data` existe mas nunca é usado. |
| MEDIUM | Responsabilidade fora do lugar | `routes/report_routes.py:157-223` | O CRUD de categorias mora no blueprint de relatórios. |
| LOW | Imports não usados | `app.py:7`, `routes/task_routes.py:7`, `routes/user_routes.py:6`, `routes/report_routes.py:7-8`, `utils/helpers.py:3-7` | `os`, `sys`, `json`, `time`, `hashlib`, `math` importados sem uso. |
| LOW | `print` usado como log | `routes/task_routes.py:149`, `routes/task_routes.py:153`, `routes/user_routes.py:83`, `routes/user_routes.py:89` | Sem níveis nem formato, misturado à saída do servidor. |
| LOW | Magic numbers e constantes ignoradas | `routes/task_routes.py:110-113`, `routes/report_routes.py:24-28`, `routes/user_routes.py:64`, `utils/helpers.py:110-116` | Status, faixa de prioridade e tamanho mínimo de senha são literais repetidos, embora as constantes existam em `utils/helpers.py`. |
| LOW | Condicionais verbosas | `models/task.py:38-60`, `models/user.py:34-38` | `if ...: return True else: return False` aninhado dificulta a leitura de regras simples. |
