# Audit Report — Project 3 (task-manager-api)

Phase 1 and Phase 2 output of `/refactor-arch`, as printed by the skill (transcript: [`logs/project-3-phase12.md`](logs/project-3-phase12.md)).

================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python (version not declared in the project; local interpreter 3.14.2)
Framework:     Flask 3.0.0
Dependencies:  flask==3.0.0, flask-sqlalchemy==3.1.1, flask-cors==4.0.0, marshmallow==3.20.1 (never imported), requests==2.31.0 (never imported), python-dotenv==1.0.0 (never imported)
Domain:        API de gerenciamento de tarefas (tasks, users, categories, reports)
Architecture:  Partially layered — `models/`, `routes/`, `services/` and `utils/` exist, but the route handlers hold the validation, the overdue/statistics rules and the ORM queries. The service and helpers are never used. The app is built when `app.py` is imported (with `db.create_all()`), and there is no config module and no centralized error handling.
Source files:  15 files analyzed (~1160 lines of code; `routes/__init__.py`, `services/__init__.py` and `utils/__init__.py` are empty)
Database:      SQLite (file `sqlite:///tasks.db`, which Flask-SQLAlchemy 3 resolves to `instance/tasks.db`) via Flask-SQLAlchemy ORM
DB tables:     users, categories, tasks
Entry point:   app.py (`python app.py`, default port 5000 hardcoded, `debug=True`, host 0.0.0.0; seed with `python seed.py` before the first boot; no environment variables)
================================

## Endpoints (22)
| Method | Path | Handler |
|---|---|---|
| GET | /health | app.py:22 |
| GET | / | app.py:26 |
| GET | /tasks | routes/task_routes.py:11 |
| GET | /tasks/<int:task_id> | routes/task_routes.py:65 |
| POST | /tasks | routes/task_routes.py:85 |
| PUT | /tasks/<int:task_id> | routes/task_routes.py:156 |
| DELETE | /tasks/<int:task_id> | routes/task_routes.py:225 |
| GET | /tasks/search | routes/task_routes.py:240 |
| GET | /tasks/stats | routes/task_routes.py:273 |
| GET | /users | routes/user_routes.py:10 |
| GET | /users/<int:user_id> | routes/user_routes.py:27 |
| POST | /users | routes/user_routes.py:42 |
| PUT | /users/<int:user_id> | routes/user_routes.py:92 |
| DELETE | /users/<int:user_id> | routes/user_routes.py:134 |
| GET | /users/<int:user_id>/tasks | routes/user_routes.py:153 |
| POST | /login | routes/user_routes.py:185 |
| GET | /reports/summary | routes/report_routes.py:12 |
| GET | /reports/user/<int:user_id> | routes/report_routes.py:103 |
| GET | /categories | routes/report_routes.py:157 |
| POST | /categories | routes/report_routes.py:167 |
| PUT | /categories/<int:cat_id> | routes/report_routes.py:190 |
| DELETE | /categories/<int:cat_id> | routes/report_routes.py:211 |

================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0 (Flask-SQLAlchemy 3.1.1, SQLite)
Files:   15 analyzed | ~1160 lines of code

## Summary
CRITICAL: 3 | HIGH: 4 | MEDIUM: 7 | LOW: 4

## Findings

### [CRITICAL] Hardcoded Credentials (AP-01)
File: app.py:13, services/notification_service.py:7-10
Description: A SECRET_KEY do Flask está fixa no código como literal, e o NotificationService define host, usuário e senha SMTP (`email_password = 'senha123'`) diretamente no construtor.
Impact: Qualquer pessoa com acesso ao repositório pode forjar sessões assinadas e usar a conta de e-mail; trocar o segredo exige alterar código e fazer deploy.
Recommendation: Ler SECRET_KEY e as credenciais SMTP de variáveis de ambiente em um módulo de configuração, sem fallback literal para segredos (PB-01).

### [CRITICAL] Sensitive Data Exposure (AP-05)
File: models/user.py:16-25, routes/user_routes.py:33, routes/user_routes.py:85-86, routes/user_routes.py:129, routes/user_routes.py:209
Description: `User.to_dict()` inclui o campo `password` (hash da senha). Esse dicionário é devolvido por GET /users/<id>, POST /users, PUT /users/<id> e POST /login.
Impact: Qualquer cliente obtém o hash de senha de qualquer usuário, e como ele é MD5 sem salt, a senha original sai em segundos com uma rainbow table.
Recommendation: Remover `password` da serialização pública do usuário e nunca devolver o hash em respostas (PB-05).

