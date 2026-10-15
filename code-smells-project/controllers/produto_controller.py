import logging

from controllers.validators import validar_filtros_busca, validar_produto
from middlewares.errors import NotFoundError
from models import produto_model

logger = logging.getLogger(__name__)

PRODUTO_NAO_ENCONTRADO = "Produto não encontrado"


def listar():
    produtos = produto_model.listar()
    logger.info("Listando %s produtos", len(produtos))
    return produtos


def buscar(produto_id):
    produto = produto_model.buscar_por_id(produto_id)
    if not produto:
        raise NotFoundError(PRODUTO_NAO_ENCONTRADO, sucesso=False)
    return produto


def pesquisar(args):
    return produto_model.pesquisar(**validar_filtros_busca(args))


def criar(payload):
    dados = validar_produto(payload)
    produto_id = produto_model.criar(**dados)
    logger.info("Produto criado: id=%s", produto_id)
    return produto_id


def atualizar(produto_id, payload):
    if not produto_model.buscar_por_id(produto_id):
        raise NotFoundError(PRODUTO_NAO_ENCONTRADO)
    produto_model.atualizar(produto_id, **validar_produto(payload))


def remover(produto_id):
    if not produto_model.buscar_por_id(produto_id):
        raise NotFoundError(PRODUTO_NAO_ENCONTRADO)
    produto_model.desativar(produto_id)
    logger.info("Produto removido: id=%s", produto_id)
