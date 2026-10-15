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

## Construção da Skill

A skill fica em [`code-smells-project/.claude/skills/refactor-arch/`](code-smells-project/.claude/skills/refactor-arch/) e foi copiada sem alterações para [`ecommerce-api-legacy/`](ecommerce-api-legacy/.claude/skills/refactor-arch/) e [`task-manager-api/`](task-manager-api/.claude/skills/refactor-arch/). Um teste ([`tests/test_skill_structure.py`](tests/test_skill_structure.py)) garante que as três cópias são idênticas byte a byte.

```
.claude/skills/refactor-arch/
├── SKILL.md                          # o "prompt": papel, regras, 3 fases e o portão de confirmação
└── references/
    ├── project-analysis.md           # Análise de projeto (Fase 1)
    ├── anti-patterns.md              # Catálogo de anti-patterns (Fase 2)
    ├── report-template.md            # Template de relatório (Fases 1, 2 e 3)
    ├── mvc-guidelines.md             # Guidelines de arquitetura (Fase 3)
    └── refactoring-playbook.md       # Playbook de refatoração (Fase 3)
```

### Decisões de design

- **`SKILL.md` é só o roteiro.** Ele define o papel (arquiteto sênior), as regras gerais e os passos de cada fase. O conhecimento de domínio fica nos arquivos de referência, e uma tabela diz **qual referência ler no início de cada fase** (*progressive disclosure*). Assim o contexto do agente só recebe o catálogo quando vai auditar e só recebe o playbook quando vai refatorar. O `SKILL.md` tem 111 linhas e nenhum nome de projeto, tabela ou arquivo dos três alvos (verificado por teste).
- **Fases 1 e 2 são somente leitura.** A skill proíbe criar, editar ou apagar arquivos, instalar dependências e subir a aplicação antes da confirmação. A Fase 2 termina sempre com a pergunta exata `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]`. Só uma resposta afirmativa libera a Fase 3.
- **Validação com baseline.** Antes de mexer no código, a Fase 3 copia o projeto original para um diretório temporário, sobe a aplicação numa porta livre e grava o status code de cada endpoint do inventário montado na Fase 1. Depois de refatorar, ela gera um smoke test **na linguagem do projeto, só com a biblioteca padrão**, sobe o app refatorado, compara com o baseline e tenta corrigir no máximo 3 vezes. Se ainda falhar, a skill reporta `✗` em vez de declarar sucesso.
- **Regras de preservação de comportamento** ([ADR 0004](adrs/0004-security-fixes-may-change-response-bodies.md)): rotas, métodos e status codes ficam iguais. Os corpos só perdem dados sensíveis. A porta passa a vir de `PORT`, com o valor original como default. As rotas de admin perigosas continuam existindo, mas exigem o header `X-Admin-Token`. Os logins do seed continuam funcionando.
- **Formato fixo e verificável.** O template define banners, labels em inglês (como no exemplo do enunciado) e textos em PT-BR ([ADR 0001](adrs/0001-user-facing-text-in-brazilian-portuguese.md)), além de `arquivo:linha` exato, ordenação CRITICAL → LOW e contagens que batem com o resumo. O teste [`tests/test_reports.py`](tests/test_reports.py) valida cada relatório contra esse formato e confere se toda linha citada existe no código original.

### Anti-patterns do catálogo

O catálogo tem **22 anti-patterns** (6 CRITICAL, 5 HIGH, 7 MEDIUM, 4 LOW). Cada um tem sinais de detecção concretos (muitos "grepáveis") para Python e JavaScript, um exemplo, o motivo e o padrão do playbook que o corrige. Os itens saíram da análise manual: todo problema encontrado nos três projetos virou uma entrada genérica.

| Severidade | Anti-patterns | Por quê |
|---|---|---|
| CRITICAL | AP-01 Credenciais hardcoded, AP-02 SQL Injection, AP-03 God Class, AP-04 Endpoint perigoso sem proteção, AP-05 Exposição de dados sensíveis, AP-18 Hash de senha fraco | Expõem dados ou permitem tomar o sistema; apareceram nos três projetos |
| HIGH | AP-06 Lógica de negócio no controller/rota, AP-07 Estado global mutável, AP-08 Acoplamento sem DI, AP-19 Debug em produção, AP-22 Falta de autenticação | Violações fortes de MVC/SOLID ou riscos que dependem de configuração |
| MEDIUM | AP-09 N+1, AP-10 Validação ausente, AP-11 Exceções genéricas / erro vazado, AP-12 Falta de transação, AP-13 Lógica duplicada, AP-20 **APIs deprecated**, AP-21 Pirâmide de callbacks / aninhamento | Performance, consistência e manutenção |
| LOW | AP-14 print/console.log como log, AP-15 Magic numbers, AP-16 Nomes ruins, AP-17 Imports não usados / código morto | Legibilidade |

