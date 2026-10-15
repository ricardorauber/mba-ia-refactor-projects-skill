# Audit Report — Project 1 (code-smells-project)

Phase 1 and Phase 2 output of `/refactor-arch`, as printed by the skill (transcript: [`logs/project-1-phase12.md`](logs/project-1-phase12.md)).

================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python (version not declared in the manifest; local interpreter 3.14.2)
Framework:     Flask 3.1.1
Dependencies:  flask==3.1.1, flask-cors==5.0.1
Domain:        API de E-commerce (produtos, usuários, pedidos, relatório de vendas)
Architecture:  Monolithic (god files) — `controllers.py` e `models.py` existem, mas cada um cobre todos os domínios (produtos, usuários, pedidos, relatórios). `app.py` mistura configuração, rotas, handlers admin com SQL e boot. `database.py` mistura conexão global, DDL e seed.
Source files:  4 files analyzed (~780 lines of code)
Database:      SQLite (file `loja.db`) via sqlite3 (raw driver, one global connection)
DB tables:     produtos, usuarios, pedidos, itens_pedido
Entry point:   app.py (`python app.py`, default port 5000 — hardcoded, `debug=True`; seed runs automatically at first boot inside `get_db()`; no environment variables required)
================================

## Endpoints (19)
| Method | Path | Handler |
|---|---|---|
| GET | / | app.py:33 |
| GET | /produtos | controllers.py:5 |
| GET | /produtos/busca | controllers.py:111 |
| GET | /produtos/<int:id> | controllers.py:14 |
| POST | /produtos | controllers.py:24 |
| PUT | /produtos/<int:id> | controllers.py:64 |
| DELETE | /produtos/<int:id> | controllers.py:98 |
| GET | /usuarios | controllers.py:128 |
| GET | /usuarios/<int:id> | controllers.py:136 |
| POST | /usuarios | controllers.py:146 |
| POST | /login | controllers.py:167 |
| POST | /pedidos | controllers.py:188 |
| GET | /pedidos | controllers.py:229 |
| GET | /pedidos/usuario/<int:usuario_id> | controllers.py:222 |
| PUT | /pedidos/<int:pedido_id>/status | controllers.py:237 |
| GET | /relatorios/vendas | controllers.py:257 |
| GET | /health | controllers.py:264 |
| POST | /admin/reset-db | app.py:48 |
| POST | /admin/query | app.py:60 |

================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~780 lines of code

## Summary
CRITICAL: 6 | HIGH: 5 | MEDIUM: 5 | LOW: 4

## Findings

### [CRITICAL] God Class / God File (AP-03)
File: app.py:1-88, controllers.py:1-292, database.py:7-86, models.py:1-314
Description: Não há separação por camada nem por domínio. `models.py` (314 linhas) concentra acesso a dados, mapeamento de linhas e regras (estoque, desconto) de produtos, usuários, pedidos e relatórios. `controllers.py` cobre todos os domínios e ainda roda SQL direto no health check. `app.py` cria e configura a app, registra rotas, implementa handlers admin com SQL e sobe o servidor. `database.py` abre a conexão, executa DDL e popula o banco.
Impact: Nenhuma parte pode ser testada ou alterada isoladamente; qualquer mudança arrisca todas as funcionalidades.
Recommendation: Dividir em config, models por domínio, controllers, views/rotas (Blueprints), middlewares e um app factory como composition root (PB-03).

### [CRITICAL] Hardcoded Credentials (AP-01)
File: app.py:7, controllers.py:289
Description: A SECRET_KEY está fixa no código como literal (`app.config["SECRET_KEY"] = "minha-chave-..."`), e o mesmo literal está repetido no corpo do health check.
Impact: Qualquer pessoa com acesso ao repositório consegue forjar sessões e assinaturas, e trocar o segredo exige alterar o código e fazer novo deploy.
Recommendation: Ler segredos de variáveis de ambiente num módulo de configuração, sem valor literal de produção (PB-01).