### [CRITICAL] Weak Password Hashing (AP-18)
File: models/user.py:29, models/user.py:32
Description: As senhas são gravadas e conferidas com `hashlib.md5(pwd.encode()).hexdigest()`, sem salt e sem fator de custo.
Impact: Um vazamento do banco revela todas as senhas, porque MD5 é quebrado instantaneamente por rainbow tables e força bruta.
Recommendation: Usar `werkzeug.security.generate_password_hash`/`check_password_hash`, que já vem com o Flask, e regerar os hashes do seed (PB-18).

### [HIGH] Tight Coupling / Missing Dependency Injection (AP-08)
File: app.py:9-31, routes/report_routes.py:2-5, routes/task_routes.py:2-5, routes/user_routes.py:2-4, seed.py:2, services/notification_service.py:5-17
Description: A aplicação é criada, configurada e executa `db.create_all()` no momento do import de `app.py`, sem app factory. O `seed.py` importa `app` direto, e as rotas importam e consultam `db` e os models diretamente. O NotificationService instancia o próprio `smtplib.SMTP` com configuração fixa.
Impact: Não dá para criar a aplicação com outro banco ou configuração (ex.: testes com banco temporário), e importar um módulo já dispara efeitos colaterais no banco.
Recommendation: Criar `create_app(config)` como composition root, injetar a configuração e deixar o acesso a dados atrás dos models/serviços (PB-08).

### [HIGH] Debug Mode in Production (AP-19)
File: app.py:34
Description: `app.run(debug=True, host='0.0.0.0', port=5000)` liga o debugger do Werkzeug escutando em todas as interfaces.
Impact: O debugger interativo permite execução remota de código a partir de qualquer página de erro, e os stack traces expõem detalhes internos.
Recommendation: Ler DEBUG, HOST e PORT de variáveis de ambiente com debug desligado por padrão (PB-19).

### [HIGH] Missing Authentication / Authorization (AP-22)
File: models/user.py:34-38, routes/user_routes.py:10-25, routes/user_routes.py:52, routes/user_routes.py:119-122, routes/user_routes.py:134-151, routes/user_routes.py:210
Description: O login devolve um token falso (`'fake-jwt-token-' + str(user.id)`) que nenhuma rota verifica. `is_admin()` nunca é chamado. Qualquer cliente lista todos os usuários com e-mail, cria usuários com `role` admin, promove qualquer conta via PUT e apaga usuários junto com as tarefas deles.
Impact: Qualquer cliente anônimo pode escalar privilégios, se passar por outro usuário e destruir dados; os papéis só existem no papel.
Recommendation: Proteger as rotas destrutivas e de troca de papel com um guard de autenticação/autorização em middleware (PB-04).

### [HIGH] Business Logic in Controller / Route (AP-06)
File: routes/report_routes.py:12-101, routes/report_routes.py:103-155, routes/report_routes.py:157-224, routes/task_routes.py:11-63, routes/task_routes.py:85-154, routes/task_routes.py:156-223, routes/task_routes.py:273-299, routes/user_routes.py:42-90, routes/user_routes.py:92-132, routes/user_routes.py:153-183
Description: Os handlers concentram validação de domínio, regra de atraso, cálculos de estatística e produtividade, consultas ORM em laço e montagem manual das respostas, com funções de 40 a 90 linhas. Além disso, o CRUD de categorias está no módulo de relatórios.
Impact: As regras não podem ser reutilizadas nem testadas sem o Flask e acabam copiadas entre handlers, que divergem entre si.
Recommendation: Mover regras e consultas para models/serviços (TaskService, ReportService, UserService) e deixar os controllers só orquestrando requisição e resposta (PB-06).

### [MEDIUM] Deprecated API: datetime.utcnow() (AP-20)
File: models/category.py:11, models/task.py:15-16, models/task.py:52, models/user.py:14, routes/report_routes.py:35, routes/report_routes.py:42, routes/report_routes.py:45, routes/report_routes.py:71, routes/report_routes.py:133, routes/task_routes.py:31 (+11 more)
Description: `datetime.utcnow()` é usado nos defaults das colunas, na regra de atraso, nos relatórios, no serviço de notificação, no helper de log e no seed. Esse método está deprecated desde o Python 3.12 (o interpretador local é o 3.14).
Impact: Gera DeprecationWarning hoje e vai quebrar quando for removido; datas naive dificultam comparações corretas de fuso.
Recommendation: Centralizar em um helper `utcnow()` baseado em `datetime.now(timezone.utc)`, mantendo o formato naive gravado no SQLite para preservar as respostas (PB-20).