O **AP-20 (APIs deprecated)** traz uma tabela "deprecated → moderno" com 14 pares: `Query.get()` → `db.session.get()`, `datetime.utcnow()` → `datetime.now(timezone.utc)`, `new Buffer()` → `Buffer.from()`, `bodyParser` → `express.json()`, `req.param()`, `before_first_request`, MD5 para senhas e outros. O playbook tem **22 padrões de transformação** (PB-01 a PB-22), todos com código antes/depois e exemplos em Python **e** JavaScript. Cada anti-pattern aponta para o padrão que o corrige, e o PB-22 é o template do smoke test.

### Como a skill ficou agnóstica de tecnologia

- O `project-analysis.md` detecta a stack pelo **manifesto primeiro** (`requirements.txt`, `package.json`, `pom.xml`, `go.mod`, `composer.json`, `Gemfile`, `*.csproj`) e confirma pelos imports. Para cada stack há heurísticas de framework, banco, tabelas e inventário de rotas, e um fallback genérico para as demais.
- O `mvc-guidelines.md` define as camadas pela **responsabilidade**, não pelo framework, com um layout para Flask, outro para Express e uma tabela de mapeamento para Spring, Laravel, Rails, ASP.NET e Go. Ele também diz como adaptar o plano a um **monólito** (separar por camada e domínio) ou a um projeto **parcialmente em camadas** (manter o que está bom e acrescentar o que falta).
- O smoke test é gerado na linguagem do projeto, sem dependências novas: `urllib` + `subprocess` em Python e `node:test` + `fetch` em Node.js.
- A mesma cópia da skill rodou nos três projetos, sem nenhuma instrução específica por projeto.

### Desafios encontrados e como foram resolvidos

O histórico completo está em [`reports/logs/iterations/README.md`](reports/logs/iterations/README.md), com os logs de cada execução que falhou.

1. **Projeto 1, iteração 1: a skill "protegeu demais".** A refatoração subiu e o smoke test passou, mas a skill colocou o token de admin em rotas comuns que a auditoria marcou como AP-22 (`GET /usuarios`, `PUT /produtos/<id>`...), o que trocou 200 por 401. Ela também moveu a senha do admin do seed para variável de ambiente (o login `admin123` deixou de funcionar), criou uma regra nova (409 ao apagar produto com pedidos) e mexeu no índice do git. **Correção:** as guidelines passaram a dizer que o guard vale só para rotas de admin (namespace `/admin`, SQL vindo do cliente ou limpeza de tabelas), que AP-22 nas outras rotas vira "Remaining Finding" com justificativa e que não se criam restrições de negócio novas. O seed passou a manter as mesmas credenciais, e o `SKILL.md` proibiu comandos de git e passou a tratar qualquer diferença de status fora das rotas de admin como falha.
2. **Projeto 1, iteração 2: o Mac dormiu no meio da execução** (`Your computer went to sleep mid-response`), e antes disso uma queda de DNS atrasou a Fase 3 em horas. **Correção:** o runner passou a rodar o `claude` sob `caffeinate -i` e a guardar o log mesmo quando a execução falha.
3. **Projeto 3, iteração 1: linha fora do arquivo.** Um finding citou `routes/report_routes.py:157-224`, mas o arquivo tem 223 linhas. O teste de relatórios pegou o erro. **Correção:** o template agora exige que intervalos que vão até o fim do arquivo terminem na última linha, conferida com `awk 'END { print NR }'`.
4. **Portas ocupadas.** A 5000 (AirPlay do macOS) e a 3000 estavam em uso nesta máquina. A skill tornou a porta configurável por `PORT` (mantendo o default original) e validou em portas livres.
5. **Rodar a skill de verdade, de forma reprodutível.** A solução foi o [`scripts/run_skill.sh`](scripts/run_skill.sh) ([ADR 0003](adrs/0003-run-the-skill-with-headless-claude-cli.md)). Ele roda `claude -p "/refactor-arch"` (Fases 1–2, que param na pergunta) e depois `claude -p --resume <sessão> "y"` (Fase 3), e guarda o stream JSON completo e uma transcrição legível em [`reports/logs/`](reports/logs/). O primeiro passo comprova o portão de confirmação: `git status` fica vazio entre as duas execuções.
6. **Node 25 e `node --test tests/`.** No primeiro smoke test do projeto 2, o Node 25 tratou `tests/` como módulo. A própria skill corrigiu isso na segunda tentativa, com `tests/index.js` e um script `npm test`.

