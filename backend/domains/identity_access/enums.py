from django.db import models


class UserStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    SUSPENDED = "SUSPENDED", "Suspended"
    DELETED = "DELETED", "Deleted"


class ElderStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    INACTIVE = "INACTIVE", "Inactive"


class MembershipStatus(models.TextChoices):
    INVITED = "INVITED", "Invited"
    ACTIVE = "ACTIVE", "Active"
    SUSPENDED = "SUSPENDED", "Suspended"
    REVOKED = "REVOKED", "Revoked"


class InvitationStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    ACCEPTED = "ACCEPTED", "Accepted"
    EXPIRED = "EXPIRED", "Expired"
    REVOKED = "REVOKED", "Revoked"


class EmergencyRecipientStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    INACTIVE = "INACTIVE", "Inactive"


class RoleCode(models.TextChoices):
    PRIMARY_CAREGIVER = "PRIMARY_CAREGIVER", "Primary Caregiver"
    CAREGIVER = "CAREGIVER", "Caregiver"
    VIEWER = "VIEWER", "Viewer"


class PermissionCode(models.TextChoices):
    VIEW_ELDER_STATUS = "VIEW_ELDER_STATUS", "View Elder Status"
    MANAGE_MEDICATION = "MANAGE_MEDICATION", "Manage Medication"
    MANAGE_CONTACTS = "MANAGE_CONTACTS", "Manage Contacts"
    MANAGE_DEVICES = "MANAGE_DEVICES", "Manage Devices"
    INITIATE_CALL = "INITIATE_CALL", "Initiate Call"
    MANAGE_MEMBERS = "MANAGE_MEMBERS", "Manage Members"
    MANAGE_SUBSCRIPTION = "MANAGE_SUBSCRIPTION", "Manage Subscription"