### [CRITICAL] Unprotected Dangerous Endpoint (AP-04)
File: app.py:47-57, app.py:59-78
Description: `POST /admin/reset-db` executa `DELETE FROM` sem `WHERE` em todas as tabelas, e `POST /admin/query` executa `cursor.execute(query)` com o SQL enviado pelo cliente. Nenhuma das duas rotas verifica autenticação.
Impact: Qualquer cliente anônimo consegue apagar o banco inteiro, ler a tabela de usuários com as senhas ou alterar dados livremente.
Recommendation: Proteger as rotas admin com um guard de token de admin vindo da configuração (401 sem token) e restringir a execução de SQL livre (PB-04).

### [CRITICAL] Sensitive Data Exposure (AP-05)
File: controllers.py:286-289, models.py:83, models.py:98
Description: O health check devolve `ambiente`, `db_path`, `debug` e `secret_key`. O mapeamento de usuários inclui o campo `senha`, que então aparece em `GET /usuarios` e `GET /usuarios/<id>`.
Impact: Um único request anônimo expõe o segredo da aplicação e as senhas de todos os usuários.
Recommendation: Remover campos sensíveis dos serializers e da resposta do health check (PB-05).

### [CRITICAL] Weak Password Hashing (AP-18)
File: database.py:76-78, models.py:109-111, models.py:126-129
Description: As senhas são gravadas em texto puro, tanto no seed quanto em `criar_usuario`, e o login compara `senha = '<input>'` direto no SQL.
Impact: Um vazamento do banco (trivial via `/admin/query`) revela todas as senhas, que os usuários costumam reutilizar em outros serviços.
Recommendation: Gerar hash com `werkzeug.security.generate_password_hash` e verificar com `check_password_hash`, já que o Werkzeug vem com o Flask (PB-18).

### [CRITICAL] SQL Injection (AP-02)
File: models.py:28, models.py:47-50, models.py:57-61, models.py:68, models.py:92, models.py:109-111, models.py:126-129, models.py:140-166, models.py:174-192, models.py:220-224 (+2 more)
Description: Todas as queries com parâmetro são montadas por concatenação de strings. Os casos mais graves são o login (`"... WHERE email = '" + email + "' AND senha = '" + senha + "'"`) e a busca (`query += " AND (nome LIKE '%" + termo + "%' ..."`, em models.py:289-299). O mesmo vale para o status do pedido (models.py:279-281).
Impact: `' OR '1'='1` no login autentica sem senha, e qualquer campo de texto permite ler, alterar ou apagar tabelas.
Recommendation: Usar queries parametrizadas com placeholders `?` do sqlite3 em todas as chamadas (PB-02).

### [HIGH] Tight Coupling / Missing Dependency Injection (AP-08)
File: app.py:3-4, app.py:6-30, controllers.py:2-3, controllers.py:266, models.py:1
Description: Cada camada importa e chama o `get_db()` concreto diretamente. A app Flask é criada e configurada no momento do import, sem app factory, e o controller de health acessa o banco sem passar pelo model.
Impact: Não dá para trocar o banco em testes nem rodar duas instâncias com configurações diferentes, porque a ordem de import vira a arquitetura.
Recommendation: Criar um app factory `create_app(config)` que monte a conexão e registre Blueprints, com a conexão obtida por request através do contexto da app (PB-08).

### [HIGH] Debug Mode in Production (AP-19)
File: app.py:8, app.py:88
Description: `app.config["DEBUG"] = True` e `app.run(host="0.0.0.0", port=5000, debug=True)` estão fixos no código.
Impact: O debugger do Werkzeug exposto em 0.0.0.0 permite execução remota de código a partir de qualquer página de erro.
Recommendation: Ler DEBUG do ambiente com padrão desligado (PB-19).