## Resultados

### Resumo das auditorias

| Projeto | Stack detectada | CRITICAL | HIGH | MEDIUM | LOW | Total | Relatório |
|---|---|---|---|---|---|---|---|
| code-smells-project | Python + Flask 3.1.1, SQLite | 6 | 5 | 5 | 4 | 20 | [audit-project-1.md](reports/audit-project-1.md) |
| ecommerce-api-legacy | Node.js + Express 4.22.1, SQLite em memória | 5 | 5 | 5 | 4 | 19 | [audit-project-2.md](reports/audit-project-2.md) |
| task-manager-api | Python + Flask 3.0.0 + Flask-SQLAlchemy, SQLite | 3 | 4 | 7 | 4 | 18 | [audit-project-3.md](reports/audit-project-3.md) |

Cobertura da análise manual: os relatórios da skill contêm 15 de 15 problemas da análise manual do projeto 1, 13 de 13 do projeto 2 e 16 de 16 do projeto 3. No projeto 3, o CRUD de categorias no blueprint de relatórios aparece dentro do finding AP-06.

### Antes e depois da estrutura

**code-smells-project** — de 4 arquivos monolíticos para MVC por domínio:

```
ANTES                         DEPOIS
app.py                        app.py                 # composition root (create_app)
controllers.py                config/settings.py     # tudo vem do ambiente
database.py                   database.py            # conexão por request (flask.g), schema, seed com hash
models.py                     models/                # produto, usuario, pedido, relatorio, sistema
requirements.txt              controllers/           # fluxo por domínio + validators
                              views/                 # Blueprints por recurso (rotas)
                              services/              # notificações, hash de senha
                              middlewares/           # error handler central, guard de admin
                              tests/smoke_test.py
                              .env.example
```

**ecommerce-api-legacy** — da God Class `AppManager` para camadas com async/await:

```
ANTES                         DEPOIS
src/app.js                    src/app.js             # composition root (createApp)
src/AppManager.js             src/config/settings.js
src/utils.js                  src/database/          # conexão promisificada, transações, schema/seed
api.http                      src/models/            # course, user, enrollment, payment, auditLog, report (JOIN único)
package.json                  src/controllers/       # checkout, report, user + validators
                              src/routes/index.js    # rotas (view)
                              src/services/          # pagamento, hash scrypt
                              src/middlewares/       # adminAuth, asyncHandler, errorHandler
                              src/utils/logger.js
                              tests/smoke.test.js
```

**task-manager-api** — parcialmente em camadas; a skill manteve `models/` e `routes/` e adicionou o que faltava:

```
ANTES                         DEPOIS
app.py                        app.py                 # create_app() + __main__
database.py                   config/settings.py     # novo
seed.py                       database.py
models/ (task, user,          models/ (+ base.py)    # utc_now, get/save/delete, is_overdue, hash werkzeug
  category)                   controllers/           # novo: task, user, category, report + validators
routes/ (task, user,          routes/ (+ category_routes.py, system_routes.py)   # só HTTP
  report)                     middlewares/           # novo: errors + error handler central
services/notification_...     seed.py                # usa create_app(), mesmas senhas
utils/helpers.py              tests/smoke_test.py
                              (services/ e utils/ removidos: nunca eram usados)
```

### Checklist de validação

