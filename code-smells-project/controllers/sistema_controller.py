import logging

from config import API_VERSION
from models import sistema_model

logger = logging.getLogger(__name__)

ENDPOINTS_PUBLICOS = {
    "produtos": "/produtos",
    "usuarios": "/usuarios",
    "pedidos": "/pedidos",
    "login": "/login",
    "relatorios": "/relatorios/vendas",
    "health": "/health",
}


def indice():
    return {"mensagem": "Bem-vindo à API da Loja", "versao": API_VERSION, "endpoints": ENDPOINTS_PUBLICOS}


def health(ambiente):
    """Return (body, healthy). Reports status only: no secrets, paths or debug flags."""
    try:
        contagens = sistema_model.contar_registros()
    except Exception:
        logger.exception("Health check falhou")
        return {"status": "erro", "detalhes": "Banco de dados indisponível"}, False
    return {
        "status": "ok",
        "database": "connected",
        "counts": contagens,
        "versao": API_VERSION,
        "ambiente": ambiente,
    }, True
