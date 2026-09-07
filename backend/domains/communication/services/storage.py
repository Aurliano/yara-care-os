"""Media storage service for communication attachments.

Handles file storage, MIME and size validation, and streaming I/O
without exposing internal filesystem paths to clients.
"""

from __future__ import annotations

import mimetypes
import os
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Generator

from django.conf import settings
from django.utils import timezone

from domains.communication.enums import MessageType
from domains.communication.exceptions import (
    CommunicationError,
    InvalidMediaError,
    MediaNotFoundError,
)

# Allowed MIME types and size limits
ALLOWED_MIME_TYPES: dict[str, set[str]] = {
    MessageType.VOICE: {
        "audio/m4a",
        "audio/mp4",
        "audio/aac",
        "audio/ogg",
        "audio/mpeg",
        "audio/wav",
        "audio/x-m4a",
    },
    MessageType.IMAGE: {
        "image/jpeg",
        "image/png",
        "image/webp",
    },
    MessageType.VIDEO: {
        "video/mp4",
        "video/quicktime",
        "video/webm",
    },
}

MAX_FILE_SIZES: dict[str, int] = {
    MessageType.VOICE: 5 * 1024 * 1024,   # 5 MB
    MessageType.IMAGE: 10 * 1024 * 1024,  # 10 MB
    MessageType.VIDEO: 100 * 1024 * 1024,  # 100 MB
}

CHUNK_SIZE = 64 * 1024  # 64 KB streaming chunks


@dataclass(frozen=True, slots=True)
class StoredMediaResult:
    attachment_id: uuid.UUID
    relative_path: str
    file_size: int
    mime_type: str
    original_filename: str


def get_media_root() -> Path:
    """Return the base media root directory."""
    raw = getattr(settings, "MEDIA_ROOT", None)
    if raw is None:
        raw = Path(settings.BASE_DIR) / "media"
    path = Path(raw)
    path.mkdir(parents=True, exist_ok=True)
    return path


def validate_media(
    file_obj: BinaryIO,
    claimed_mime_type: str | None,
    media_type: str,
    original_filename: str | None = None,
) -> str:
    """Validate MIME type and size for the specified media type."""
    if media_type not in ALLOWED_MIME_TYPES:
        raise InvalidMediaError(f"Unsupported media type: {media_type}")

    allowed_mimes = ALLOWED_MIME_TYPES[media_type]

    # Detect MIME from filename if claimed is ambiguous
    mime = (claimed_mime_type or "").lower().split(";")[0].strip()
    if not mime and original_filename:
        guessed, _ = mimetypes.guess_type(original_filename)
        if guessed:
            mime = guessed.lower()

    if mime not in allowed_mimes:
        raise InvalidMediaError(
            f"Invalid MIME type '{mime}' for {media_type}. Allowed: {sorted(allowed_mimes)}"
        )

    # Check size
    file_obj.seek(0, os.SEEK_END)
    size = file_obj.tell()
    file_obj.seek(0)

    max_size = MAX_FILE_SIZES.get(media_type, 10 * 1024 * 1024)
    if size > max_size:
        raise InvalidMediaError(
            f"File size ({size} bytes) exceeds limit ({max_size} bytes) for {media_type}."
        )
    if size == 0:
        raise InvalidMediaError("Uploaded file is empty.")

    return mime


def save_media_file(
    file_obj: BinaryIO,
    media_type: str,
    claimed_mime_type: str | None,
    original_filename: str = "",
) -> StoredMediaResult:
    """Validate and stream-write media file to disk, returning storage metadata."""
    mime = validate_media(file_obj, claimed_mime_type, media_type, original_filename)

    attachment_id = uuid.uuid4()
    now = timezone.now()
    date_path = now.strftime("%Y/%m/%d")

    # Preserve or infer safe extension
    ext = Path(original_filename).suffix.lower() if original_filename else ""
    if not ext:
        guessed_ext = mimetypes.guess_extension(mime)
        ext = guessed_ext or ".bin"

    safe_filename = f"{attachment_id}{ext}"
    relative_path = f"communication/{media_type.lower()}/{date_path}/{safe_filename}"

    dest_path = get_media_root() / relative_path
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    bytes_written = 0
    with open(dest_path, "wb") as dest:
        while chunk := file_obj.read(CHUNK_SIZE):
            dest.write(chunk)
            bytes_written += len(chunk)

    return StoredMediaResult(
        attachment_id=attachment_id,
        relative_path=relative_path,
        file_size=bytes_written,
        mime_type=mime,
        original_filename=original_filename or safe_filename,
    )


def open_media_stream(relative_path: str) -> tuple[Generator[bytes, None, None], int, str]:
    """Open a media file for streaming read, returning (stream_generator, size, mime_type)."""
    full_path = get_media_root() / relative_path
    if not full_path.is_file():
        raise MediaNotFoundError(f"Media file not found: {relative_path}")

    size = full_path.stat().st_size
    mime_type, _ = mimetypes.guess_type(str(full_path))
    mime_type = mime_type or "application/octet-stream"

    def _generator() -> Generator[bytes, None, None]:
        with open(full_path, "rb") as f:
            while chunk := f.read(CHUNK_SIZE):
                yield chunk

    return _generator(), size, mime_type