| Item | Projeto 1 | Projeto 2 | Projeto 3 |
|---|---|---|---|
| **Fase 1 — Análise** | | | |
| Linguagem detectada corretamente | ✅ Python | ✅ JavaScript/Node.js | ✅ Python |
| Framework detectado corretamente | ✅ Flask 3.1.1 | ✅ Express 4.x (4.22.1 no lock) | ✅ Flask 3.0.0 + Flask-SQLAlchemy |
| Domínio da aplicação descrito corretamente | ✅ E-commerce | ✅ LMS com checkout | ✅ Task Manager |
| Número de arquivos analisados condiz com a realidade | ✅ 4 | ✅ 3 | ✅ 15 (inclui 3 `__init__.py` vazios) |
| **Fase 2 — Auditoria** | | | |
| Relatório segue o template definido nos arquivos de referência | ✅ | ✅ | ✅ |
| Cada finding tem arquivo e linhas exatos | ✅ | ✅ | ✅ (após a iteração 2) |
| Findings ordenados por severidade (CRITICAL → LOW) | ✅ | ✅ | ✅ |
| Mínimo de 5 findings identificados | ✅ 20 | ✅ 19 | ✅ 18 |
| Detecção de APIs deprecated incluída (se aplicável) | ➖ não aplicável (checado e justificado no relatório) | ➖ não aplicável (checado e justificado no relatório) | ✅ `Query.get()` e `datetime.utcnow()` |
| Skill pausa e pede confirmação antes da Fase 3 | ✅ | ✅ | ✅ |
| **Fase 3 — Refatoração** | | | |
| Estrutura de diretórios segue padrão MVC | ✅ | ✅ | ✅ |
| Configuração extraída para módulo de config (sem hardcoded) | ✅ `config/settings.py` | ✅ `src/config/settings.js` | ✅ `config/settings.py` |
| Models criados para abstrair dados | ✅ | ✅ | ✅ |
| Views/Routes separadas para visualização ou roteamento | ✅ `views/` | ✅ `src/routes/` | ✅ `routes/` |
| Controllers concentram o fluxo da aplicação | ✅ | ✅ | ✅ |
| Error handling centralizado | ✅ | ✅ | ✅ |
| Entry point claro | ✅ `app.py` | ✅ `src/app.js` | ✅ `app.py` |
| Aplicação inicia sem erros | ✅ | ✅ | ✅ |
| Endpoints originais respondem corretamente | ✅ 17/17 públicos iguais; 2 de admin exigem token | ✅ 3/3 (relatório de admin exige token) | ✅ 22/22 (um 500 → 400 para entrada inválida) |

### Evidências de execução

As transcrições completas das execuções da skill estão em [`reports/logs/`](reports/logs/): `project-N-phase12.md` (Fases 1–2) e `project-N-phase3.md` (Fase 3, com a tabela "Baseline vs After"). Os `.jsonl` trazem o stream bruto do `claude`.

Saída dos smoke tests gerados pela skill, rodados após a refatoração:

```
$ cd code-smells-project && .venv/bin/python tests/smoke_test.py       # reports/logs/smoke-project-1.log
✓ GET / -> 200 (expected 200)
✓ GET /produtos -> 200 (expected 200)
...
✓ POST /admin/query -> 401 (expected 401)
✓ POST /admin/query -> 200 (expected 200)
29/29 checks passed

$ cd ecommerce-api-legacy && node --test tests/                        # reports/logs/smoke-project-2.log
✔ admin report requires the admin token
✔ checkout succeeds for a new and an existing user
✔ checkout rejects denied payments, missing fields and unknown courses
...
ℹ tests 7
ℹ pass 7
ℹ fail 0

$ cd task-manager-api && .venv/bin/python tests/smoke_test.py          # reports/logs/smoke-project-3.log
...
✓ DELETE /users/4 -> 200 (expected 200)
27/27 checks passed
```

Boot do task-manager-api refatorado (venv limpo, seed + login com usuário do seed):

```
$ python seed.py
Seed concluído com sucesso!
  3 usuários
  4 categorias
  10 tasks
$ PORT=50977 python app.py
SECRET_KEY is not set; using an ephemeral value
 * Serving Flask app 'app'
 * Debug mode: off
$ curl -X POST localhost:50977/login -d '{"email":"joao@email.com","password":"1234"}'
{"message":"Login realizado com sucesso","token":"fake-jwt-token-1","user":{"active":true,...,"role":"admin"}}   # sem o campo password
```

### Comportamento da skill em stacks diferentes

