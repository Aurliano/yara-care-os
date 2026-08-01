"""DeviceModel registration and capability management."""

from __future__ import annotations

from django.db import transaction

from domains.device.enums import DeviceCapabilityCode, DeviceModelStatus
from domains.device.exceptions import DeviceModelNotFoundError, InvalidCapabilityOverrideError
from domains.device.models import DeviceCapability, DeviceModel, DeviceModelCapability


def get_device_model(device_model_id) -> DeviceModel:
    try:
        return DeviceModel.objects.prefetch_related("model_capabilities__capability").get(pk=device_model_id)
    except DeviceModel.DoesNotExist as exc:
        raise DeviceModelNotFoundError("Device model not found.") from exc


def get_model_capability_codes(device_model: DeviceModel) -> set[str]:
    return set(
        device_model.model_capabilities.values_list("capability__code", flat=True)
    )


@transaction.atomic
def register_device_model(
    *,
    manufacturer: str,
    model_code: str,
    model_name: str,
    capability_codes: list[str],
    device_type: str = "GENERIC",
) -> DeviceModel:
    for code in capability_codes:
        if code not in DeviceCapabilityCode.values:
            raise InvalidCapabilityOverrideError(f"Unknown capability code: {code}")

    device_model, _ = DeviceModel.objects.get_or_create(
        model_code=model_code,
        defaults={
            "manufacturer": manufacturer,
            "model_name": model_name,
            "device_type": device_type,
            "status": DeviceModelStatus.ACTIVE,
        },
    )
    if device_model.manufacturer != manufacturer or device_model.model_name != model_name:
        device_model.manufacturer = manufacturer
        device_model.model_name = model_name
        device_model.device_type = device_type
        device_model.save(update_fields=["manufacturer", "model_name", "device_type"])

    for code in capability_codes:
        capability, _ = DeviceCapability.objects.get_or_create(
            code=code,
            defaults={"name": code.replace("_", " ").title()},
        )
        DeviceModelCapability.objects.get_or_create(
            device_model=device_model,
            capability=capability,
        )
    return get_device_model(device_model.id)
