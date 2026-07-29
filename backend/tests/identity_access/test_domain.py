import pytest
from django.utils import timezone
from datetime import timedelta

from domains.identity_access.enums import MembershipStatus, RoleCode
from domains.identity_access.exceptions import (
    InvalidInvitationStateError,
    InvalidMembershipStateError,
    LastPrimaryCaregiverError,
)
from domains.identity_access.models import Invitation, Membership, Role
from domains.identity_access.services.authorization import can, get_permissions, user_is_associated_with_elder
from domains.identity_access.services.emergency_recipients import configure_emergency_recipients
from domains.identity_access.services.invitations import accept_invitation, create_invitation, revoke_invitation
from domains.identity_access.services.memberships import create_membership, revoke_membership
from domains.identity_access.services.profiles import create_elder


@pytest.mark.django_db
def test_user_elder_relationship_through_membership(user, elder):
    membership = Membership.objects.get(user=user, elder=elder)
    assert membership.status == MembershipStatus.ACTIVE
    assert membership.is_primary is True
    assert membership.role.code == RoleCode.PRIMARY_CAREGIVER
    assert user_is_associated_with_elder(user, elder)


@pytest.mark.django_db
def test_permission_check_uses_membership_context(user, elder):
    assert can(user, "MANAGE_MEMBERS", elder) is True
    assert can(user, "MANAGE_MEDICATION", elder) is True
    permissions = get_permissions(user, elder)
    assert "VIEW_ELDER_STATUS" in permissions


@pytest.mark.django_db
def test_viewer_has_limited_permissions(viewer_user, elder, user):
    create_membership(
        user=viewer_user,
        elder=elder,
        role_code=RoleCode.VIEWER,
        status=MembershipStatus.ACTIVE,
    )
    permissions = get_permissions(viewer_user, elder)
    assert permissions == {"VIEW_ELDER_STATUS"}
    assert can(viewer_user, "MANAGE_MEMBERS", elder) is False


@pytest.mark.django_db
def test_duplicate_active_membership_blocked(user, elder):
    with pytest.raises(Exception):
        create_membership(
            user=user,
            elder=elder,
            role_code=RoleCode.CAREGIVER,
            status=MembershipStatus.ACTIVE,
        )


@pytest.mark.django_db
def test_invitation_accept_creates_membership_with_invitation_role(user, elder, second_user):
    invitation = create_invitation(
        actor=user,
        elder=elder,
        role_code=RoleCode.CAREGIVER,
        expires_at=timezone.now() + timedelta(days=7),
    )
    membership = accept_invitation(user=second_user, invitation=invitation)
    invitation.refresh_from_db()

    assert invitation.status == "ACCEPTED"
    assert invitation.accepted_at is not None
    assert invitation.role.code == RoleCode.CAREGIVER
    assert membership.user == second_user
    assert membership.elder == elder
    assert membership.status == MembershipStatus.ACTIVE
    assert membership.role.code == RoleCode.CAREGIVER


@pytest.mark.django_db
def test_expired_invitation_persists_expired_before_reject(user, elder, second_user):
    caregiver_role = Role.objects.get(code=RoleCode.CAREGIVER)
    invitation = Invitation.objects.create(
        elder=elder,
        invited_by=user,
        role=caregiver_role,
        invite_code="expired-code-123",
        expires_at=timezone.now() - timedelta(hours=1),
    )
    with pytest.raises(InvalidInvitationStateError):
        accept_invitation(user=second_user, invitation=invitation)
    invitation.refresh_from_db()
    assert invitation.status == "EXPIRED"


@pytest.mark.django_db
def test_revoked_invitation_cannot_be_accepted(user, elder, second_user):
    invitation = create_invitation(
        actor=user,
        elder=elder,
        role_code=RoleCode.VIEWER,
        expires_at=timezone.now() + timedelta(days=1),
    )
    revoke_invitation(actor=user, invitation=invitation)
    with pytest.raises(Exception):
        accept_invitation(user=second_user, invitation=invitation)


@pytest.mark.django_db
def test_accept_invitation_does_not_create_duplicate(user, elder, second_user):
    invitation = create_invitation(
        actor=user,
        elder=elder,
        role_code=RoleCode.VIEWER,
        expires_at=timezone.now() + timedelta(days=1),
    )
    accept_invitation(user=second_user, invitation=invitation)
    invitation2 = create_invitation(
        actor=user,
        elder=elder,
        role_code=RoleCode.CAREGIVER,
        expires_at=timezone.now() + timedelta(days=1),
    )
    with pytest.raises(InvalidMembershipStateError):
        accept_invitation(user=second_user, invitation=invitation2)


@pytest.mark.django_db
def test_cannot_revoke_last_primary_caregiver(user, elder):
    membership = Membership.objects.get(user=user, elder=elder)
    with pytest.raises(LastPrimaryCaregiverError):
        revoke_membership(actor=user, membership=membership)


@pytest.mark.django_db
def test_emergency_recipient_requires_active_membership(user, elder, second_user):
    membership = create_membership(
        user=second_user,
        elder=elder,
        role_code=RoleCode.CAREGIVER,
        status=MembershipStatus.ACTIVE,
    )
    recipients = configure_emergency_recipients(
        actor=user,
        elder=elder,
        membership_ids=[membership.id],
    )
    assert len(recipients) == 1
    assert recipients[0].membership_id == membership.id


@pytest.mark.django_db
def test_emergency_recipient_rejects_membership_from_other_elder(user, elder, second_user):
    other_elder = create_elder(actor=second_user, full_name="Other Elder")
    other_membership = Membership.objects.get(user=second_user, elder=other_elder)

    with pytest.raises(InvalidMembershipStateError):
        configure_emergency_recipients(
            actor=user,
            elder=elder,
            membership_ids=[other_membership.id],
        )


@pytest.mark.django_db
def test_cross_elder_access_denied(user, elder, second_user, authenticated_client):
    response = authenticated_client.get(f"/api/v1/elders/{elder.id}/")
    assert response.status_code == 200

    client = authenticated_client
    client.force_authenticate(user=second_user)
    response = client.get(f"/api/v1/elders/{elder.id}/")
    assert response.status_code == 403
