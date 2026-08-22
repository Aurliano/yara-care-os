"""Diagnose the Skyroom transport without starting a real call."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.core.management.base import BaseCommand

from domains.communication.exceptions import CommunicationProviderError
from infrastructure.communication.services import room_key_for_elder


class Command(BaseCommand):
    help = "Report whether the Skyroom key, service, and room are usable. Never prints the key."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--elder-id",
            type=str,
            default="",
            help="Optional elder id; resolves (and creates once) that elder's room.",
        )

    def handle(self, *args, **options) -> None:
        provider_name = getattr(settings, "COMMUNICATION_PROVIDER", "skyroom")
        self.stdout.write(f"COMMUNICATION_PROVIDER={provider_name}")
        self.stdout.write(f"SKYROOM_API_BASE_URL={getattr(settings, 'SKYROOM_API_BASE_URL', '')}")
        self.stdout.write(f"SKYROOM_SERVICE_ID={getattr(settings, 'SKYROOM_SERVICE_ID', 0) or '(unset)'}")

        if provider_name != "skyroom":
            self.stdout.write(
                self.style.WARNING("Provider is not skyroom; nothing to check against the vendor.")
            )
            return

        from infrastructure.communication.skyroom import SkyroomCommunicationProvider

        try:
            provider = SkyroomCommunicationProvider()
        except CommunicationProviderError as exc:
            self.stdout.write(self.style.ERROR(f"Key not loaded: {exc}"))
            self.stdout.write(
                "Set SKYROOM_API_KEY in backend/.env and restart the server. "
                "An OS environment variable of the same name overrides .env."
            )
            return

        self.stdout.write(self.style.SUCCESS(f"Key loaded ({provider.api_key_fingerprint()})"))

        try:
            services = provider.list_services()
        except CommunicationProviderError as exc:
            self.stdout.write(self.style.ERROR(f"getServices failed [{exc.reason}] code={exc.error_code}: {exc}"))
            return

        active = [service for service in services if service.get("status") == 1]
        self.stdout.write(f"Services: {len(services)} total, {len(active)} active")
        for service in services:
            self.stdout.write(
                "  id={id} status={status} user_limit={user_limit} "
                "time_limit={time_limit} time_usage={time_usage}".format(
                    id=service.get("id"),
                    status=service.get("status"),
                    user_limit=service.get("user_limit"),
                    time_limit=service.get("time_limit"),
                    time_usage=service.get("time_usage"),
                )
            )
        if not active:
            self.stdout.write(self.style.ERROR("No active service: createRoom will fail."))
            return
        if len(active) > 1 and not getattr(settings, "SKYROOM_SERVICE_ID", 0):
            self.stdout.write(
                self.style.WARNING(
                    "More than one active service: set SKYROOM_SERVICE_ID so rooms land on the intended one."
                )
            )

        elder_id_raw = options["elder_id"]
        if not elder_id_raw:
            self.stdout.write(self.style.SUCCESS("Transport reachable. Pass --elder-id to also check the room."))
            return

        try:
            elder_id = uuid.UUID(elder_id_raw)
        except ValueError:
            self.stdout.write(self.style.ERROR("--elder-id must be a UUID."))
            return

        room_key = room_key_for_elder(elder_id)
        try:
            room = provider.ensure_room(room_key=room_key, title="Yara")
        except CommunicationProviderError as exc:
            self.stdout.write(self.style.ERROR(f"ensure_room failed [{exc.reason}] code={exc.error_code}: {exc}"))
            return
        self.stdout.write(self.style.SUCCESS(f"Room ready: key={room.key} external_id={room.external_id}"))

        from domains.communication.providers import ProviderUser

        try:
            login = provider.generate_login_url(
                room=room,
                user=ProviderUser(key="yara-check", external_id="", display_name="Yara"),
                ttl_seconds=60,
            )
        except CommunicationProviderError as exc:
            self.stdout.write(
                self.style.ERROR(
                    f"createLoginUrl failed [{exc.reason}] code={exc.error_code}: {exc}"
                )
            )
            return
        scheme = "https" if login.login_url.startswith("https://") else "other"
        self.stdout.write(
            self.style.SUCCESS(f"Login URL issued length={len(login.login_url)} scheme={scheme}")
        )
