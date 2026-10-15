# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
npm install
npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória e já carrega seeds automaticamente no boot.

Exemplos de requisições estão em `api.http`.

## Configuração

Todas as configurações vêm de variáveis de ambiente (veja `.env.example`):

| Variável | Padrão | Uso |
|---|---|---|
| `PORT` / `HOST` | `3000` / `0.0.0.0` | Porta e host do servidor |
| `DATABASE_PATH` | `:memory:` | Caminho do banco SQLite (o seed roda só quando o banco está vazio) |
| `ADMIN_TOKEN` | vazio | Token exigido no header `X-Admin-Token` das rotas `/api/admin/*`; sem ele configurado essas rotas respondem `403` |
| `PAYMENT_GATEWAY_KEY` | gerada em memória | Chave do gateway de pagamento |
| `LOG_LEVEL` | `info` | `error`, `warn`, `info` ou `silent` |

```bash
ADMIN_TOKEN=minha-chave npm start
curl -H "X-Admin-Token: minha-chave" http://localhost:3000/api/admin/financial-report
```

## Estrutura

```
src/
├── app.js              # composition root (createApp + listen)
├── config/settings.js  # variáveis de ambiente
├── database/           # conexão promisificada, transações, schema e seed
├── models/             # acesso a dados por entidade
├── controllers/        # fluxo dos casos de uso e validação
├── services/           # pagamento e hash de senha
├── routes/             # mapeamento HTTP
├── middlewares/        # erros centralizados, token admin, async handler
└── utils/logger.js
```

## Testes

```bash
npm test   # node --test tests/
```
