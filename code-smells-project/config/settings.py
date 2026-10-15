import logging
import os
import secrets

API_VERSION = "1.0.0"

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 5000
DEFAULT_DATABASE_PATH = "loja.db"
DEFAULT_ENVIRONMENT = "producao"


class Settings:
    """Every setting comes from the environment; secrets have no literal default."""

    def __init__(self, env=os.environ):
        self.host = env.get("HOST", DEFAULT_HOST)
        self.port = int(env.get("PORT", DEFAULT_PORT))
        self.debug = env.get("FLASK_DEBUG", "0") == "1"
        self.database_path = env.get("DATABASE_PATH", DEFAULT_DATABASE_PATH)
        self.environment = env.get("APP_ENV", DEFAULT_ENVIRONMENT)
        self.log_level = env.get("LOG_LEVEL", "INFO").upper()
        self.admin_token = env.get("ADMIN_TOKEN", "")
        self.secret_key = env.get("SECRET_KEY") or self._ephemeral("SECRET_KEY")

    @staticmethod
    def _ephemeral(name):
        logging.getLogger(__name__).warning("%s is not set; using an ephemeral value", name)
        return secrets.token_hex(32)
