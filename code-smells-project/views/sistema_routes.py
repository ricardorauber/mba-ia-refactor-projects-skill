from flask import Blueprint, current_app, jsonify

from controllers import sistema_controller

bp = Blueprint("sistema", __name__)


@bp.get("/")
def index():
    return jsonify(sistema_controller.indice())


@bp.get("/health")
def health_check():
    corpo, saudavel = sistema_controller.health(current_app.config["APP_ENV"])
    return jsonify(corpo), 200 if saudavel else 500
