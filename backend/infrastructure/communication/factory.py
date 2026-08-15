"""Resolve the configured CommunicationProvider adapter."""

from __future__ import annotations

from django.conf import settings

from domains.communication.exceptions import CommunicationProviderError
from domains.communication.providers import CommunicationProvider

_FAKE_SINGLETON = None


def get_communication_provider() -> CommunicationProvider:
    name = getattr(settings, "COMMUNICATION_PROVIDER", "skyroom")
    if name == "fake":
        return _get_fake_provider()
    if name == "skyroom":
        from infrastructure.communication.skyroom import SkyroomCommunicationProvider

        return SkyroomCommunicationProvider()
    raise CommunicationProviderError(f"Unknown communication provider '{name}'.")


def _get_fake_provider():
    global _FAKE_SINGLETON
    if _FAKE_SINGLETON is None:
        from infrastructure.communication.fake import FakeCommunicationProvider

        _FAKE_SINGLETON = FakeCommunicationProvider()
    return _FAKE_SINGLETON


def reset_fake_provider() -> None:
    global _FAKE_SINGLETON
    _FAKE_SINGLETON = None
