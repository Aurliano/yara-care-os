"""Invitation lifecycle operations."""

from __future__ import annotations

import secrets

from django.db import transaction
from django.utils import timezone

from domains.identity_access.enums import InvitationStatus, MembershipStatus, RoleCode
from domains.identity_access.exceptions import (
    AuthorizationError,
    InvalidInvitationStateError,
    InvalidMembershipStateError,
)
from domains.identity_access.models import Elder, Invitation, Membership, User
from domains.identity_access.services.authorization import can
from domains.identity_access.services.memberships import create_membership


def _generate_invite_code() -> str:
    return secrets.token_urlsafe(24)


@transaction.atomic
def create_invitation(
    *,
    actor: User,
    elder: Elder,
    expires_at,
) -> Invitation:
    if not can(actor, "MANAGE_MEMBERS", elder):
        raise AuthorizationError("Actor cannot create invitations for this Elder.")

    return Invitation.objects.create(
        elder=elder,
        invited_by=actor,
        invite_code=_generate_invite_code(),
        expires_at=expires_at,
    )


@transaction.atomic
def accept_invitation(*, user: User, invitation: Invitation) -> Membership:
    if invitation.status == InvitationStatus.PENDING and invitation.is_expired:
        invitation.status = InvitationStatus.EXPIRED
        invitation.save(update_fields=["status"])
        raise InvalidInvitationStateError("Invitation has expired.")

    if not invitation.can_be_accepted():
        raise InvalidInvitationStateError("Invitation cannot be accepted.")

    existing = Membership.objects.filter(
        user=user,
        elder=invitation.elder,
        status__in=[MembershipStatus.INVITED, MembershipStatus.ACTIVE],
    ).first()
    if existing is not None:
        raise InvalidMembershipStateError("User already has an open membership for this Elder.")

    membership = create_membership(
        user=user,
        elder=invitation.elder,
        role_code=RoleCode.VIEWER,
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

    if invitation.status != InvitationStatus.PENDING:
        raise InvalidInvitationStateError("Only pending invitations can be revoked.")

    invitation.status = InvitationStatus.REVOKED
    invitation.save(update_fields=["status"])
    return invitation
