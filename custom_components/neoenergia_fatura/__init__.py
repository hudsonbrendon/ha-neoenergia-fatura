"""Integração Neoenergia Fatura (Cosern via IMAP) para Home Assistant."""

from __future__ import annotations

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_loaded_integration

from .const import (
    CONF_FOLDER,
    CONF_IMAP_HOST,
    CONF_IMAP_PORT,
    CONF_PDF_PASSWORD,
)
from .coordinator import NeoenergiaFaturaCoordinator
from .data import NeoenergiaFaturaConfigEntry, NeoenergiaFaturaData
from .mailbox import CosernMailbox

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(
    hass: HomeAssistant, entry: NeoenergiaFaturaConfigEntry
) -> bool:
    """Configura a integração a partir de um config entry."""
    mailbox = CosernMailbox(
        host=entry.data[CONF_IMAP_HOST],
        port=entry.data[CONF_IMAP_PORT],
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
        pdf_password=entry.data[CONF_PDF_PASSWORD],
        folder=entry.data[CONF_FOLDER],
    )
    coordinator = NeoenergiaFaturaCoordinator(hass, mailbox)
    entry.runtime_data = NeoenergiaFaturaData(
        mailbox=mailbox,
        coordinator=coordinator,
        integration=async_get_loaded_integration(hass, entry.domain),
    )
    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: NeoenergiaFaturaConfigEntry
) -> bool:
    """Descarrega o config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
