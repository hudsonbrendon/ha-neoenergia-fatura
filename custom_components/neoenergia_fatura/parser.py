"""Parser dos PDFs da Neoenergia (fatura digital e demonstrativo de GD).

Trabalha sobre o texto extraido pelo pypdf. Os layouts vieram de PDFs reais da
Neoenergia Cosern. Numeros seguem o formato pt-BR (1.234,56). Sem dependencia
do Home Assistant, para ser testavel isoladamente.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any

_NUM = r"-?[\d.]+,\d+"
_MESES = {
    "jan": 1, "fev": 2, "mar": 3, "abr": 4, "mai": 5, "jun": 6,
    "jul": 7, "ago": 8, "set": 9, "out": 10, "nov": 11, "dez": 12,
}


def br_float(value: str | None) -> float | None:
    """'4.158,00' -> 4158.0."""
    if value is None:
        return None
    try:
        return float(value.strip().replace(".", "").replace(",", "."))
    except ValueError:
        return None


def br_date(value: str | None) -> date | None:
    """'23/11/2026' -> date."""
    if not value:
        return None
    try:
        return datetime.strptime(value.strip(), "%d/%m/%Y").date()
    except ValueError:
        return None


def _search(pattern: str, text: str, flags: int = 0) -> str | None:
    m = re.search(pattern, text, flags)
    return m.group(1) if m else None


def parse_fatura(text: str) -> dict[str, Any]:
    """Extrai os campos da fatura digital (DANFE de energia)."""
    data: dict[str, Any] = {
        "referencia": _search(r"REF:MÊS/ANO\s*\n\s*(\d{2}/\d{4})", text),
        "vencimento": br_date(
            _search(r"\nVENCIMENTO\s*\n\s*(\d{2}/\d{2}/\d{4})", text)
        ),
        "valor": br_float(_search(rf"TOTAL A PAGAR R\$\s*\n?\s*({_NUM})", text)),
        "uc": _search(r"NÚMERO DA UNIDADE CONSUMIDORA\s*\n\s*([\d.\-]+)", text),
        "codigo_cliente": _search(r"CÓD\. DÉBITO EM CONTA\s*\n\s*(\d+)", text)
        or _search(r"CÓDIGO DÉBITO EM CONTA (\d+)", text),
        "classificacao": _search(r"CLASSIFICAÇÃO:\s*(.+?)\s{2,}TIPO", text),
        "bandeira": _search(r"bandeira em vigor é a\s+(\w+)", text),
        "nota_fiscal": _search(r"NOTA FISCAL N°\s*(\d+)", text),
        "leitura_anterior": _search(r"LEITURA ANTERIOR (\d{2}/\d{2}/\d{4})", text),
        "leitura_atual": _search(r"LEITURA ATUAL (\d{2}/\d{2}/\d{4})", text),
        "proxima_leitura": _search(r"PRÓXIMA LEITURA (\d{2}/\d{2}/\d{4})", text),
        "dias_faturados": _search(r"N° DE DIAS\s+(\d+)", text),
        "linha_digitavel": _search(
            r"(\d{5}\.\d{5}\s+\d{5}\.\d{6}\s+\d{5}\.\d{6}\s+\d\s+\d{14})", text
        ),
    }
    # Consumo faturado do mes (primeira linha da tabela CONSUMO / kWh)
    consumo = _search(
        r"CONSUMO FATURADO\s+N°DIAS FAT\s*\n\s*\w+\s+(\d+)", text
    )
    data["consumo_kwh"] = int(consumo) if consumo else None

    # Medidor: energia ativa consumida e injetada
    data["energia_ativa_kwh"] = br_float(
        _search(rf"Energia Ativa\s+Único\s+{_NUM}\s+{_NUM}\s+{_NUM}\s+({_NUM})", text)
    )
    data["energia_injetada_kwh"] = br_float(
        _search(
            rf"Energia Ativa Injetada\s+Único\s+{_NUM}\s+{_NUM}\s+{_NUM}\s+({_NUM})",
            text,
        )
    )
    # Saldo de creditos de geracao (bloco "Saldo ... total")
    data["saldo_creditos_kwh"] = br_float(
        _search(r"Saldo atual total\s*=\s*([\d.,]+)", text)
    )
    data["energia_compensada_kwh"] = br_float(
        _search(r"Energia compensada total\s*=\s*([\d.,]+)", text)
    )
    data["excedente_mes_kwh"] = br_float(
        _search(r"Excedente do mês\s*=\s*([\d.,]+)", text)
    )

    # Historico de consumo (tabela MES CONSUMO N_DIAS)
    historico = []
    for m in re.finditer(
        r"\b([A-Z]{3})(\d{2})\s+(\d+)\s+\d+\b", text
    ):
        mes = _MESES.get(m.group(1).lower())
        if mes:
            historico.append(
                {"ano_mes": f"20{m.group(2)}-{mes:02d}", "consumo_kwh": int(m.group(3))}
            )
    data["historico_consumo"] = historico
    return data


def parse_gd(text: str) -> dict[str, Any]:
    """Extrai o demonstrativo de geracao distribuida (energia solar)."""
    data: dict[str, Any] = {
        "periodo": _search(r"Período.*?(\w{3}/\d{4})", text, re.S),
        # No cabecalho da GD a potencia usa ponto decimal (ex "5.00" = 5 kWp).
        "potencia_kwp": (
            lambda v: float(v.replace(",", ".")) if v else None
        )(_search(r"\w{3}/\d{4}\s+(\d+[.,]\d{2})\s+\w+\s+GD", text)),
    }
    # Linha "Resumo de Saldo de Credito": 7 numeros em sequencia
    resumo = re.search(
        rf"({_NUM})\s+({_NUM})\s+({_NUM})\s+({_NUM})\s+({_NUM})\s+(\w{{3}}/\d{{4}})\s+({_NUM})",
        text,
    )
    if resumo:
        data.update(
            {
                "saldo_anterior_kwh": br_float(resumo.group(1)),
                "total_injetado_kwh": br_float(resumo.group(2)),
                "total_compensado_kwh": br_float(resumo.group(3)),
                "saldo_acumulado_kwh": br_float(resumo.group(4)),
                "saldo_a_expirar_kwh": br_float(resumo.group(5)),
                "ciclo_expiracao": resumo.group(6),
            }
        )
    # Primeira linha "Dados dos Ultimos 13 Meses" = mes mais recente
    linha = re.search(
        rf"(\w{{3}}/\d{{4}})\s+\w+\s+({_NUM})\s+({_NUM})\s+({_NUM})\s+({_NUM})\s+({_NUM})\s+({_NUM})\s+({_NUM})",
        text,
    )
    if linha:
        data.update(
            {
                "mes_recente": linha.group(1),
                "injetada_mes_kwh": br_float(linha.group(4)),
                "consumida_mes_kwh": br_float(linha.group(5)),
                "compensada_mes_kwh": br_float(linha.group(7)),
            }
        )
    return data
