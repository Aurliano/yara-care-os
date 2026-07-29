from django.db import models


class PlanStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    INACTIVE = "INACTIVE", "Inactive"


class LicenseStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    SUSPENDED = "SUSPENDED", "Suspended"
    EXPIRED = "EXPIRED", "Expired"
    REVOKED = "REVOKED", "Revoked"


class EntitlementKind(models.TextChoices):
    FEATURE = "FEATURE", "Feature"
    LIMIT = "LIMIT", "Limit"


class EntitlementKey(models.TextChoices):
    MAX_CAREGIVERS = "MAX_CAREGIVERS", "Max Caregivers"
    MAX_HUBS = "MAX_HUBS", "Max Hubs"
    MAX_PILLBOXES = "MAX_PILLBOXES", "Max Pillboxes"
    PILLBOX_SUPPORT = "PILLBOX_SUPPORT", "Pillbox Support"
    SENSOR_SUPPORT = "SENSOR_SUPPORT", "Sensor Support"
    VIDEO_CALL = "VIDEO_CALL", "Video Call"
