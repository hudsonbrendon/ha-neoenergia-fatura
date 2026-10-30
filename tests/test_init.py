"""Setup, sensores, diagnostics e config flow com a mailbox mockada."""

from __future__ import annotations

from unittest.mock import patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import device_registry as dr, entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.components.diagnostics import (
    get_diagnostics_for_config_entry,
)
from pytest_homeassistant_custom_component.typing import ClientSessionGenerator

from custom_components.neoenergia_fatura.const import DOMAIN
from custom_components.neoenergia_fatura.mailbox import MailboxError

from .conftest import ENTRY_DATA, setup_integration


def _state(hass: HomeAssistant, entry_id: str, key: str) -> str:
    entity_id = er.async_get(hass).async_get_entity_id(
        "sensor", DOMAIN, f"{entry_id}_{key}"
    )
    assert entity_id
    return hass.states.get(entity_id).state


async def test_setup_and_sensors(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_mailbox: None
) -> None:
    await setup_integration(hass, mock_config_entry)
    assert mock_config_entry.state is ConfigEntryState.LOADED

    assert _state(hass, mock_config_entry.entry_id, "valor") == "152.37"
    assert _state(hass, mock_config_entry.entry_id, "vencimento") == "2026-11-23"
    assert _state(hass, mock_config_entry.entry_id, "consumo") == "462"
    assert _state(hass, mock_config_entry.entry_id, "potencia") == "5.0"
    assert _state(hass, mock_config_entry.entry_id, "gd_total_injetado") == "4158.0"

    device = dr.async_get(hass).async_get_device_by_identifier(
        (DOMAIN, mock_config_entry.entry_id), mock_config_entry.entry_id
    )
    assert device is not None
    assert device.manufacturer == "Neoenergia"

    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED


async def test_setup_retry_on_mailbox_error(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    with patch(
        "custom_components.neoenergia_fatura.mailbox.CosernMailbox.fetch",
        side_effect=MailboxError("falha no IMAP"),
    ):
        await setup_integration(hass, mock_config_entry)
    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_diagnostics_redacts_credentials(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    mock_config_entry: MockConfigEntry,
    mock_mailbox: None,
) -> None:
    await setup_integration(hass, mock_config_entry)
    diag = await get_diagnostics_for_config_entry(hass, hass_client, mock_config_entry)
    assert diag["entry"]["username"] == "**REDACTED**"
    assert diag["entry"]["password"] == "**REDACTED**"
    assert diag["entry"]["pdf_password"] == "**REDACTED**"
    assert diag["entry"]["imap_host"] == "imap.gmail.com"
    assert diag["data"]["fatura"]["linha_digitavel"] == "**REDACTED**"
    assert diag["data"]["fatura"]["valor"] == 152.37


async def test_config_flow_success(hass: HomeAssistant, mock_mailbox: None) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=ENTRY_DATA
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Cosern (user@example.com)"
    assert result["data"] == ENTRY_DATA
    assert result["result"].unique_id == f"user@example.com:{DOMAIN}"


async def test_config_flow_cannot_connect_then_duplicate(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_mailbox: None
) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    with patch(
        "custom_components.neoenergia_fatura.config_flow.CosernMailbox.check_login",
        side_effect=MailboxError("login"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=ENTRY_DATA
        )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}

    mock_config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=ENTRY_DATA
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
