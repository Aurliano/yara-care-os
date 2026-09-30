"""Tests for deployment safety guards and management command environment boundaries."""

import io
import uuid

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings
import pytest

from domains.device.enums import DeviceCapabilityCode
from domains.device.models import Device, DeviceModel
from domains.device.services.device_models import register_device_model
from domains.identity_access.models import User
from integration.services.family_lab_seed import FAMILY_CAREGIVER_PHONE
from integration.services.hub_dev_seed import DEV_CAREGIVER_PHONE


@pytest.mark.django_db
@pytest.mark.parametrize(
    "command_name,command_args",
    [
        ("seed_family_lab", []),
        ("seed_hub_provision", []),
        ("seed_hub_dev_sync", []),
        ("reset_test_environment", ["--confirm"]),
        ("remove_test_device", ["--device-id", str(uuid.uuid4()), "--confirm"]),
    ],
)
def test_all_five_commands_are_blocked_in_production(command_name: str, command_args: list[str]) -> None:
    """Every destructive reset or seed command must fail immediately in production."""
    with override_settings(YARA_ENVIRONMENT="production"):
        with pytest.raises(CommandError, match=f"Refusing to execute '{command_name}'.*production"):
            call_command(command_name, *command_args)


@pytest.mark.django_db
def test_guard_blocks_before_any_mutation_in_production() -> None:
    """Verify that zero database records are created or deleted when blocked in production."""
    user_count_before = User.objects.count()
    device_count_before = Device.objects.count()

    with override_settings(YARA_ENVIRONMENT="production"):
        with pytest.raises(CommandError):
            call_command("seed_family_lab")

        with pytest.raises(CommandError):
            call_command("seed_hub_provision")

    assert User.objects.count() == user_count_before
    assert Device.objects.count() == device_count_before
    assert not User.objects.filter(phone=FAMILY_CAREGIVER_PHONE).exists()
    assert not User.objects.filter(phone=DEV_CAREGIVER_PHONE).exists()


@pytest.mark.django_db
def test_guard_blocks_on_production_database_name() -> None:
    """Defense-in-depth: database names containing 'prod' or 'production' must be rejected even if env is dev."""
    prod_db_config = {"default": {"NAME": "yara_production_replica", "ENGINE": "django.db.backends.postgresql"}}
    with override_settings(YARA_ENVIRONMENT="development", DATABASES=prod_db_config):
        with pytest.raises(CommandError, match="indicates a production database"):
            call_command("seed_family_lab")


@pytest.mark.django_db
def test_staging_with_debug_false_permits_seed_commands() -> None:
    """Staging environments run with DEBUG=False; seed commands must not be blocked merely by DEBUG=False."""
    call_command("seed_identity_access", verbosity=0)
    call_command("seed_licensing", verbosity=0)
    out = io.StringIO()
    with override_settings(DEBUG=False, YARA_ENVIRONMENT="staging"):
        call_command("seed_family_lab", stdout=out)
        call_command("seed_hub_provision", stdout=out)

    assert User.objects.filter(phone=FAMILY_CAREGIVER_PHONE).exists()
    assert User.objects.filter(phone=DEV_CAREGIVER_PHONE).exists()
    assert DeviceModel.objects.filter(model_code="YARA-HUB-TABLET").exists()


@pytest.mark.django_db
def test_staging_with_debug_false_requires_explicit_confirmation_for_reset() -> None:
    """reset_test_environment must require --confirm in staging without being blocked by DEBUG=False."""
    with override_settings(DEBUG=False, YARA_ENVIRONMENT="staging"):
        # Without confirmation: must fail with confirmation error, NOT DEBUG error
        with pytest.raises(CommandError, match="Confirmation flag --confirm is required"):
            call_command("reset_test_environment")

        # With confirmation: succeeds in staging
        out = io.StringIO()
        call_command("reset_test_environment", "--confirm", stdout=out)
        assert "CLEAN BASELINE ESTABLISHED" in out.getvalue()


@pytest.mark.django_db
def test_staging_with_debug_false_dry_run_and_confirm_for_remove_device() -> None:
    """remove_test_device must support dry-run and confirmed execution under DEBUG=False in staging."""
    register_device_model(
        manufacturer="Yara",
        model_code="YARA-TEST-MODEL",
        model_name="Test Model",
        capability_codes=[DeviceCapabilityCode.DISPLAY],
        device_type="HUB",
    )
    model = DeviceModel.objects.get(model_code="YARA-TEST-MODEL")
    device = Device.objects.create(
        serial_number=f"SN-{uuid.uuid4().hex[:8]}",
        device_model=model,
    )

    with override_settings(DEBUG=False, YARA_ENVIRONMENT="staging"):
        # Dry-run: does not delete
        out_dry = io.StringIO()
        call_command("remove_test_device", "--device-id", str(device.id), stdout=out_dry)
        assert "[DRY-RUN]" in out_dry.getvalue()
        assert Device.objects.filter(id=device.id).exists()

        # Confirmed execution: deletes device
        out_confirm = io.StringIO()
        call_command("remove_test_device", "--device-id", str(device.id), "--confirm", stdout=out_confirm)
        assert "DEVICE SUCCESSFULLY REMOVED" in out_confirm.getvalue()
        assert not Device.objects.filter(id=device.id).exists()
