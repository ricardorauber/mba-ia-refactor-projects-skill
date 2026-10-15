import logging

from controllers.validators import validar_login, validar_usuario
from middlewares.errors import NotFoundError, UnauthorizedError
from models import usuario_model
from services import password_service

logger = logging.getLogger(__name__)


def listar():
    return usuario_model.listar()


def buscar(usuario_id):
    usuario = usuario_model.buscar_por_id(usuario_id)
    if not usuario:
        raise NotFoundError("Usuário não encontrado")
    return usuario


def criar(payload):
    dados = validar_usuario(payload)
    usuario_id = usuario_model.criar(dados["nome"], dados["email"], password_service.hash_password(dados["senha"]))
    logger.info("Usuário criado: id=%s", usuario_id)
    return usuario_id


def autenticar(payload):
    credenciais = validar_login(payload)
    for row in usuario_model.buscar_credenciais_por_email(credenciais["email"]):
        confere, precisa_rehash = password_service.verify_password(row["senha"], credenciais["senha"])
        if confere:
            if precisa_rehash:
                usuario_model.atualizar_senha(row["id"], password_service.hash_password(credenciais["senha"]))
            logger.info("Login bem-sucedido: usuario_id=%s", row["id"])
            return usuario_model.to_dict(row, usuario_model.CAMPOS_LOGIN)
    logger.info("Login falhou")
    raise UnauthorizedError("Email ou senha inválidos", sucesso=False)
