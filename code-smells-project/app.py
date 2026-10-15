import logging

from flask import Flask
from flask_cors import CORS

from config import Settings
from database import close_db, init_db
from middlewares.error_handler import register_error_handlers
from views import BLUEPRINTS

logger = logging.getLogger(__name__)


def create_app(settings=None):
    """Composition root: config -> database -> blueprints -> error handlers."""
    settings = settings or Settings()
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=settings.secret_key,
        DEBUG=settings.debug,
        DATABASE_PATH=settings.database_path,
        ADMIN_TOKEN=settings.admin_token,
        APP_ENV=settings.environment,
    )
    CORS(app)

    init_db(settings.database_path)
    app.teardown_appcontext(close_db)

    for blueprint in BLUEPRINTS:
        app.register_blueprint(blueprint)
    register_error_handlers(app)
    return app


def configure_logging(level):
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


if __name__ == "__main__":
    settings = Settings()
    configure_logging(settings.log_level)
    application = create_app(settings)
    logger.info("Servidor iniciado em http://%s:%s", settings.host, settings.port)
    application.run(host=settings.host, port=settings.port, debug=settings.debug)
