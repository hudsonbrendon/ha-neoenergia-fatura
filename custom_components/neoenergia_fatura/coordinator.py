"""Coordinator: le os e-mails da Cosern por IMAP e parseia os PDFs."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL_HOURS, DOMAIN, LOGGER
from .mailbox import MailboxError
from .parser import parse_fatura, parse_gd

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .mailbox import CosernMailbox


class NeoenergiaFaturaCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Busca periodica (IMAP e parsing rodam em executor)."""

    def __init__(self, hass: HomeAssistant, mailbox: CosernMailbox) -> None:
        """Inicializa o coordinator."""
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=DEFAULT_SCAN_INTERVAL_HOURS),
        )
        self.mailbox = mailbox

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            raw = await self.hass.async_add_executor_job(self.mailbox.fetch)
        except MailboxError as err:
            raise UpdateFailed(str(err)) from err

        result: dict[str, Any] = {"fatura": None, "gd": None, "fatura_date": None}
        if raw.get("fatura"):
            result["fatura"] = parse_fatura(raw["fatura"].text)
            result["fatura_date"] = raw["fatura"].email_date
        if raw.get("gd"):
            result["gd"] = parse_gd(raw["gd"].text)
        return result
