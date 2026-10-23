"""Config flow da Neoenergia Fatura (IMAP + senha do PDF)."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

from .const import (
    CONF_FOLDER,
    CONF_IMAP_HOST,
    CONF_IMAP_PORT,
    CONF_PDF_PASSWORD,
    DEFAULT_FOLDER,
    DEFAULT_IMAP_HOST,
    DEFAULT_IMAP_PORT,
    DOMAIN,
)
from .mailbox import CosernMailbox, MailboxError


class NeoenergiaFaturaConfigFlow(ConfigFlow, domain=DOMAIN):
    """Fluxo de configuracao via UI."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Pede e-mail/senha-de-app IMAP e os 5 digitos do CPF (senha do PDF)."""
        errors: dict[str, str] = {}
        if user_input is not None:
            mailbox = CosernMailbox(
                host=user_input[CONF_IMAP_HOST],
                port=user_input[CONF_IMAP_PORT],
                username=user_input[CONF_USERNAME],
                password=user_input[CONF_PASSWORD],
                pdf_password=user_input[CONF_PDF_PASSWORD],
                folder=user_input[CONF_FOLDER],
            )
            try:
                await self.hass.async_add_executor_job(mailbox.check_login)
            except MailboxError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(
                    f"{user_input[CONF_USERNAME]}:{DOMAIN}"
                )
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Cosern ({user_input[CONF_USERNAME]})",
                    data=user_input,
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Required(CONF_PDF_PASSWORD): str,
                vol.Required(CONF_IMAP_HOST, default=DEFAULT_IMAP_HOST): str,
                vol.Required(CONF_IMAP_PORT, default=DEFAULT_IMAP_PORT): int,
                vol.Required(CONF_FOLDER, default=DEFAULT_FOLDER): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
