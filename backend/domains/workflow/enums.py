from django.db import models


class WorkflowDefinitionStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    INACTIVE = "INACTIVE", "Inactive"


class ExecutionStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    ACTIVE = "ACTIVE", "Active"
    CONFIRMED = "CONFIRMED", "Confirmed"
    MISSED = "MISSED", "Missed"
    CANCELLED = "CANCELLED", "Cancelled"
    FAILED = "FAILED", "Failed"


TERMINAL_EXECUTION_STATUSES = frozenset(
    {
        ExecutionStatus.CONFIRMED,
        ExecutionStatus.MISSED,
        ExecutionStatus.CANCELLED,
        ExecutionStatus.FAILED,
    }
)


class ActionType(models.TextChoices):
    SHOW_REMINDER = "SHOW_REMINDER", "Show Reminder"
    PLAY_AUDIO = "PLAY_AUDIO", "Play Audio"
    OPEN_COMPARTMENT = "OPEN_COMPARTMENT", "Open Compartment"
    REQUEST_CONFIRMATION = "REQUEST_CONFIRMATION", "Request Confirmation"
    INITIATE_CALL = "INITIATE_CALL", "Initiate Call"
    NOTIFY_CAREGIVER = "NOTIFY_CAREGIVER", "Notify Caregiver"


class EvidenceSourceType(models.TextChoices):
    DOMAIN_EVENT = "DOMAIN_EVENT", "Domain Event"
    DIRECT_INTERACTION = "DIRECT_INTERACTION", "Direct Interaction"


class EvidenceType(models.TextChoices):
    HUB_CONFIRMATION = "HUB_CONFIRMATION", "Hub Confirmation"
    COMPARTMENT_CLOSED = "COMPARTMENT_CLOSED", "Compartment Closed"
    COMMUNICATION_SESSION_ENDED = "COMMUNICATION_SESSION_ENDED", "Communication Session Ended"


class ActionResultStatus(models.TextChoices):
    SUCCEEDED = "SUCCEEDED", "Succeeded"
    FAILED = "FAILED", "Failed"
