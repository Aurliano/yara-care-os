from django.db import models


class ContactStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    ARCHIVED = "ARCHIVED", "Archived"


class CommunicationChannel(models.TextChoices):
    VOICE = "VOICE", "Voice"
    VIDEO = "VIDEO", "Video"
    MESSAGE = "MESSAGE", "Message"


class SessionStatus(models.TextChoices):
    INITIATED = "INITIATED", "Initiated"
    CONNECTING = "CONNECTING", "Connecting"
    CONNECTED = "CONNECTED", "Connected"
    ENDED = "ENDED", "Ended"
    MISSED = "MISSED", "Missed"
    DECLINED = "DECLINED", "Declined"
    FAILED = "FAILED", "Failed"
    CANCELLED = "CANCELLED", "Cancelled"


TERMINAL_SESSION_STATUSES = frozenset(
    {
        SessionStatus.ENDED,
        SessionStatus.MISSED,
        SessionStatus.DECLINED,
        SessionStatus.FAILED,
        SessionStatus.CANCELLED,
    }
)

ACTIVE_SESSION_STATUSES = frozenset(
    {
        SessionStatus.INITIATED,
        SessionStatus.CONNECTING,
        SessionStatus.CONNECTED,
    }
)


class SessionOutcome(models.TextChoices):
    ANSWERED = "ANSWERED", "Answered"
    MISSED = "MISSED", "Missed"
    DECLINED = "DECLINED", "Declined"
    FAILED = "FAILED", "Failed"
    CANCELLED = "CANCELLED", "Cancelled"


class ParticipantRole(models.TextChoices):
    INITIATOR = "INITIATOR", "Initiator"
    RECIPIENT = "RECIPIENT", "Recipient"


class CallAttemptOutcome(models.TextChoices):
    CONNECTED = "CONNECTED", "Connected"
    FAILED = "FAILED", "Failed"
    DECLINED = "DECLINED", "Declined"
    MISSED = "MISSED", "Missed"
