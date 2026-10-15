from database import get_db
from models.pedido_model import STATUS_APROVADO, STATUS_CANCELADO, STATUS_PENDENTE

# (faturamento mínimo exclusivo, taxa de desconto), da maior faixa para a menor
FAIXAS_DESCONTO = ((10000, 0.10), (5000, 0.05), (1000, 0.02))
CASAS_DECIMAIS = 2


def desconto_para(faturamento):
    return next((faturamento * taxa for minimo, taxa in FAIXAS_DESCONTO if faturamento > minimo), 0)


def resumo_vendas():
    row = get_db().execute(
        """SELECT COUNT(*) AS total_pedidos,
                  COALESCE(SUM(total), 0) AS faturamento,
                  COALESCE(SUM(status = ?), 0) AS pendentes,
                  COALESCE(SUM(status = ?), 0) AS aprovados,
                  COALESCE(SUM(status = ?), 0) AS cancelados
           FROM pedidos""",
        (STATUS_PENDENTE, STATUS_APROVADO, STATUS_CANCELADO),
    ).fetchone()

    total_pedidos = row["total_pedidos"]
    faturamento = row["faturamento"]
    desconto = desconto_para(faturamento)
    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, CASAS_DECIMAIS),
        "desconto_aplicavel": round(desconto, CASAS_DECIMAIS),
        "faturamento_liquido": round(faturamento - desconto, CASAS_DECIMAIS),
        "pedidos_pendentes": row["pendentes"],
        "pedidos_aprovados": row["aprovados"],
        "pedidos_cancelados": row["cancelados"],
        "ticket_medio": round(faturamento / total_pedidos, CASAS_DECIMAIS) if total_pedidos > 0 else 0,
    }
