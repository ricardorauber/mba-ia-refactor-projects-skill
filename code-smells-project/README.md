# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python app.py
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo (senhas gravadas com hash).

### Variáveis de ambiente

Todas são opcionais; veja `.env.example`.

| Variável | Padrão | Uso |
|---|---|---|
| `HOST` / `PORT` | `0.0.0.0` / `5000` | Endereço do servidor |
| `FLASK_DEBUG` | `0` | `1` liga o modo debug (nunca em produção) |
| `DATABASE_PATH` | `loja.db` | Arquivo SQLite |
| `APP_ENV` | `producao` | Ambiente informado no `/health` |
| `LOG_LEVEL` | `INFO` | Nível de log |
| `SECRET_KEY` | gerada a cada boot | Chave da aplicação |
| `ADMIN_TOKEN` | vazio | Libera as rotas `/admin/*` via header `X-Admin-Token`; sem ele, essas rotas respondem 403 |

As rotas `/admin/reset-db` e `/admin/query` exigem o header `X-Admin-Token`. O `/admin/query` aceita apenas um único `SELECT`, que roda numa conexão somente leitura.

## Estrutura

```
app.py            composition root (create_app)
config/           configurações lidas do ambiente
database.py       conexão por request, schema e seed
models/           acesso a dados e regras de domínio
controllers/      fluxo de cada caso de uso e validação
views/            Blueprints (rotas HTTP)
services/         notificações e hash de senha
middlewares/      tratamento de erros e guard de admin
tests/            smoke test
```

## Smoke test

```bash
.venv/bin/python tests/smoke_test.py
```

O teste sobe a aplicação numa porta livre, com banco temporário, e chama todos os endpoints.