### [HIGH] Missing Authentication / Authorization (AP-22)
File: app.py:14-16, app.py:18-19, app.py:24, app.py:26, app.py:28, controllers.py:180
Description: Criar, atualizar e apagar produtos, listar todos os usuários e pedidos, mudar o status de um pedido e ver o relatório de vendas não exigem nenhuma credencial. O login devolve os dados do usuário sem token nem sessão, então não há o que verificar depois, e o campo `tipo` (admin/cliente) nunca é checado.
Impact: Qualquer cliente pode apagar o catálogo, aprovar ou cancelar pedidos alheios e ler dados financeiros.
Recommendation: Introduzir um guard de autenticação/autorização como middleware (PB-04). Restringir rotas públicas existentes muda o contrato, então isso deve ser uma decisão explícita.

### [HIGH] Business Logic in Controller / Route (AP-06)
File: controllers.py:24-62, controllers.py:188-220, controllers.py:237-255
Description: `criar_produto` tem 39 linhas de regras de domínio (faixas de preço e estoque, tamanho do nome, categorias válidas). `criar_pedido` dispara efeitos colaterais (e-mail, SMS, push) direto do handler. `atualizar_status_pedido` define as transições válidas e as notificações por status.
Impact: As regras não podem ser reusadas nem testadas sem o Flask, e já divergem entre criação e atualização de produto.
Recommendation: Mover validação e regras para o model/serviço de cada domínio e notificações para um serviço, deixando o controller só orquestrar (PB-06).

### [HIGH] Mutable Global State (AP-07)
File: database.py:4-11
Description: `db_connection = None` em nível de módulo é reatribuída via `global db_connection` e compartilhada por todas as requests com `check_same_thread=False`.
Impact: Transações de requests concorrentes se misturam (um `commit` de uma request grava escritas pendentes de outra), e o estado vaza entre testes.
Recommendation: Abrir a conexão por request em `flask.g` e fechá-la em `teardown_appcontext` (PB-07).

### [MEDIUM] Missing Input Validation (AP-10)
File: app.py:61-62, controllers.py:43-50, controllers.py:72-90, controllers.py:118-121, controllers.py:153-158, controllers.py:169-171, controllers.py:195-201, controllers.py:239-240
Description: `request.get_json()` é usado sem checar `None` em login, status e admin/query, o que gera AttributeError e resposta 500. `preco < 0` com string gera TypeError (500). `float(preco_min)` inválido também retorna 500. A atualização de produto não valida nome nem categoria como a criação faz. Não há validação do formato do e-mail. Os itens do pedido não são validados: falta de `produto_id` gera KeyError, e `quantidade` negativa passa na checagem de estoque e aumenta o estoque.
Impact: Entradas ruins viram erros 500 ou dados corrompidos (estoque e total negativos) em vez de um 400 claro.
Recommendation: Centralizar validadores por domínio e chamá-los na criação e na atualização, retornando 400 (PB-10).

### [MEDIUM] Broad Exception Handling / Leaked Error Details (AP-11)
File: app.py:77-78, controllers.py:10-12, controllers.py:21-22, controllers.py:60-62, controllers.py:95-96, controllers.py:108-109, controllers.py:125-126, controllers.py:133-134, controllers.py:143-144, controllers.py:164-165 (+7 more)
Description: Todos os handlers repetem `except Exception as e: return jsonify({"erro": str(e)}), 500`, e não existe `@app.errorhandler` centralizado.
Impact: Mensagens internas (SQL, nomes de colunas) vazam para o cliente, e o mesmo try/except está copiado 17 vezes.
Recommendation: Criar um middleware de erros centralizado com exceções de domínio mapeadas para status HTTP e mensagem genérica no 500 (PB-11).

### [MEDIUM] Duplicated Logic (AP-13)
File: controllers.py:28-46, controllers.py:72-90, models.py:12-21, models.py:31-40, models.py:79-86, models.py:95-102, models.py:171-201, models.py:203-233, models.py:304-313
Description: O bloco de validação de produto está copiado entre criação e atualização, e as cópias já divergem. O mapeamento linha→dict de produto aparece 3 vezes, o de usuário 2 vezes, e `get_pedidos_usuario` e `get_todos_pedidos` são idênticas exceto pelo `WHERE`.
Impact: Correções aplicadas num lugar deixam o bug nos outros, como já acontece com a validação de categoria na atualização.
Recommendation: Extrair serializers e validadores únicos por entidade e uma função de listagem de pedidos com filtro opcional (PB-13).

