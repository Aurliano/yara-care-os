import pytest
from django.db import IntegrityError

from domains.identity_access.enums import MembershipStatus
from domains.identity_access.models import EmergencyRecipient, Membership
from domains.identity_access.services.emergency_recipients import configure_emergency_recipients
from domains.identity_access.services.profiles import create_elder, create_user


@pytest.mark.django_db
def test_unique_primary_caregiver_constraint():
    owner = create_user(phone="+989111111111", password="securepass123", full_name="Owner")
    elder = create_elder(actor=owner, full_name="Elder One")
    second = create_user(phone="+989111111112", password="securepass123", full_name="Second")
    primary_role = Membership.objects.filter(elder=elder).first().role

    with pytest.raises(IntegrityError):
        Membership.objects.create(
            user=second,
            elder=elder,
            role=primary_role,
            status=MembershipStatus.ACTIVE,
            is_primary=True,
        )


@pytest.mark.django_db
def test_emergency_recipient_unique_membership(user, elder, second_user):
    membership_one = Membership.objects.get(user=user, elder=elder)
    membership_two = Membership.objects.create(
        user=second_user,
        elder=elder,
        role=membership_one.role,
        status=MembershipStatus.ACTIVE,
        is_primary=False,
    )
    configure_emergency_recipients(
        actor=user,
        elder=elder,
        membership_ids=[membership_one.id],
    )
    with pytest.raises(IntegrityError):
        EmergencyRecipient.objects.create(
            elder=elder,
            membership=membership_one,
            priority=2,
            status="ACTIVE",
        )
