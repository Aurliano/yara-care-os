"""Identity & Access API routes."""

from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from domains.identity_access.api.views import (
    CurrentUserView,
    ElderDetailView,
    ElderListCreateView,
    ElderMembersView,
    EmergencyRecipientListConfigureView,
    InvitationAcceptView,
    InvitationListCreateView,
    InvitationRevokeView,
    MembershipRevokeView,
    MembershipRoleView,
    MembershipSuspendView,
    MyPermissionsView,
    PermissionCheckView,
    RegisterView,
)
from domains.identity_access.api.auth import PhoneTokenObtainPairSerializer

token_view = TokenObtainPairView.as_view(
    serializer_class=PhoneTokenObtainPairSerializer,
)

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="identity-register"),
    path("auth/token/", token_view, name="identity-token"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="identity-token-refresh"),
    path("users/me/", CurrentUserView.as_view(), name="identity-current-user"),
    path("elders/", ElderListCreateView.as_view(), name="identity-elder-list-create"),
    path("elders/<uuid:elder_id>/", ElderDetailView.as_view(), name="identity-elder-detail"),
    path(
        "elders/<uuid:elder_id>/members/",
        ElderMembersView.as_view(),
        name="identity-elder-members",
    ),
    path(
        "elders/<uuid:elder_id>/members/<uuid:membership_id>/role/",
        MembershipRoleView.as_view(),
        name="identity-membership-role",
    ),
    path(
        "elders/<uuid:elder_id>/members/<uuid:membership_id>/suspend/",
        MembershipSuspendView.as_view(),
        name="identity-membership-suspend",
    ),
    path(
        "elders/<uuid:elder_id>/members/<uuid:membership_id>/revoke/",
        MembershipRevokeView.as_view(),
        name="identity-membership-revoke",
    ),
    path(
        "elders/<uuid:elder_id>/invitations/",
        InvitationListCreateView.as_view(),
        name="identity-invitation-list-create",
    ),
    path(
        "elders/<uuid:elder_id>/invitations/<uuid:invitation_id>/revoke/",
        InvitationRevokeView.as_view(),
        name="identity-invitation-revoke",
    ),
    path(
        "invitations/accept/",
        InvitationAcceptView.as_view(),
        name="identity-invitation-accept",
    ),
    path(
        "elders/<uuid:elder_id>/emergency-recipients/",
        EmergencyRecipientListConfigureView.as_view(),
        name="identity-emergency-recipients",
    ),
    path(
        "elders/<uuid:elder_id>/permissions/me/",
        MyPermissionsView.as_view(),
        name="identity-my-permissions",
    ),
    path(
        "elders/<uuid:elder_id>/permissions/check/",
        PermissionCheckView.as_view(),
        name="identity-permission-check",
    ),
]