### [MEDIUM] Callback Pyramid / Deep Nesting (AP-21)
File: models/task.py:38-43, models/task.py:45-48, models/task.py:50-60, models/user.py:34-38, routes/report_routes.py:33-37, routes/report_routes.py:132-135, routes/task_routes.py:30-39, routes/task_routes.py:71-80, routes/task_routes.py:283-287, routes/user_routes.py:171-180 (+3 more)
Description: A regra de atraso tem `if` aninhado em 4 ou mais níveis, contando o laço, e há várias cadeias `if cond: return True else: return False` nos models e helpers.
Impact: O fluxo fica difícil de ler e de alterar, e cada cópia aninhada vira lugar para inconsistência.
Recommendation: Achatar com guard clauses e expressões booleanas diretas (`return self.role == ADMIN`) (PB-21).

### [MEDIUM] Duplicated Logic (AP-13)
File: routes/report_routes.py:19-22, routes/report_routes.py:33-37, routes/report_routes.py:132-135, routes/task_routes.py:17-39, routes/task_routes.py:71-80, routes/task_routes.py:110, routes/task_routes.py:276-287, routes/user_routes.py:61, routes/user_routes.py:162-180, utils/helpers.py:21 (+3 more)
Description: A regra "está atrasada" está copiada em 6 handlers, embora `Task.is_overdue()` (models/task.py:50-60) já exista. A serialização da task é refeita à mão fora de `Task.to_dict()`. A lista de status, a regex de e-mail, as contagens por status e o percentual de conclusão se repetem em vários arquivos.
Impact: As cópias divergem: uma correção aplicada em um ponto deixa o bug nos outros.
Recommendation: Ter uma única fonte para cada regra (métodos do model, constantes de domínio, um validador) e reutilizá-la em todos os pontos (PB-13).

### [MEDIUM] N+1 Queries (AP-09)
File: routes/report_routes.py:55-56, routes/report_routes.py:161-163, routes/task_routes.py:41-57, routes/user_routes.py:22
Description: GET /tasks faz um `User.query.get` e um `Category.query.get` para cada task. GET /users acessa o relacionamento lazy `u.tasks` para cada usuário. O relatório consulta as tasks de cada usuário em laço, e GET /categories conta as tasks de cada categoria com uma query por item.
Impact: O número de queries cresce linearmente com os dados e degrada listagens e relatórios.
Recommendation: Usar eager loading (`joinedload`/`selectinload`) ou agregações com `GROUP BY` em uma única query (PB-09).

### [MEDIUM] Deprecated API: Query.get() (AP-20)
File: routes/report_routes.py:105, routes/report_routes.py:192, routes/report_routes.py:213, routes/task_routes.py:42, routes/task_routes.py:51, routes/task_routes.py:67, routes/task_routes.py:117, routes/task_routes.py:122, routes/task_routes.py:158, routes/task_routes.py:188 (+6 more)
Description: `Model.query.get(id)` aparece 16 vezes. É API legada no SQLAlchemy 2.x, exigido pelo Flask-SQLAlchemy 3.1.1, e emite LegacyAPIWarning.
Impact: Gera warnings hoje e vai quebrar na próxima versão major do SQLAlchemy.
Recommendation: Substituir por `db.session.get(Model, id)` (PB-20).

### [MEDIUM] Missing Input Validation (AP-10)
File: routes/report_routes.py:173-180, routes/report_routes.py:196-202, routes/task_routes.py:96-100, routes/task_routes.py:113, routes/task_routes.py:166-170, routes/task_routes.py:181-184, routes/task_routes.py:260-264, routes/user_routes.py:102-103, routes/user_routes.py:114-117, routes/user_routes.py:124-125
Description: Os campos são usados sem checagem de tipo. `priority` como string quebra em `priority < 1`, e `len(data['title'])` falha com `None`. Em PUT /categories, `request.get_json()` é usado sem checar `None`. Em /tasks/search, `int(priority)` e `int(user_id)` não são protegidos. A cor da categoria e o `active` do usuário não são validados, e o nome do usuário pode virar vazio no update. Os validadores `process_task_data` e `is_valid_color` existem, mas não são chamados.
Impact: Entrada inválida vira erro 500 ou dado corrompido em vez de um 400 claro.
Recommendation: Centralizar a validação de payloads (tipo, faixa, formato e enums) em funções únicas usadas por create e update (PB-10).

