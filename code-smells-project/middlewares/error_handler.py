import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from middlewares.errors import AppError

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(error):
        body = {"erro": error.message}
        if error.sucesso is not None:
            body["sucesso"] = error.sucesso
        return jsonify(body), error.status_code

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        return jsonify({"erro": error.description}), error.code

    @app.errorhandler(Exception)
    def handle_unexpected(_error):
        logger.exception("Unhandled error")
        return jsonify({"erro": "Erro interno do servidor"}), 500
