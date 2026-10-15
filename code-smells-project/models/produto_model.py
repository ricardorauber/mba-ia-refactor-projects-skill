from database import get_db

CATEGORIAS_VALIDAS = ("informatica", "moveis", "vestuario", "geral", "eletronicos", "livros")
CATEGORIA_PADRAO = "geral"
NOME_MIN = 2
NOME_MAX = 200

ATIVO = 1
INATIVO = 0

CAMPOS_PUBLICOS = ("id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em")


def to_dict(row):
    return {campo: row[campo] for campo in CAMPOS_PUBLICOS}


def listar():
    rows = get_db().execute("SELECT * FROM produtos WHERE ativo = ? ORDER BY id", (ATIVO,)).fetchall()
    return [to_dict(row) for row in rows]


def buscar_por_id(produto_id):
    row = get_db().execute(
        "SELECT * FROM produtos WHERE id = ? AND ativo = ?", (produto_id, ATIVO)
    ).fetchone()
    return to_dict(row) if row else None


def criar(nome, descricao, preco, estoque, categoria):
    db = get_db()
    with db:
        cursor = db.execute(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            (nome, descricao, preco, estoque, categoria),
        )
    return cursor.lastrowid


def atualizar(produto_id, nome, descricao, preco, estoque, categoria):
    db = get_db()
    with db:
        db.execute(
            "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
            (nome, descricao, preco, estoque, categoria, produto_id),
        )


def desativar(produto_id):
    """Soft delete: order items keep pointing to an existing row."""
    db = get_db()
    with db:
        db.execute("UPDATE produtos SET ativo = ? WHERE id = ?", (INATIVO, produto_id))


def pesquisar(termo="", categoria=None, preco_min=None, preco_max=None):
    clausulas, parametros = ["ativo = ?"], [ATIVO]
    if termo:
        clausulas.append("(nome LIKE ? OR descricao LIKE ?)")
        parametros += [f"%{termo}%", f"%{termo}%"]
    if categoria:
        clausulas.append("categoria = ?")
        parametros.append(categoria)
    if preco_min is not None:
        clausulas.append("preco >= ?")
        parametros.append(preco_min)
    if preco_max is not None:
        clausulas.append("preco <= ?")
        parametros.append(preco_max)
    sql = "SELECT * FROM produtos WHERE " + " AND ".join(clausulas) + " ORDER BY id"
    return [to_dict(row) for row in get_db().execute(sql, parametros).fetchall()]
