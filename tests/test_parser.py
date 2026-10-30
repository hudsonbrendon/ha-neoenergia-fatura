"""Checa o parser contra os textos reais dos PDFs da Cosern (sem Home Assistant).

`python3 -I tests/test_parser.py`. As fixtures sao o texto ja extraido (o PDF
original tem senha e nao fica no repo).
"""

from __future__ import annotations

from datetime import date
import importlib.util
import pathlib

_P = (
    pathlib.Path(__file__).resolve().parent.parent
    / "custom_components"
    / "neoenergia_fatura"
    / "parser.py"
)
_spec = importlib.util.spec_from_file_location("neo_parser", _P)
_m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_m)

_FIX = pathlib.Path(__file__).resolve().parent / "fixtures"


def test_br_float() -> None:
    """Formato pt-BR."""
    assert _m.br_float("4.158,00") == 4158.0
    assert _m.br_float("152,37") == 152.37
    assert _m.br_float(None) is None


def test_parse_fatura() -> None:
    """Campos chave da fatura real."""
    d = _m.parse_fatura((_FIX / "fatura.txt").read_text())
    assert d["valor"] == 152.37
    assert d["vencimento"] == date(2026, 11, 23)
    assert d["referencia"] == "10/2026"
    assert d["consumo_kwh"] == 462
    assert d["energia_injetada_kwh"] == 531.0
    assert d["saldo_creditos_kwh"] == 777.0
    assert d["bandeira"] == "Verde"
    assert len(d["historico_consumo"]) == 13


def test_parse_gd() -> None:
    """Campos chave do demonstrativo de geracao distribuida real."""
    d = _m.parse_gd((_FIX / "gd.txt").read_text())
    assert d["potencia_kwp"] == 5.0
    assert d["total_injetado_kwh"] == 4158.0
    assert d["saldo_acumulado_kwh"] == 452.0
    assert d["injetada_mes_kwh"] == 456.0
    assert d["compensada_mes_kwh"] == 377.0


if __name__ == "__main__":
    test_br_float()
    test_parse_fatura()
    test_parse_gd()
    print("todos os checks do parser passaram")
