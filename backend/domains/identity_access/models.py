"""Identity & Access domain models."""

from __future__ import annotations

import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from django.db.models import Q
from django.utils import timezone

from domains.identity_access.enums import (
    ElderStatus,
    EmergencyRecipientStatus,
    InvitationStatus,
    MembershipStatus,
    UserStatus,
)


class UserManager(BaseUserManager):
    def create_user(self, phone: str, password: str | None = None, **extra_fields):
        if not phone:
            raise ValueError("Phone is required.")
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("status", UserStatus.ACTIVE)
        return self.create_user(phone, password, **extra_fields)


class User(AbstractBaseUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone = models.CharField(max_length=32, unique=True)
    email = models.EmailField(blank=True, default="")
    full_name = models.CharField(max_length=255)
    status = models.CharField(
        max_length=16,
        choices=UserStatus.choices,
        default=UserStatus.ACTIVE,
    )
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        db_table = "identity_user"

    @property
    def is_active(self) -> bool:
        return self.status == UserStatus.ACTIVE

    def has_perm(self, perm, obj=None) -> bool:
        return self.is_superuser

    def has_module_perms(self, app_label) -> bool:
        return self.is_superuser


class Elder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=255)
    birth_date = models.DateField(null=True, blank=True)
    photo_media_id = models.UUIDField(null=True, blank=True)
    status = models.CharField(
        max_length=16,
        choices=ElderStatus.choices,
        default=ElderStatus.ACTIVE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "identity_elder"


class Role(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=128)

    class Meta:
        db_table = "identity_role"

    def __str__(self) -> str:
        return self.code


class Permission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=128)

    class Meta:
        db_table = "identity_permission"

    def __str__(self) -> str:
        return self.code


class RolePermission(models.Model):
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="role_permissions",
    )
    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name="role_permissions",
    )

    class Meta:
        db_table = "identity_role_permission"
        constraints = [
            models.UniqueConstraint(
                fields=["role", "permission"],
                name="identity_role_permission_unique",
            ),
        ]


class Membership(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="memberships",
    )
    elder = models.ForeignKey(
        Elder,
        on_delete=models.PROTECT,
        related_name="memberships",
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        related_name="memberships",
    )
    relationship = models.CharField(max_length=128, blank=True, default="")
    status = models.CharField(
        max_length=16,
        choices=MembershipStatus.choices,
        default=MembershipStatus.INVITED,
    )
    is_primary = models.BooleanField(default=False)
    joined_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "identity_membership"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "elder"],
                condition=Q(status__in=[MembershipStatus.INVITED, MembershipStatus.ACTIVE]),
                name="identity_membership_unique_open",
            ),
            models.UniqueConstraint(
                fields=["elder"],
                condition=Q(is_primary=True, status=MembershipStatus.ACTIVE),
                name="identity_membership_unique_primary",
            ),
        ]

    def activate(self) -> None:
        self.status = MembershipStatus.ACTIVE
        self.joined_at = timezone.now()
        self.ended_at = None

    def suspend(self) -> None:
        self.status = MembershipStatus.SUSPENDED

    def revoke(self) -> None:
        self.status = MembershipStatus.REVOKED
        self.ended_at = timezone.now()
        self.is_primary = False


class Invitation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    elder = models.ForeignKey(
        Elder,
        on_delete=models.CASCADE,
        related_name="invitations",
    )
    invited_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="sent_invitations",
    )
    invite_code = models.CharField(max_length=64, unique=True)
    status = models.CharField(
        max_length=16,
        choices=InvitationStatus.choices,
        default=InvitationStatus.PENDING,
    )
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "identity_invitation"

    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    def can_be_accepted(self) -> bool:
        return self.status == InvitationStatus.PENDING and not self.is_expired


class EmergencyRecipient(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    elder = models.ForeignKey(
        Elder,
        on_delete=models.CASCADE,
        related_name="emergency_recipients",
    )
    membership = models.ForeignKey(
        Membership,
        on_delete=models.CASCADE,
        related_name="emergency_recipient_entries",
    )
    priority = models.PositiveSmallIntegerField()
    status = models.CharField(
        max_length=16,
        choices=EmergencyRecipientStatus.choices,
        default=EmergencyRecipientStatus.ACTIVE,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "identity_emergency_recipient"
        constraints = [
            models.UniqueConstraint(
                fields=["elder", "membership"],
                name="identity_emergency_recipient_unique_membership",
            ),
            models.UniqueConstraint(
                fields=["elder", "priority"],
                condition=Q(status=EmergencyRecipientStatus.ACTIVE),
                name="identity_emergency_recipient_unique_priority",
            ),
        ]
