"""Unit tests for communication media storage and validation."""

from __future__ import annotations

import io
import pytest

from domains.communication.enums import MessageType
from domains.communication.services.storage import (
    InvalidMediaError,
    save_media_file,
    validate_media,
)


def test_validate_allowed_voice_mime():
    buf = io.BytesIO(b"audio-bytes-123")
    mime = validate_media(buf, "audio/m4a", MessageType.VOICE, "recording.m4a")
    assert mime == "audio/m4a"


def test_validate_allowed_image_mime():
    buf = io.BytesIO(b"image-bytes-123")
    mime = validate_media(buf, "image/jpeg", MessageType.IMAGE, "photo.jpg")
    assert mime == "image/jpeg"


def test_validate_allowed_video_mime():
    buf = io.BytesIO(b"video-bytes-123")
    mime = validate_media(buf, "video/mp4", MessageType.VIDEO, "video.mp4")
    assert mime == "video/mp4"


def test_reject_invalid_mime():
    buf = io.BytesIO(b"malicious-script")
    with pytest.raises(InvalidMediaError) as exc_info:
        validate_media(buf, "application/x-sh", MessageType.VOICE, "script.sh")
    assert "Invalid MIME type" in str(exc_info.value)


def test_reject_empty_file():
    buf = io.BytesIO(b"")
    with pytest.raises(InvalidMediaError) as exc_info:
        validate_media(buf, "audio/m4a", MessageType.VOICE, "empty.m4a")
    assert "empty" in str(exc_info.value)


def test_reject_oversized_voice_file(monkeypatch):
    from domains.communication.services import storage

    monkeypatch.setitem(storage.MAX_FILE_SIZES, MessageType.VOICE, 100)
    buf = io.BytesIO(b"A" * 150)
    with pytest.raises(InvalidMediaError) as exc_info:
        validate_media(buf, "audio/m4a", MessageType.VOICE, "big.m4a")
    assert "exceeds limit" in str(exc_info.value)