### [MEDIUM] Broad Exception Handling (AP-11)
File: routes/report_routes.py:186, routes/report_routes.py:207, routes/report_routes.py:221, routes/task_routes.py:62-63, routes/task_routes.py:137, routes/task_routes.py:151, routes/task_routes.py:204, routes/task_routes.py:221, routes/task_routes.py:236, routes/user_routes.py:87 (+6 more)
Description: Há `except:` sem tipo e `except Exception` repetidos em quase todos os handlers e helpers; GET /tasks engole qualquer erro em um 500 genérico. Não existe handler centralizado (`@app.errorhandler`).
Impact: Erros reais são silenciados sem log útil, e o mesmo try/except é copiado em todo lugar, de forma inconsistente.
Recommendation: Capturar só exceções específicas e registrar handlers de erro centralizados que façam rollback, logem a exceção e devolvam JSON padronizado (PB-11).

### [LOW] Unused Imports / Dead Code (AP-17)
File: app.py:7, models/task.py:3, models/task.py:38-60, models/user.py:34-38, routes/report_routes.py:7-8, routes/task_routes.py:7, routes/user_routes.py:6, services/notification_service.py:4-48, utils/helpers.py:3-7, utils/helpers.py:9-116 (+1 more)
Description: Há imports nunca usados: `os, sys, json` em app.py; `json, os, sys, time` em task_routes; `hashlib, json` em user_routes; `format_date, calculate_percentage, json` em report_routes. Também não são usados: os métodos `validate_status`, `validate_priority`, `is_overdue` e `is_admin`; o NotificationService inteiro, que nunca é instanciado; todo o `utils/helpers.py` com suas constantes; e as dependências marshmallow, requests e python-dotenv (requirements.txt:4-6).
Impact: O ruído esconde as dependências reais e induz o leitor a achar que existem validação e notificação ativas.
Recommendation: Remover imports, funções e dependências mortas, ou passar a usá-las onde substituem código duplicado (PB-17).

### [LOW] Magic Numbers / Strings (AP-15)
File: app.py:34, routes/report_routes.py:45, routes/report_routes.py:129, routes/report_routes.py:180, routes/task_routes.py:96-100, routes/task_routes.py:110-114, routes/user_routes.py:64, routes/user_routes.py:71, routes/user_routes.py:115, utils/helpers.py:110-116 (+3 more)
Description: Vários valores aparecem soltos no código: porta 5000, janela de 7 dias, `priority <= 2` como "alta prioridade", cor `'#000000'`, limites de título 3/200, faixa de prioridade 1–5, senha mínima 4 e listas de status e roles. As constantes já existem em `utils/helpers.py:110-116`, mas não são usadas.
Impact: As regras de negócio ficam sem nome nem fonte única, e mudar um limite exige caçar todas as cópias.
Recommendation: Extrair constantes nomeadas de domínio e usá-las em models, validadores e serviços (PB-15).

### [LOW] Poor Naming (AP-16)
File: models/task.py:45, models/user.py:27, models/user.py:31, routes/report_routes.py:24-28, routes/report_routes.py:161, routes/task_routes.py:16, routes/user_routes.py:14
Description: Dados de domínio usam nomes de uma letra ou abreviados: `p`, `pwd`, `p1`…`p5` para contagens por prioridade, `c`, `t` e `u` nos laços.
Impact: O leitor precisa deduzir o significado, o que facilita erros em código que já é duplicado.
Recommendation: Renomear para nomes descritivos (`priority`, `password`, `critical_count`, `task`, `user`) (PB-16).

### [LOW] Print as Logging (AP-14)
File: routes/task_routes.py:149, routes/task_routes.py:153, routes/task_routes.py:219, routes/task_routes.py:234, routes/user_routes.py:83, routes/user_routes.py:89, routes/user_routes.py:147, services/notification_service.py:21, services/notification_service.py:24, utils/helpers.py:39 (+1 more)
Description: Os handlers e serviços registram eventos e erros com `print(...)`, inclusive com nome de usuário e e-mail do destinatário.
Impact: Os logs ficam sem nível, sem timestamp e sem como filtrar ou desligar, e dados pessoais vão para o stdout.
Recommendation: Usar o módulo `logging` (ou `app.logger`) com níveis adequados e sem dados pessoais (PB-14).

================================
Total: 18 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
