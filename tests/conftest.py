"""Fixtures: mailbox mockada com os textos reais das fixtures."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.neoenergia_fatura.const import (
    CONF_FOLDER,
    CONF_IMAP_HOST,
    CONF_IMAP_PORT,
    CONF_PDF_PASSWORD,
    DOMAIN,
)
from custom_components.neoenergia_fatura.mailbox import PdfResult

FIXTURES = Path(__file__).parent / "fixtures"
ENTRY_DATA = {
    CONF_USERNAME: "user@example.com",
    CONF_PASSWORD: "app-password",
    CONF_PDF_PASSWORD: "12345",
    CONF_IMAP_HOST: "imap.gmail.com",
    CONF_IMAP_PORT: 993,
    CONF_FOLDER: "INBOX",
}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable loading custom integrations in every test."""


@pytest.fixture
def mock_mailbox() -> Generator[None]:
    """Patch IMAP: fetch returns the fixture texts, check_login succeeds."""
    result = {
        "fatura": PdfResult(
            text=(FIXTURES / "fatura.txt").read_text(),
            email_date="Thu, 23 Oct 2026 10:00:00 -0300",
            filename="fatura.pdf",
        ),
        "gd": PdfResult(
            text=(FIXTURES / "gd.txt").read_text(), email_date=None, filename="gd.pdf"
        ),
    }
    with (
        patch(
            "custom_components.neoenergia_fatura.mailbox.CosernMailbox.fetch",
            return_value=result,
        ),
        patch(
            "custom_components.neoenergia_fatura.mailbox.CosernMailbox.check_login",
            return_value=None,
        ),
    ):
        yield


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Config entry da conta de teste."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Cosern (user@example.com)",
        unique_id=f"user@example.com:{DOMAIN}",
        data=ENTRY_DATA,
        entry_id="01JNEOENERGIAFATURA0000001",
    )


async def setup_integration(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    """Add the entry and load it."""
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
