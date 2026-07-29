"""Invitation lifecycle operations."""

from __future__ import annotations

import secrets

from django.db import transaction
from django.utils import timezone

from domains.identity_access.enums import InvitationStatus, MembershipStatus
from domains.identity_access.exceptions import (
    AuthorizationError,
    InvalidInvitationStateError,
    InvalidMembershipStateError,
)
from domains.identity_access.models import Elder, Invitation, Membership, Role, User
from domains.identity_access.services.authorization import can
from domains.identity_access.services.memberships import create_membership


def _generate_invite_code() -> str:
    return secrets.token_urlsafe(24)


def _get_role(role_code: str) -> Role:
    return Role.objects.get(code=role_code)


def persist_invitation_expiration_if_due(invitation: Invitation) -> bool:
    """Persist EXPIRED outside caller transactions so rejection does not roll it back."""
    updated = Invitation.objects.filter(
        pk=invitation.pk,
        status=InvitationStatus.PENDING,
        expires_at__lte=timezone.now(),
    ).update(status=InvitationStatus.EXPIRED)
    if updated:
        invitation.refresh_from_db()
        return True
    return False


@transaction.atomic
def create_invitation(
    *,
    actor: User,
    elder: Elder,
    role_code: str,
    expires_at,
) -> Invitation:
    if not can(actor, "MANAGE_MEMBERS", elder):
        raise AuthorizationError("Actor cannot create invitations for this Elder.")

    return Invitation.objects.create(
        elder=elder,
        invited_by=actor,
        role=_get_role(role_code),
        invite_code=_generate_invite_code(),
        expires_at=expires_at,
    )


def accept_invitation(*, user: User, invitation: Invitation) -> Membership:
    if persist_invitation_expiration_if_due(invitation):
        raise InvalidInvitationStateError("Invitation has expired.")

    with transaction.atomic():
        invitation = Invitation.objects.select_for_update().get(pk=invitation.pk)

        if not invitation.can_be_accepted():
            raise InvalidInvitationStateError("Invitation cannot be accepted.")

        existing = Membership.objects.filter(
            user=user,
            elder=invitation.elder,
            status__in=[MembershipStatus.INVITED, MembershipStatus.ACTIVE],
        ).first()
        if existing is not None:
            raise InvalidMembershipStateError(
                "User already has an open membership for this Elder."
            )

        membership = create_membership(
            user=user,
            elder=invitation.elder,
            role_code=invitation.role.code,
            status=MembershipStatus.ACTIVE,
        )

        invitation.status = InvitationStatus.ACCEPTED
        invitation.accepted_at = timezone.now()
        invitation.save(update_fields=["status", "accepted_at"])

    return membership


@transaction.atomic
def revoke_invitation(*, actor: User, invitation: Invitation) -> Invitation:
    if not can(actor, "MANAGE_MEMBERS", invitation.elder):
        raise AuthorizationError("Actor cannot revoke invitations for this Elder.")

    persist_invitation_expiration_if_due(invitation)
    invitation.refresh_from_db()
    if invitation.status != InvitationStatus.PENDING:
        raise InvalidInvitationStateError("Only pending invitations can be revoked.")

    invitation.status = InvitationStatus.REVOKED
    invitation.save(update_fields=["status"])
    return invitation
