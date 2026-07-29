"""Elder and user profile operations."""

from __future__ import annotations

from django.db import transaction

from domains.identity_access.enums import MembershipStatus, RoleCode
from domains.identity_access.models import Elder, User
from domains.identity_access.services.memberships import create_membership


@transaction.atomic
def create_elder(*, actor: User, full_name: str, birth_date=None) -> Elder:
    elder = Elder.objects.create(full_name=full_name, birth_date=birth_date)
    create_membership(
        user=actor,
        elder=elder,
        role_code=RoleCode.PRIMARY_CAREGIVER,
        status=MembershipStatus.ACTIVE,
        is_primary=True,
    )
    return elder


@transaction.atomic
def create_user(*, phone: str, password: str, full_name: str, email: str = "") -> User:
    return User.objects.create_user(
        phone=phone,
        password=password,
        full_name=full_name,
        email=email,
    )


def update_user_profile(*, user: User, full_name: str | None = None, email: str | None = None) -> User:
    update_fields = []
    if full_name is not None:
        user.full_name = full_name
        update_fields.append("full_name")
    if email is not None:
        user.email = email
        update_fields.append("email")
    if update_fields:
        update_fields.append("updated_at")
        user.save(update_fields=update_fields)
    return user


def update_elder_profile(
    *,
    elder: Elder,
    full_name: str | None = None,
    birth_date=None,
) -> Elder:
    update_fields = []
    if full_name is not None:
        elder.full_name = full_name
        update_fields.append("full_name")
    if birth_date is not None:
        elder.birth_date = birth_date
        update_fields.append("birth_date")
    if update_fields:
        update_fields.append("updated_at")
        elder.save(update_fields=update_fields)
    return elder
