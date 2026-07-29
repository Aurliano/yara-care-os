"""Emergency recipient configuration."""

from __future__ import annotations

from django.db import transaction

from domains.identity_access.enums import EmergencyRecipientStatus, MembershipStatus
from domains.identity_access.exceptions import AuthorizationError, InvalidMembershipStateError
from domains.identity_access.models import Elder, EmergencyRecipient, Membership, User
from domains.identity_access.services.authorization import can


@transaction.atomic
def configure_emergency_recipients(
    *,
    actor: User,
    elder: Elder,
    membership_ids: list,
) -> list[EmergencyRecipient]:
    if not can(actor, "MANAGE_MEMBERS", elder):
        raise AuthorizationError("Actor cannot configure emergency recipients for this Elder.")

    memberships = list(
        Membership.objects.filter(
            elder=elder,
            id__in=membership_ids,
            status=MembershipStatus.ACTIVE,
        )
    )
    if len(memberships) != len(set(membership_ids)):
        raise InvalidMembershipStateError(
            "All emergency recipients must be active memberships for this Elder."
        )

    EmergencyRecipient.objects.filter(elder=elder).delete()

    recipients: list[EmergencyRecipient] = []
    for priority, membership in enumerate(memberships, start=1):
        recipients.append(
            EmergencyRecipient.objects.create(
                elder=elder,
                membership=membership,
                priority=priority,
                status=EmergencyRecipientStatus.ACTIVE,
            )
        )
    return recipients


def get_emergency_recipients(elder: Elder) -> list[EmergencyRecipient]:
    return list(
        EmergencyRecipient.objects.filter(
            elder=elder,
            status=EmergencyRecipientStatus.ACTIVE,
        )
        .select_related("membership", "membership__user")
        .order_by("priority")
    )
