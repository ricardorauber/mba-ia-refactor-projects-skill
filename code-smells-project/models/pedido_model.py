from collections import defaultdict

from database import get_db
from models.produto_model import ATIVO

STATUS_PENDENTE = "pendente"
STATUS_APROVADO = "aprovado"
STATUS_CANCELADO = "cancelado"
STATUS_VALIDOS = (STATUS_PENDENTE, STATUS_APROVADO, "enviado", "entregue", STATUS_CANCELADO)

PRODUTO_DESCONHECIDO = "Desconhecido"


class PedidoInvalidoError(Exception):
    pass


def _produtos_por_id(db, produto_ids):
    marcadores = ",".join("?" * len(produto_ids))
    rows = db.execute(
        f"SELECT id, nome, preco, estoque FROM produtos WHERE ativo = ? AND id IN ({marcadores})",
        [ATIVO, *produto_ids],
    ).fetchall()
    return {row["id"]: row for row in rows}


def criar(usuario_id, itens):
    """Create the order, its items and the stock decrement in one transaction.

    `itens` is a list of (produto_id, quantidade). Raises PedidoInvalidoError when a product
    is missing or out of stock; nothing is written in that case.
    """
    db = get_db()
    produtos = _produtos_por_id(db, sorted({produto_id for produto_id, _ in itens}))

    total = 0
    for produto_id, quantidade in itens:
        produto = produtos.get(produto_id)
        if produto is None:
            raise PedidoInvalidoError(f"Produto {produto_id} não encontrado")
        if produto["estoque"] < quantidade:
            raise PedidoInvalidoError(f"Estoque insuficiente para {produto['nome']}")
        total = total + produto["preco"] * quantidade

    with db:
        pedido_id = db.execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
            (usuario_id, STATUS_PENDENTE, total),
        ).lastrowid
        db.executemany(
            "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
            [(pedido_id, produto_id, quantidade, produtos[produto_id]["preco"]) for produto_id, quantidade in itens],
        )
        for produto_id, quantidade in itens:
            baixa = db.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
                (quantidade, produto_id, quantidade),
            )
            if baixa.rowcount == 0:
                raise PedidoInvalidoError(f"Estoque insuficiente para {produtos[produto_id]['nome']}")

    return {"pedido_id": pedido_id, "total": total}


def listar(usuario_id=None):
    """Orders with their items in two queries (no query per order or per item)."""
    db = get_db()
    filtro, parametros = ("WHERE usuario_id = ?", (usuario_id,)) if usuario_id is not None else ("", ())

    pedidos = db.execute(f"SELECT * FROM pedidos {filtro} ORDER BY id", parametros).fetchall()
    if not pedidos:
        return []

    itens_rows = db.execute(
        f"""SELECT i.pedido_id, i.produto_id, i.quantidade, i.preco_unitario, p.nome AS produto_nome
            FROM itens_pedido i
            LEFT JOIN produtos p ON p.id = i.produto_id
            WHERE i.pedido_id IN (SELECT id FROM pedidos {filtro})
            ORDER BY i.id""",
        parametros,
    ).fetchall()

    itens_por_pedido = defaultdict(list)
    for item in itens_rows:
        itens_por_pedido[item["pedido_id"]].append({
            "produto_id": item["produto_id"],
            "produto_nome": item["produto_nome"] or PRODUTO_DESCONHECIDO,
            "quantidade": item["quantidade"],
            "preco_unitario": item["preco_unitario"],
        })

    return [
        {
            "id": pedido["id"],
            "usuario_id": pedido["usuario_id"],
            "status": pedido["status"],
            "total": pedido["total"],
            "criado_em": pedido["criado_em"],
            "itens": itens_por_pedido[pedido["id"]],
        }
        for pedido in pedidos
    ]


def atualizar_status(pedido_id, novo_status):
    db = get_db()
    with db:
        db.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
