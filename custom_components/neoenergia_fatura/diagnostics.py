"""Diagnostics da Neoenergia Fatura (credenciais redigidas)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from .const import CONF_PDF_PASSWORD
from .data import NeoenergiaFaturaConfigEntry

TO_REDACT = {
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_PDF_PASSWORD,
    "codigo_cliente",
    "uc",
    "linha_digitavel",
    "nota_fiscal",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: NeoenergiaFaturaConfigEntry
) -> dict[str, Any]:
    """Devolve dados do entry e o ultimo resultado do coordinator, redigidos."""
    coordinator = entry.runtime_data.coordinator
    return {
        "entry": async_redact_data(dict(entry.data), TO_REDACT),
        "data": async_redact_data(coordinator.data or {}, TO_REDACT),
    }
