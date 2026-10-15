import logging
import os
import secrets

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 5000
DEFAULT_DATABASE_URL = "sqlite:///tasks.db"  # Flask-SQLAlchemy stores it in instance/tasks.db

logger = logging.getLogger(__name__)


class Settings:
    """Every setting of the application, read from the environment."""

    def __init__(self, env=os.environ):
        self.host = env.get("HOST", DEFAULT_HOST)
        self.port = int(env.get("PORT", DEFAULT_PORT))
        self.debug = env.get("FLASK_DEBUG", "0") == "1"
        self.log_level = env.get("LOG_LEVEL", "INFO").upper()
        self.database_url = self._database_url(env)
        self.secret_key = env.get("SECRET_KEY") or self._ephemeral("SECRET_KEY")

    @staticmethod
    def _database_url(env):
        if env.get("DATABASE_URL"):
            return env["DATABASE_URL"]
        if env.get("DATABASE_PATH"):
            return "sqlite:///" + os.path.abspath(env["DATABASE_PATH"])
        return DEFAULT_DATABASE_URL

    @staticmethod
    def _ephemeral(name):
        logger.warning("%s is not set; using an ephemeral value", name)
        return secrets.token_hex(32)
