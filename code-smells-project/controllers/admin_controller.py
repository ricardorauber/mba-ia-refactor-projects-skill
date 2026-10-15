import logging

from middlewares.errors import ValidationError
from models import sistema_model

logger = logging.getLogger(__name__)


def resetar_banco():
    sistema_model.resetar_banco()
    logger.warning("Banco de dados resetado via /admin/reset-db")


def consultar(payload):
    """Narrowed SQL console: one read-only SELECT statement."""
    sql = payload.get("sql", "") if isinstance(payload, dict) else ""
    if not sql or not isinstance(sql, str):
        raise ValidationError("Query não informada")
    statement = sql.strip().rstrip(";").strip()
    if not statement.upper().startswith("SELECT") or ";" in statement:
        raise ValidationError("Apenas uma consulta SELECT é permitida")
    try:
        return sistema_model.executar_consulta_leitura(statement)
    except sistema_model.ConsultaInvalidaError as error:
        logger.info("Consulta admin rejeitada: %s", error)
        raise ValidationError("Consulta inválida") from error
