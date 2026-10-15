import sqlite3

from database import get_db, get_read_only_db
from models.produto_model import ATIVO

# Children first, so no row is left pointing to a deleted parent
TABELAS_RESET = ("itens_pedido", "pedidos", "produtos", "usuarios")


class ConsultaInvalidaError(Exception):
    pass


def contar_registros():
    row = get_db().execute(
        """SELECT (SELECT COUNT(*) FROM produtos WHERE ativo = ?) AS produtos,
                  (SELECT COUNT(*) FROM usuarios) AS usuarios,
                  (SELECT COUNT(*) FROM pedidos) AS pedidos""",
        (ATIVO,),
    ).fetchone()
    return {"produtos": row["produtos"], "usuarios": row["usuarios"], "pedidos": row["pedidos"]}


def resetar_banco():
    db = get_db()
    with db:
        for tabela in TABELAS_RESET:
            db.execute(f"DELETE FROM {tabela}")  # fixed table names, no user input


def executar_consulta_leitura(sql):
    """Run one statement on a connection with query_only enabled, so writes are refused."""
    connection = get_read_only_db()
    try:
        return [dict(row) for row in connection.execute(sql).fetchall()]
    except sqlite3.Error as error:
        raise ConsultaInvalidaError(str(error)) from error
    finally:
        connection.close()
