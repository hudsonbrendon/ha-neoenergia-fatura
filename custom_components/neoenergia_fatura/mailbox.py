"""Leitura dos e-mails da Neoenergia Cosern por IMAP + extracao dos PDFs.

A Cosern envia a fatura digital e o demonstrativo de geracao distribuida como
PDFs protegidos por senha = os 5 primeiros digitos do CPF/CNPJ do titular.
Esta camada baixa o anexo mais recente de cada tipo, decifra e devolve o texto.

Roda em executor (imaplib/pypdf sao sincronos). Sem dependencia do Home Assistant.
"""

from __future__ import annotations

from dataclasses import dataclass
import email
from email.header import decode_header
import imaplib
from io import BytesIO
from typing import Any

from pypdf import PdfReader

# Remetentes/assuntos observados nos e-mails reais da Cosern.
SENDER = "faturaneoenergiacosern.com.br"
SUBJECT_FATURA = "Fatura Digital"
SUBJECT_GD = "Geração Distribuída"


class MailboxError(Exception):
    """Falha ao conectar/ler a caixa de e-mail."""


@dataclass
class PdfResult:
    """Texto extraido de um PDF e a data do e-mail."""

    text: str
    email_date: str | None
    filename: str | None


def _decode(value: str | None) -> str:
    if not value:
        return ""
    return "".join(
        part.decode(enc or "utf-8", "replace") if isinstance(part, bytes) else part
        for part, enc in decode_header(value)
    )


def _pdf_text(raw: bytes, password: str) -> str:
    reader = PdfReader(BytesIO(raw))
    if reader.is_encrypted:
        # pypdf.decrypt retorna 0 (falha), 1 (user pw) ou 2 (owner pw).
        if not reader.decrypt(password):
            msg = "senha do PDF incorreta (confira os 5 primeiros digitos do CPF)"
            raise MailboxError(msg)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


class CosernMailbox:
    """Cliente IMAP somente-leitura para os e-mails da Cosern."""

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        pdf_password: str,
        port: int = 993,
        folder: str = "INBOX",
    ) -> None:
        """pdf_password = 5 primeiros digitos do CPF/CNPJ do titular."""
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._pdf_password = pdf_password
        self._folder = folder

    def _connect(self) -> imaplib.IMAP4_SSL:
        try:
            imap = imaplib.IMAP4_SSL(self._host, self._port)
            imap.login(self._username, self._password)
            imap.select(self._folder, readonly=True)
        except (imaplib.IMAP4.error, OSError) as err:
            msg = f"falha no IMAP: {err}"
            raise MailboxError(msg) from err
        return imap

    def check_login(self) -> None:
        """Valida credenciais (usado no config flow)."""
        imap = self._connect()
        try:
            imap.logout()
        except imaplib.IMAP4.error, OSError:
            pass

    def _latest_pdf(self, imap: imaplib.IMAP4_SSL, subject_kw: str) -> PdfResult | None:
        # Busca por remetente (ASCII) e filtra o assunto em Python, para nao
        # depender de SEARCH com acentos.
        typ, data = imap.search(None, "FROM", SENDER)
        if typ != "OK" or not data or not data[0]:
            return None
        for num in reversed(data[0].split()):  # mais recente primeiro
            typ, msg_data = imap.fetch(num, "(RFC822)")
            if typ != "OK" or not msg_data or not msg_data[0]:
                continue
            msg = email.message_from_bytes(msg_data[0][1])
            if subject_kw.lower() not in _decode(msg.get("Subject")).lower():
                continue
            for part in msg.walk():
                fname = _decode(part.get_filename())
                if (
                    part.get_content_type() == "application/pdf"
                    or fname.lower().endswith(".pdf")
                ):
                    raw = part.get_payload(decode=True)
                    if not raw:
                        continue
                    return PdfResult(
                        text=_pdf_text(raw, self._pdf_password),
                        email_date=_decode(msg.get("Date")),
                        filename=fname or None,
                    )
        return None

    @staticmethod
    def subjects() -> tuple[str, str]:
        """Palavras-chave de assunto (fatura, GD)."""
        return SUBJECT_FATURA, SUBJECT_GD

    def fetch(self) -> dict[str, Any]:
        """Baixa fatura + demonstrativo GD mais recentes; devolve os textos."""
        imap = self._connect()
        try:
            fatura = self._latest_pdf(imap, SUBJECT_FATURA)
            gd = self._latest_pdf(imap, SUBJECT_GD)
        finally:
            try:
                imap.logout()
            except imaplib.IMAP4.error, OSError:
                pass
        return {"fatura": fatura, "gd": gd}
