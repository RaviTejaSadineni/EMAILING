from __future__ import annotations

import hashlib
import mailbox
from dataclasses import dataclass
from datetime import UTC
from email.header import decode_header
from email.message import Message
from email.parser import BytesParser
from email.policy import default
from email.utils import getaddresses, parseaddr, parsedate_to_datetime
from pathlib import Path

try:
    import chardet
except Exception:  # pragma: no cover
    chardet = None


@dataclass
class ParsedAttachment:
    filename: str
    content_type: str
    size: int
    file_hash: str
    content: bytes


@dataclass
class ParsedEmail:
    message_id: str
    subject: str | None
    from_address: str
    to_addresses: list[str]
    cc_addresses: list[str]
    bcc_addresses: list[str]
    date: object | None
    body_text: str | None
    body_html: str | None
    in_reply_to: str | None
    references: list[str]
    headers: dict[str, str]
    raw_size: int
    attachments: list[ParsedAttachment]


def _decode_header_value(value: str | None) -> str | None:
    if value is None:
        return None
    chunks: list[str] = []
    for item, encoding in decode_header(value):
        if isinstance(item, bytes):
            if encoding:
                chunks.append(item.decode(encoding, errors="replace"))
                continue
            if chardet is not None:
                detected = chardet.detect(item)
                guess = detected.get("encoding") if detected else None
                if guess:
                    chunks.append(item.decode(guess, errors="replace"))
                    continue
            chunks.append(item.decode("utf-8", errors="replace"))
        else:
            chunks.append(item)
    return "".join(chunks).strip()


def _parse_addresses(value: str | None) -> list[str]:
    if not value:
        return []
    return [email for _, email in getaddresses([value]) if email]


def _extract_body_and_attachments(message: Message) -> tuple[str | None, str | None, list[ParsedAttachment]]:
    body_text_parts: list[str] = []
    body_html_parts: list[str] = []
    attachments: list[ParsedAttachment] = []

    for part in message.walk():
        if part.is_multipart():
            continue

        content_disposition = (part.get_content_disposition() or "").lower()
        content_type = part.get_content_type() or "application/octet-stream"
        payload = part.get_payload(decode=True) or b""

        if content_disposition == "attachment" or part.get_filename():
            filename = _decode_header_value(part.get_filename()) or "attachment.bin"
            file_hash = hashlib.sha256(payload).hexdigest()
            attachments.append(
                ParsedAttachment(
                    filename=filename,
                    content_type=content_type,
                    size=len(payload),
                    file_hash=file_hash,
                    content=payload,
                )
            )
            continue

        charset = part.get_content_charset()
        if charset:
            decoded = payload.decode(charset, errors="replace")
        elif chardet is not None and payload:
            detected = chardet.detect(payload)
            decoded = payload.decode((detected or {}).get("encoding") or "utf-8", errors="replace")
        else:
            decoded = payload.decode("utf-8", errors="replace")

        if content_type == "text/plain":
            body_text_parts.append(decoded)
        elif content_type == "text/html":
            body_html_parts.append(decoded)

    body_text = "\n".join(body_text_parts).strip() or None
    body_html = "\n".join(body_html_parts).strip() or None
    return body_text, body_html, attachments


class MboxParser:
    def __init__(self, file_path: str | Path) -> None:
        self.file_path = str(file_path)

    def iter_emails(self, start_index: int = 0):
        mbox = mailbox.mbox(self.file_path)
        for idx, raw_message in enumerate(mbox):
            if idx < start_index:
                continue
            try:
                message_bytes = raw_message.as_bytes(unixfrom=True)
                message = BytesParser(policy=default).parsebytes(message_bytes)

                message_id = (message.get("Message-ID") or f"generated-{idx}").strip()
                subject = _decode_header_value(message.get("Subject"))
                from_address = parseaddr(message.get("From", ""))[1]
                to_addresses = _parse_addresses(message.get("To"))
                cc_addresses = _parse_addresses(message.get("Cc"))
                bcc_addresses = _parse_addresses(message.get("Bcc"))

                parsed_date = None
                if message.get("Date"):
                    try:
                        parsed_date = parsedate_to_datetime(message["Date"])
                        if parsed_date and parsed_date.tzinfo is None:
                            parsed_date = parsed_date.replace(tzinfo=UTC)
                    except Exception:
                        parsed_date = None

                body_text, body_html, attachments = _extract_body_and_attachments(message)
                references = (message.get("References") or "").split()
                headers = {k: _decode_header_value(v) or "" for k, v in message.items()}
                if self._is_effectively_empty_email(
                    headers=headers,
                    from_address=from_address,
                    to_addresses=to_addresses,
                    subject=subject,
                    attachments=attachments,
                ):
                    continue

                yield ParsedEmail(
                    message_id=message_id,
                    subject=subject,
                    from_address=from_address,
                    to_addresses=to_addresses,
                    cc_addresses=cc_addresses,
                    bcc_addresses=bcc_addresses,
                    date=parsed_date,
                    body_text=body_text,
                    body_html=body_html,
                    in_reply_to=message.get("In-Reply-To"),
                    references=references,
                    headers=headers,
                    raw_size=len(message_bytes),
                    attachments=attachments,
                )
            except Exception:
                continue

    @staticmethod
    def _is_effectively_empty_email(
        *,
        headers: dict[str, str],
        from_address: str,
        to_addresses: list[str],
        subject: str | None,
        attachments: list[ParsedAttachment],
    ) -> bool:
        return not headers and not from_address and not to_addresses and not subject and not attachments
