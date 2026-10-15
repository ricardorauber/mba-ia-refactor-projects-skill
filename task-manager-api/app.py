import logging

from flask import Flask
from flask_cors import CORS

from config import Settings
from database import db
from middlewares.error_handler import register_error_handlers
from routes.category_routes import category_bp
from routes.report_routes import report_bp
from routes.system_routes import system_bp
from routes.task_routes import task_bp
from routes.user_routes import user_bp

BLUEPRINTS = (system_bp, task_bp, user_bp, report_bp, category_bp)


def create_app(settings=None):
    settings = settings or Settings()
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI=settings.database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY=settings.secret_key,
    )

    CORS(app)
    db.init_app(app)
    register_error_handlers(app)
    for blueprint in BLUEPRINTS:
        app.register_blueprint(blueprint)

    with app.app_context():
        db.create_all()
    return app


if __name__ == '__main__':
    settings = Settings()
    logging.basicConfig(level=settings.log_level, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
    create_app(settings).run(host=settings.host, port=settings.port, debug=settings.debug)