### [MEDIUM] Missing Transaction / Inconsistent Writes (AP-12)
File: models.py:65-70, models.py:133-169
Description: `criar_pedido` insere o pedido, os itens e baixa o estoque sem bloco de transação nem rollback. Se der exceção no meio, as escritas ficam pendentes na conexão global e são gravadas pelo próximo `commit` de outra request. A checagem de estoque e a baixa não são atômicas. `deletar_produto` apaga o produto e deixa `itens_pedido` apontando para ele.
Impact: Pedidos sem itens, estoque negativo sob concorrência e itens órfãos ("Desconhecido").
Recommendation: Envolver a operação numa transação (`with conn:`) com rollback em erro e tratar as referências na exclusão (PB-12).

### [MEDIUM] N+1 Queries (AP-09)
File: models.py:154-156, models.py:187-199, models.py:219-231
Description: Para cada pedido roda uma query de itens e, para cada item, outra de produto. Em `criar_pedido`, o preço de cada produto é buscado de novo depois de já ter sido lido no laço anterior.
Impact: O número de queries cresce com pedidos × itens e degrada a listagem de pedidos.
Recommendation: Buscar itens e nomes de produtos com um JOIN e reaproveitar os produtos já lidos (PB-09).

### [LOW] Magic Numbers / Strings (AP-15)
File: app.py:35, app.py:88, controllers.py:47-50, controllers.py:52, controllers.py:242, controllers.py:285-286, models.py:247-253, models.py:256-262
Description: Faixas de desconto 10000/5000/1000 e percentuais 0.1/0.05/0.02 estão soltos no código. A lista de categorias e a lista de status estão inline, os limites de nome 2/200 também. A porta 5000 é literal, a versão "1.0.0" está duplicada e o ambiente "producao" é fixo.
Impact: Regras de negócio sem nome nem fonte única, fáceis de divergir.
Recommendation: Extrair constantes nomeadas nos módulos de domínio e configuração (PB-15).

### [LOW] Print / console.log as Logging (AP-14)
File: app.py:56, app.py:83-86, controllers.py:8, controllers.py:11, controllers.py:57, controllers.py:61, controllers.py:106, controllers.py:161, controllers.py:179-182, controllers.py:208-210 (+2 more)
Description: `print(` é usado como log em handlers e no boot, incluindo e-mails de usuários em tentativas de login e na criação de conta, e banners `print("=" * 50)`.
Impact: Sem níveis nem timestamps, sem como silenciar, e dados pessoais vão parar no stdout.
Recommendation: Usar o módulo `logging` com logger por módulo e sem dados pessoais (PB-14).

### [LOW] Poor Naming (AP-16)
File: controllers.py:14, controllers.py:56, models.py:187-192, models.py:219-224
Description: `id` sobrescreve o builtin nos parâmetros e variáveis, e há cursores numerados `cursor2`/`cursor3` e o nome abreviado `prod`.
Impact: O leitor precisa deduzir o papel de cada variável, e o builtin `id` fica inacessível no escopo.
Recommendation: Usar nomes de domínio (`produto_id`, `itens_cursor`, `produto`) (PB-16).

### [LOW] Unused Imports / Dead Code (AP-17)
File: database.py:2, models.py:2
Description: `import os` em database.py e `import sqlite3` em models.py nunca são usados.
Impact: Ruído que engana sobre as dependências reais do módulo.
Recommendation: Remover os imports não usados (PB-17).

================================
Total: 20 findings
================================

Note: I found nothing for AP-20 (no API in the deprecated table is used with Flask 3.1.1 / sqlite3) or AP-21. Phases 1 and 2 were read-only, so no file was created or changed.

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