- **Monólito Python (projeto 1):** a skill separou por camada e por domínio (5 models, 6 controllers, 6 blueprints). Ela trocou a conexão global por uma conexão por request, parametrizou todas as queries, passou a gerar hash das senhas com `werkzeug` (sem dependência nova) e migra senhas legadas em texto puro no primeiro login. O `/admin/query` agora aceita só um `SELECT` numa conexão `query_only`.
- **God Class Node.js (projeto 2):** a mesma skill gerou uma arquitetura idiomática de Express: `createApp()`, `express.Router`, middleware de erro com 4 parâmetros, `asyncHandler`, sqlite3 promisificado com transações e `node:crypto` scrypt no lugar do `badCrypto`. A pirâmide de callbacks do relatório financeiro virou um único `LEFT JOIN` com o mesmo JSON de saída, e a chave do gateway e o número do cartão saíram dos logs (agora `**** 4444`).
- **Projeto Python parcialmente organizado (projeto 3):** a skill reconheceu a organização existente e **não** reestruturou à toa. Manteve os models do SQLAlchemy e o nome `routes/`, acrescentou controllers, config, middlewares e app factory, moveu o CRUD de categorias para um blueprint próprio (mesmas URLs) e removeu `services/` e `utils/`, que não eram usados. Também trocou as APIs deprecated.
- **O que ficou em aberto, de propósito:** nos três projetos a skill listou como "Remaining Finding" a falta de autenticação real nas rotas que não são de admin (AP-22). Adicionar login com token mudaria o contrato da API, o que precisa de uma decisão de produto ([ADR 0004](adrs/0004-security-fixes-may-change-response-bodies.md)).
- **Custo:** as execuções aceitas levaram de 1,5 a 3 minutos nas Fases 1–2 e de 5,5 a 8,5 minutos na Fase 3, com `claude-opus-5-5`.

## Como Executar

### Pré-requisitos

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) instalado e autenticado (`claude --version`)
- Python 3.10+ (testado com 3.14) para os projetos Flask e os testes do repositório
- Node.js 18+ (testado com 25) para o `ecommerce-api-legacy`
- Uma cópia deste repositório: `git clone git@github.com:ricardorauber/mba-ia-refactor-projects-skill.git`

### Executar a skill (modo interativo, como no enunciado)

```bash
cd code-smells-project
claude "/refactor-arch"
```

A skill imprime a Fase 1, o relatório da Fase 2 e pergunta `Proceed with refactoring (Phase 3)? [y/n]`. Responda `y` para refatorar. O mesmo comando vale dentro de `ecommerce-api-legacy/` e de `task-manager-api/`.

### Executar a skill em modo headless (como foi feito aqui)

```bash
scripts/run_skill.sh code-smells-project phase12
```

```bash
scripts/run_skill.sh code-smells-project phase3
```

O primeiro comando roda as Fases 1–2 e para na confirmação. O segundo retoma a mesma sessão respondendo `y`. Os logs vão para `reports/logs/project-N-*`, e o modelo pode ser trocado com `REFACTOR_ARCH_MODEL`. Para montar o relatório a partir da transcrição:

```bash
python3 scripts/extract_report.py reports/logs/project-1-phase12.md reports/audit-project-1.md "Audit Report — Project 1 (code-smells-project)"
```

### Validar que a refatoração funcionou

**code-smells-project**

```bash
cd code-smells-project && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

```bash
.venv/bin/python tests/smoke_test.py
```

```bash
PORT=5050 ADMIN_TOKEN=troque-me .venv/bin/python app.py
```

**ecommerce-api-legacy**

```bash
cd ecommerce-api-legacy && npm install && npm test
```

```bash
PORT=3030 ADMIN_TOKEN=troque-me npm start
```

**task-manager-api**

```bash
cd task-manager-api && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

```bash
.venv/bin/python seed.py && .venv/bin/python tests/smoke_test.py
```

```bash
PORT=5060 .venv/bin/python app.py
```

As variáveis de ambiente de cada projeto estão no respectivo `.env.example` e no README do projeto. As rotas de admin exigem o header `X-Admin-Token` com o valor de `ADMIN_TOKEN`.

**Testes do repositório** (estrutura da skill, cópias idênticas, formato e linhas dos relatórios, seções do README):

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt && .venv/bin/pytest
```
