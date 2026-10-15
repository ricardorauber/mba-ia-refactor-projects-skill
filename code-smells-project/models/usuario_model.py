from database import get_db

TIPO_CLIENTE = "cliente"

CAMPOS_PUBLICOS = ("id", "nome", "email", "tipo", "criado_em")
CAMPOS_LOGIN = ("id", "nome", "email", "tipo")


def to_dict(row, campos=CAMPOS_PUBLICOS):
    return {campo: row[campo] for campo in campos}


def listar():
    rows = get_db().execute("SELECT * FROM usuarios ORDER BY id").fetchall()
    return [to_dict(row) for row in rows]


def buscar_por_id(usuario_id):
    row = get_db().execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    return to_dict(row) if row else None


def buscar_credenciais_por_email(email):
    """Internal rows including the password hash; never serialize them directly."""
    return get_db().execute("SELECT * FROM usuarios WHERE email = ? ORDER BY id", (email,)).fetchall()


def criar(nome, email, senha_hash, tipo=TIPO_CLIENTE):
    db = get_db()
    with db:
        cursor = db.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            (nome, email, senha_hash, tipo),
        )
    return cursor.lastrowid


def atualizar_senha(usuario_id, senha_hash):
    db = get_db()
    with db:
        db.execute("UPDATE usuarios SET senha = ? WHERE id = ?", (senha_hash, usuario_id))
