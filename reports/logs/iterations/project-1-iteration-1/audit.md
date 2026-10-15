# Audit Report — Project 1 (code-smells-project)

Phase 1 and Phase 2 output of `/refactor-arch`, as printed by the skill (transcript: [`logs/project-1-phase12.md`](logs/project-1-phase12.md)).

================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python 3 (version not pinned in the manifest)
Framework:     Flask 3.1.1
Dependencies:  flask==3.1.1, flask-cors==5.0.1
Domain:        API de E-commerce (produtos, usuários, pedidos, relatórios de vendas)
Architecture:  Monolithic — `models.py` e `controllers.py` existem, mas cada um cobre todos os domínios; `models.py` mistura SQL e regras de negócio; `controllers.py` faz validação, notificações e SQL direto; `app.py` registra rotas, executa SQL de admin e sobe o servidor; `database.py` abre a conexão, roda o DDL e o seed
Source files:  4 files analyzed (~780 lines of code)
Database:      SQLite (file `loja.db`) via sqlite3 raw driver (standard library)
DB tables:     produtos, usuarios, pedidos, itens_pedido
Entry point:   app.py (`python app.py`, default port 5000)
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

### [CRITICAL] Hardcoded Credentials (AP-01)
File: app.py:7, controllers.py:289, database.py:76
Description: A `SECRET_KEY` está escrita no código como "minha-chave-super-secreta-123", e o mesmo valor é repetido no health check. O seed também cria o usuário admin com a senha fixa "admin123".
Impact: Qualquer pessoa com acesso ao repositório pode forjar sessões e entrar como administrador. Para trocar o segredo é preciso alterar o código e fazer novo deploy.
Recommendation: Ler os segredos de variáveis de ambiente em um módulo `config`, sem fallback literal em produção, e tirar a senha fixa do admin do seed (PB-01).

### [CRITICAL] God Class / God File (AP-03)
File: app.py:47-78, controllers.py:264-292, database.py:7-86, models.py:1-314
Description: `models.py` reúne SQL de produtos, usuários, pedidos e relatórios, além de regras de negócio como checagem de estoque e faixas de desconto. `controllers.py` cobre todos os domínios e ainda executa SQL direto no health check. `app.py` registra rotas, roda SQL de admin e sobe o servidor. `database.py` cuida da conexão, do DDL e do seed.
Impact: Nenhuma parte pode ser testada ou alterada isoladamente, e qualquer mudança pode afetar todos os recursos.
Recommendation: Separar por camada e por domínio (config, models, controllers, routes, services, middlewares) com um composition root (PB-03).

### [CRITICAL] Unprotected Dangerous Endpoint (AP-04)
File: app.py:47-57, app.py:59-78
Description: `POST /admin/reset-db` apaga todas as tabelas com `DELETE FROM` sem `WHERE`. `POST /admin/query` executa qualquer SQL recebido em `dados["sql"]` com `cursor.execute(query)`. Nenhum dos dois verifica autenticação.
Impact: Qualquer cliente anônimo pode ler todas as tabelas (inclusive senhas), alterar dados ou apagar o banco inteiro.
Recommendation: Proteger as rotas de admin com um guard de token de administrador vindo da configuração e restringir o que elas podem fazer (PB-04).

### [CRITICAL] Sensitive Data Exposure (AP-05)
File: controllers.py:286-289, models.py:79-86, models.py:95-102
Description: O health check devolve `db_path`, `debug` e `secret_key`. A conversão de linha para dicionário de usuários inclui o campo `senha`, então `GET /usuarios` e `GET /usuarios/<id>` retornam as senhas de todos os usuários.
Impact: Um único cliente comprometido ou um proxy registrando respostas expõe todas as contas e o segredo da aplicação.
Recommendation: Tirar `senha` da serialização pública e remover os dados de configuração do health check (PB-05).

### [CRITICAL] Weak Password Hashing (AP-18)
File: database.py:75-83, models.py:109-111, models.py:126-129
Description: As senhas ficam em texto puro: o seed insere "admin123", "123456" e "senha123", `criar_usuario` grava o valor recebido e o login compara `senha = '<entrada>'` direto no SQL.
Impact: Um vazamento do `loja.db` revela todas as senhas, que os usuários costumam reutilizar em outros serviços.
Recommendation: Gerar hash com `werkzeug.security.generate_password_hash` e conferir com `check_password_hash` (o Werkzeug já vem com o Flask) (PB-18).

