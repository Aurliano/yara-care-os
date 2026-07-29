"""Authorization queries and permission checks."""

from __future__ import annotations

from domains.identity_access.enums import MembershipStatus
from domains.identity_access.models import Elder, Membership, Permission, User


ACTIVE_MEMBERSHIP_STATUSES = {MembershipStatus.ACTIVE}


def get_membership(user: User, elder: Elder) -> Membership | None:
    return (
        Membership.objects.select_related("role")
        .filter(user=user, elder=elder, status__in=ACTIVE_MEMBERSHIP_STATUSES)
        .first()
    )


def user_is_associated_with_elder(user: User, elder: Elder) -> bool:
    return get_membership(user, elder) is not None


def get_permissions(user: User, elder: Elder) -> set[str]:
    membership = get_membership(user, elder)
    if membership is None:
        return set()

    return set(
        Permission.objects.filter(
            role_permissions__role=membership.role,
        ).values_list("code", flat=True)
    )


def can(user: User, permission_code: str, elder: Elder) -> bool:
    return permission_code in get_permissions(user, elder)
