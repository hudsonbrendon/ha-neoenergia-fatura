"""Tipos compartilhados da integração Neoenergia Fatura."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .coordinator import NeoenergiaFaturaCoordinator
    from .mailbox import CosernMailbox


type NeoenergiaFaturaConfigEntry = ConfigEntry[NeoenergiaFaturaData]


@dataclass
class NeoenergiaFaturaData:
    """Dados guardados no ConfigEntry."""

    mailbox: CosernMailbox
    coordinator: NeoenergiaFaturaCoordinator
    integration: Integration