### [CRITICAL] SQL Injection (AP-02)
File: models.py:28, models.py:47-50, models.py:57-61, models.py:109-111, models.py:126-129, models.py:140, models.py:148-151, models.py:157-166, models.py:279-281, models.py:289-297 (+8 more)
Description: As queries são montadas concatenando valores da requisição, por exemplo `"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"` no login e `query += " AND (nome LIKE '%" + termo + "%' ..."` na busca. O mesmo acontece no cadastro e na edição de produtos, no cadastro de usuários, nos itens de pedido (`produto_id` e `quantidade` vêm do JSON sem checagem de tipo) e nas consultas por id.
Impact: Com `' OR '1'='1` é possível entrar no login sem senha, e qualquer campo de texto permite ler, alterar ou apagar tabelas.
Recommendation: Usar queries parametrizadas com placeholders `?` do sqlite3 em todas as consultas (PB-02).

### [HIGH] Tight Coupling / Missing Dependency Injection (AP-08)
File: app.py:3-4, app.py:6, controllers.py:2-3, models.py:1
Description: O app Flask é criado no import do módulo, sem app factory. Controllers e models importam `get_db` e `models` diretamente, e o controller acessa o banco sem passar pelo model.
Impact: Não dá para trocar o banco ou a configuração em testes, e a ordem dos imports acaba definindo a arquitetura.
Recommendation: Criar um `create_app(config)` como composition root, com a conexão por requisição gerenciada pela factory (PB-08).

### [HIGH] Debug Mode in Production (AP-19)
File: app.py:8, app.py:88
Description: `app.config["DEBUG"] = True` e `app.run(host="0.0.0.0", port=5000, debug=True)` estão fixos no código.
Impact: O debugger do Werkzeug exposto na rede permite execução remota de código a partir de uma página de erro.
Recommendation: Controlar debug, host e porta por variáveis de ambiente, com debug desligado por padrão (PB-19).

### [HIGH] Missing Authentication / Authorization (AP-22)
File: app.py:15, app.py:16, app.py:18, app.py:24, app.py:26, app.py:28, controllers.py:167-186
Description: Editar e apagar produtos, listar todos os usuários e todos os pedidos, mudar o status de pedidos e ver o relatório de vendas não exigem autenticação. O login não emite nenhum token e o campo `tipo` ('admin') nunca é verificado.
Impact: Qualquer cliente pode apagar produtos, mudar status de pedidos e ler dados financeiros e de clientes.
Recommendation: Introduzir um guard de autenticação e autorização (token de admin) nas rotas privilegiadas (PB-04).

### [HIGH] Business Logic in Controller (AP-06)
File: controllers.py:24-62, controllers.py:188-220, controllers.py:237-255
Description: `criar_produto` contém as regras de domínio (faixas de preço e estoque, tamanho do nome, lista de categorias válidas). `criar_pedido` dispara e-mail, SMS e push direto do handler. `atualizar_status_pedido` define os status válidos e as notificações de cada transição.
Impact: As regras não podem ser reutilizadas nem testadas sem o Flask, e já divergem entre criação e atualização.
Recommendation: Levar as regras e os efeitos colaterais para services ou models e deixar o controller só orquestrar (PB-06).

### [HIGH] Mutable Global State (AP-07)
File: database.py:4-11
Description: Uma única conexão SQLite global (`db_connection`, reatribuída com `global`) é compartilhada por todas as requisições com `check_same_thread=False`.
Impact: Requisições concorrentes dividem a mesma transação: um `commit` de uma requisição grava escritas pendentes de outra, e as condições de corrida são difíceis de reproduzir.
Recommendation: Abrir uma conexão por requisição em `flask.g` e fechá-la no teardown do app (PB-07).

### [MEDIUM] Broad Exception Handling / Leaked Error Details (AP-11)
File: app.py:77-78, controllers.py:10-12, controllers.py:21-22, controllers.py:60-62, controllers.py:95-96, controllers.py:108-109, controllers.py:125-126, controllers.py:133-134, controllers.py:143-144, controllers.py:164-165 (+7 more)
Description: Cada handler repete `except Exception as e: return jsonify({"erro": str(e)}), 500`, e não existe um `@app.errorhandler` central.
Impact: Mensagens internas (SQL, nomes de tabela) chegam ao cliente, e erros de entrada viram 500 em vez de 400.
Recommendation: Centralizar o tratamento de erros em handlers registrados no app, com exceções de domínio mapeadas para os status corretos (PB-11).

### [MEDIUM] Duplicated Logic (AP-13)
File: controllers.py:28-46, controllers.py:72-90, models.py:12-21, models.py:31-40, models.py:79-86, models.py:95-102, models.py:171-201, models.py:203-233, models.py:304-313
Description: O bloco de validação de produto foi copiado entre criação e atualização. A conversão de linha para dicionário de produto aparece três vezes e a de usuário duas. A montagem de pedidos com itens está duplicada em `get_pedidos_usuario` e `get_todos_pedidos`.
Impact: As cópias já divergem (a atualização não valida nome nem categoria) e uma correção feita em um lugar deixa o bug nos outros.
Recommendation: Extrair serializadores, validadores e a montagem de pedidos para funções únicas (PB-13).

