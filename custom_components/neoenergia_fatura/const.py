"""Constantes da integração Neoenergia Fatura (IMAP)."""

from __future__ import annotations

import logging

DOMAIN = "neoenergia_fatura"
LOGGER = logging.getLogger(__package__)

CONF_IMAP_HOST = "imap_host"
CONF_IMAP_PORT = "imap_port"
CONF_FOLDER = "folder"
CONF_PDF_PASSWORD = "pdf_password"

DEFAULT_IMAP_HOST = "imap.gmail.com"
DEFAULT_IMAP_PORT = 993
DEFAULT_FOLDER = "INBOX"
DEFAULT_SCAN_INTERVAL_HOURS = 12
