"""Membership lifecycle operations."""

from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from domains.identity_access.enums import MembershipStatus, RoleCode
from domains.identity_access.exceptions import (
    AuthorizationError,
    InvalidMembershipStateError,
    LastPrimaryCaregiverError,
)
from domains.identity_access.models import Elder, Membership, Role, User
from domains.identity_access.services.authorization import can


def _get_role(code: str) -> Role:
    return Role.objects.get(code=code)


def _count_active_primary_caregivers(elder: Elder, *, exclude: Membership | None = None) -> int:
    queryset = Membership.objects.filter(
        elder=elder,
        status=MembershipStatus.ACTIVE,
        role__code=RoleCode.PRIMARY_CAREGIVER,
    )
    if exclude is not None:
        queryset = queryset.exclude(pk=exclude.pk)
    return queryset.count()


def _ensure_management_path_remains(elder: Elder, membership: Membership) -> None:
    if membership.status != MembershipStatus.ACTIVE:
        return

    is_manager = (
        membership.is_primary
        or membership.role.code == RoleCode.PRIMARY_CAREGIVER
    )
    if not is_manager:
        return

    remaining = _count_active_primary_caregivers(elder, exclude=membership)
    if remaining == 0:
        raise LastPrimaryCaregiverError(
            "At least one active primary caregiver must remain for this Elder."
        )


@transaction.atomic
def create_membership(
    *,
    user: User,
    elder: Elder,
    role_code: str,
    relationship: str = "",
    status: str = MembershipStatus.ACTIVE,
    is_primary: bool = False,
) -> Membership:
    role = _get_role(role_code)
    membership = Membership.objects.create(
        user=user,
        elder=elder,
        role=role,
        relationship=relationship,
        status=status,
        is_primary=is_primary,
        joined_at=timezone.now() if status == MembershipStatus.ACTIVE else None,
    )
    return membership


@transaction.atomic
def change_membership_role(
    *,
    actor: User,
    membership: Membership,
    role_code: str,
) -> Membership:
    if not can(actor, "MANAGE_MEMBERS", membership.elder):
        raise AuthorizationError("Actor cannot manage members for this Elder.")

    if membership.status != MembershipStatus.ACTIVE:
        raise InvalidMembershipStateError("Only active memberships can change role.")

    new_role = _get_role(role_code)
    was_manager = (
        membership.is_primary
        or membership.role.code == RoleCode.PRIMARY_CAREGIVER
    )
    if was_manager and new_role.code != RoleCode.PRIMARY_CAREGIVER:
        remaining = _count_active_primary_caregivers(membership.elder, exclude=membership)
        if remaining == 0:
            raise LastPrimaryCaregiverError(
                "At least one active primary caregiver must remain for this Elder."
            )

    membership.role = new_role
    if new_role.code != RoleCode.PRIMARY_CAREGIVER:
        membership.is_primary = False
    membership.save(update_fields=["role", "is_primary", "updated_at"])
    return membership


@transaction.atomic
def suspend_membership(*, actor: User, membership: Membership) -> Membership:
    if not can(actor, "MANAGE_MEMBERS", membership.elder):
        raise AuthorizationError("Actor cannot manage members for this Elder.")

    if membership.status != MembershipStatus.ACTIVE:
        raise InvalidMembershipStateError("Only active memberships can be suspended.")

    _ensure_management_path_remains(membership.elder, membership)
    membership.suspend()
    membership.save(update_fields=["status", "updated_at"])
    return membership


@transaction.atomic
def revoke_membership(*, actor: User, membership: Membership) -> Membership:
    if not can(actor, "MANAGE_MEMBERS", membership.elder):
        raise AuthorizationError("Actor cannot manage members for this Elder.")

    if membership.status not in {MembershipStatus.ACTIVE, MembershipStatus.SUSPENDED}:
        raise InvalidMembershipStateError("Membership cannot be revoked from its current state.")

    _ensure_management_path_remains(membership.elder, membership)
    membership.revoke()
    membership.save(update_fields=["status", "ended_at", "is_primary", "updated_at"])
    return membership
