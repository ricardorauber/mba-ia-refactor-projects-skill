from flask import Blueprint, jsonify, request

from controllers import admin_controller
from middlewares.auth import require_admin_token

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.post("/reset-db")
@require_admin_token
def reset_database():
    admin_controller.resetar_banco()
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200


@bp.post("/query")
@require_admin_token
def executar_query():
    dados = admin_controller.consultar(request.get_json(silent=True))
    return jsonify({"dados": dados, "sucesso": True}), 200
