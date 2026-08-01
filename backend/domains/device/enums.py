from django.db import models


class DeviceModelStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    INACTIVE = "INACTIVE", "Inactive"


class DeviceOperationalStatus(models.TextChoices):
    INVENTORY = "INVENTORY", "Inventory"
    ACTIVE = "ACTIVE", "Active"
    INACTIVE = "INACTIVE", "Inactive"
    REVOKED = "REVOKED", "Revoked"


class DeviceCapabilityCode(models.TextChoices):
    DISPLAY = "DISPLAY", "Display"
    SPEAKER = "SPEAKER", "Speaker"
    MICROPHONE = "MICROPHONE", "Microphone"
    CAMERA = "CAMERA", "Camera"
    BLE = "BLE", "BLE"
    BATTERY = "BATTERY", "Battery"


class CapabilityOverrideState(models.TextChoices):
    ENABLED = "ENABLED", "Enabled"
    DISABLED = "DISABLED", "Disabled"


class AssignmentType(models.TextChoices):
    OWNED = "OWNED", "Owned"
    RENTED = "RENTED", "Rented"
    LOANER = "LOANER", "Loaner"


class AssignmentStatus(models.TextChoices):
    INVENTORY = "INVENTORY", "Inventory"
    ASSIGNED = "ASSIGNED", "Assigned"
    RETURNED = "RETURNED", "Returned"
    REFURBISHED = "REFURBISHED", "Refurbished"


class PairingStatus(models.TextChoices):
    PAIRING = "PAIRING", "Pairing"
    ACTIVE = "ACTIVE", "Active"
    DISCONNECTED = "DISCONNECTED", "Disconnected"
    REVOKED = "REVOKED", "Revoked"


class CommandStatus(models.TextChoices):
    QUEUED = "QUEUED", "Queued"
    DELIVERED = "DELIVERED", "Delivered"
    EXECUTING = "EXECUTING", "Executing"
    SUCCEEDED = "SUCCEEDED", "Succeeded"
    FAILED = "FAILED", "Failed"
    EXPIRED = "EXPIRED", "Expired"
    CANCELLED = "CANCELLED", "Cancelled"


TERMINAL_COMMAND_STATUSES = frozenset(
    {
        CommandStatus.SUCCEEDED,
        CommandStatus.FAILED,
        CommandStatus.EXPIRED,
        CommandStatus.CANCELLED,
    }
)


class CommandType(models.TextChoices):
    OPEN_COMPARTMENT = "OPEN_COMPARTMENT", "Open Compartment"
    CLOSE_COMPARTMENT = "CLOSE_COMPARTMENT", "Close Compartment"
    PLAY_AUDIO = "PLAY_AUDIO", "Play Audio"
    SHOW_DISPLAY = "SHOW_DISPLAY", "Show Display"
    DIAGNOSTIC = "DIAGNOSTIC", "Diagnostic"


class CompartmentStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    INACTIVE = "INACTIVE", "Inactive"


class CompartmentAssignmentStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    RELEASED = "RELEASED", "Released"