### [MEDIUM] Missing Input Validation (AP-10)
File: controllers.py:43-46, controllers.py:72-90, controllers.py:118-121, controllers.py:169-170, controllers.py:196-201, controllers.py:239-240
Description: `preco` e `estoque` são comparados com `< 0` sem checar o tipo (uma string causa TypeError). A atualização não valida nome nem categoria. `float(preco_min)` falha com texto. `dados.get` é chamado com corpo vazio (None) no login e no status. Os itens do pedido não são validados (`produto_id` ou `quantidade` ausentes ou inválidos), e não há checagem do formato de e-mail.
Impact: Entradas inválidas viram 500 ou dados corrompidos em vez de um 400 claro.
Recommendation: Validadores únicos com checagem de tipo, faixa e formato, usados na criação e na atualização (PB-10).

### [MEDIUM] Missing Transaction / Inconsistent Writes (AP-12)
File: models.py:65-70, models.py:139-168
Description: `criar_pedido` faz o INSERT do pedido, os INSERTs dos itens e os UPDATEs de estoque sem transação explícita nem rollback, e a checagem de estoque é separada do decremento. `deletar_produto` apaga o produto e deixa linhas órfãs em `itens_pedido`.
Impact: Uma falha no meio deixa pedidos sem itens ou estoque decrementado pela metade, e na conexão compartilhada essas escritas pendentes podem ser gravadas pelo commit de outra requisição.
Recommendation: Rodar as escritas dependentes em uma transação com commit e rollback (PB-12).

### [MEDIUM] N+1 Queries (AP-09)
File: models.py:139-141, models.py:154-156, models.py:177-200, models.py:209-232
Description: Para cada pedido é executada uma query de itens e, para cada item, outra para buscar o nome do produto. `criar_pedido` também consulta o produto duas vezes por item.
Impact: O número de queries cresce com pedidos × itens e torna lentas as listagens de pedidos.
Recommendation: Buscar pedidos, itens e produtos com JOIN e agrupar em memória (PB-09).

### [LOW] Print as Logging (AP-14)
File: app.py:56, app.py:83-86, controllers.py:8, controllers.py:11, controllers.py:57, controllers.py:61, controllers.py:106, controllers.py:161, controllers.py:179, controllers.py:182 (+4 more)
Description: São 19 chamadas a `print(...)` para eventos, erros, "notificações" e o banner de boot, incluindo e-mails de usuários em claro.
Impact: Os logs não têm nível nem timestamp e não podem ser silenciados ou redirecionados, e dados pessoais vão parar no stdout.
Recommendation: Usar o módulo `logging` com logger por módulo e níveis adequados (PB-14).

### [LOW] Magic Numbers / Strings (AP-15)
File: app.py:88, controllers.py:47-50, controllers.py:52, controllers.py:242, controllers.py:285-287, models.py:247-253, models.py:256-262
Description: As faixas de desconto (10000/5000/1000, com 0.1/0.05/0.02), os limites de nome (2 e 200), as listas de categorias e status, a porta 5000 e os valores "producao" e "loja.db" estão soltos no código.
Impact: As regras de negócio não têm nome nem fonte única e são fáceis de divergir.
Recommendation: Extrair constantes nomeadas no módulo de domínio e na configuração (PB-15).

### [LOW] Poor Naming (AP-16)
File: controllers.py:14, controllers.py:56, models.py:187, models.py:191, models.py:219, models.py:223
Description: Os nomes `cursor2` e `cursor3` não dizem o que cada cursor consulta, e `id` sobrescreve a builtin do Python nos parâmetros e variáveis.
Impact: Quem lê o código precisa descobrir o significado de cada variável, e sobrescrever builtins esconde erros.
Recommendation: Usar nomes de domínio (`produto_id`, `itens_cursor`) (PB-16).

### [LOW] Unused Imports / Dead Code (AP-17)
File: database.py:2, models.py:2
Description: `import os` em `database.py` e `import sqlite3` em `models.py` nunca são usados.
Impact: Esses imports são ruído e enganam sobre as dependências reais de cada módulo.
Recommendation: Remover os imports não usados (PB-17).

================================
Total: 20 findings
================================

No Deprecated-API findings: SQLAlchemy and the Flask APIs removed in 2.3 are not used, and `sqlite3` is opened without `detect_types`, so the deprecated default datetime adapters are not used either. No file has been created or changed.

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
