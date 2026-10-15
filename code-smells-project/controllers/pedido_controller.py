from controllers.validators import validar_pedido, validar_status
from middlewares.errors import ValidationError
from models import pedido_model
from services import notification_service


def criar(payload):
    dados = validar_pedido(payload)
    try:
        resultado = pedido_model.criar(dados["usuario_id"], dados["itens"])
    except pedido_model.PedidoInvalidoError as error:
        raise ValidationError(str(error), sucesso=False) from error
    notification_service.pedido_criado(resultado["pedido_id"], dados["usuario_id"])
    return resultado


def listar_todos():
    return pedido_model.listar()


def listar_por_usuario(usuario_id):
    return pedido_model.listar(usuario_id)


def atualizar_status(pedido_id, payload):
    novo_status = validar_status(payload)
    pedido_model.atualizar_status(pedido_id, novo_status)
    notification_service.status_pedido_alterado(pedido_id, novo_status)
