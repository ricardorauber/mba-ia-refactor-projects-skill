# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`. O projeto foi reorganizado em MVC: `config/` (configuração por variáveis de ambiente), `models/` (entidades, regras de domínio e consultas), `controllers/` (fluxo de cada caso de uso e validação), `routes/` (blueprints HTTP), `middlewares/` (erros de domínio e tratamento centralizado) e `app.py` (composition root com `create_app()`).

## Como rodar

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python seed.py
.venv/bin/python app.py
```

A aplicação sobe em `http://localhost:5000`. O `seed.py` popula o banco SQLite (`instance/tasks.db`) com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**, caso contrário os endpoints vão retornar listas vazias. Os logins do seed continuam os mesmos (por exemplo `joao@email.com` / `1234`).

## Configuração

Todas as variáveis são opcionais (veja `.env.example`):

| Variável | Padrão | Uso |
|---|---|---|
| `PORT` / `HOST` | `5000` / `0.0.0.0` | Endereço do servidor |
| `FLASK_DEBUG` | `0` | `1` liga o debugger do Flask (somente desenvolvimento) |
| `LOG_LEVEL` | `INFO` | Nível do `logging` |
| `SECRET_KEY` | aleatória a cada boot | Chave de assinatura do Flask |
| `DATABASE_URL` / `DATABASE_PATH` | `sqlite:///tasks.db` | Banco de dados (`DATABASE_PATH` aceita um caminho de arquivo SQLite) |

## Smoke test

```bash
.venv/bin/python tests/smoke_test.py
```

Sobe a aplicação em uma porta livre com um banco temporário, roda o seed e chama todos os endpoints.
