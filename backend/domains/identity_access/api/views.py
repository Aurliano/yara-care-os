"""Identity & Access API views."""

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from domains.identity_access.api.permissions import CanManageMembers, HasElderAccess
from domains.identity_access.api.serializers import (
    ElderCreateSerializer,
    ElderSerializer,
    EmergencyRecipientConfigureSerializer,
    EmergencyRecipientSerializer,
    InvitationAcceptSerializer,
    InvitationCreateSerializer,
    InvitationSerializer,
    MembershipRoleChangeSerializer,
    MembershipSerializer,
    PermissionCheckResponseSerializer,
    PermissionCheckSerializer,
    PermissionsListSerializer,
    RegisterSerializer,
    UserProfileUpdateSerializer,
    UserSerializer,
)
from domains.identity_access.exceptions import (
    AuthorizationError,
    IdentityAccessError,
    InvalidInvitationStateError,
    InvalidMembershipStateError,
    LastPrimaryCaregiverError,
)
from domains.identity_access.models import Elder, Invitation, Membership, User
from domains.identity_access.services.authorization import can, get_permissions
from domains.identity_access.services.emergency_recipients import (
    configure_emergency_recipients,
    get_emergency_recipients,
)
from domains.identity_access.services.invitations import (
    accept_invitation,
    create_invitation,
    revoke_invitation,
)
from domains.identity_access.services.memberships import (
    change_membership_role,
    revoke_membership,
    suspend_membership,
)
from domains.identity_access.services.profiles import (
    create_elder,
    create_user,
    update_elder_profile,
    update_user_profile,
)


def _domain_error_response(exc: IdentityAccessError) -> Response:
    if isinstance(exc, AuthorizationError):
        code = status.HTTP_403_FORBIDDEN
    elif isinstance(exc, (InvalidInvitationStateError, InvalidMembershipStateError)):
        code = status.HTTP_400_BAD_REQUEST
    elif isinstance(exc, LastPrimaryCaregiverError):
        code = status.HTTP_409_CONFLICT
    else:
        code = status.HTTP_400_BAD_REQUEST
    return Response({"detail": str(exc)}, status=code)


class RegisterView(APIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if User.objects.filter(phone=data["phone"]).exists():
            return Response(
                {"detail": "A user with this phone already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = create_user(
            phone=data["phone"],
            password=data["password"],
            full_name=data["full_name"],
            email=data.get("email", ""),
        )
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return Response(UserSerializer(request.user).data)

    def patch(self, request: Request) -> Response:
        serializer = UserProfileUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = update_user_profile(user=request.user, **serializer.validated_data)
        return Response(UserSerializer(user).data)


class ElderListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        elders = Elder.objects.filter(
            memberships__user=request.user,
            memberships__status="ACTIVE",
        ).distinct()
        return Response(ElderSerializer(elders, many=True).data)

    def post(self, request: Request) -> Response:
        serializer = ElderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        elder = create_elder(actor=request.user, **serializer.validated_data)
        return Response(ElderSerializer(elder).data, status=status.HTTP_201_CREATED)


class ElderDetailView(APIView):
    permission_classes = [IsAuthenticated, HasElderAccess]

    def get(self, request: Request, elder_id) -> Response:
        elder = get_object_or_404(Elder, pk=elder_id)
        if not can(request.user, "VIEW_ELDER_STATUS", elder):
            return Response(status=status.HTTP_403_FORBIDDEN)
        return Response(ElderSerializer(elder).data)

    def patch(self, request: Request, elder_id) -> Response:
        elder = get_object_or_404(Elder, pk=elder_id)
        serializer = ElderCreateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        if not can(request.user, "MANAGE_MEMBERS", elder):
            return Response(status=status.HTTP_403_FORBIDDEN)
        elder = update_elder_profile(elder=elder, **serializer.validated_data)
        return Response(ElderSerializer(elder).data)


class ElderMembersView(APIView):
    permission_classes = [IsAuthenticated, HasElderAccess]

    def get(self, request: Request, elder_id) -> Response:
        elder = get_object_or_404(Elder, pk=elder_id)
        memberships = Membership.objects.filter(elder=elder).select_related("user", "role")
        return Response(MembershipSerializer(memberships, many=True).data)


class MembershipRoleView(APIView):
    permission_classes = [IsAuthenticated, CanManageMembers]

    def patch(self, request: Request, elder_id, membership_id) -> Response:
        membership = get_object_or_404(Membership, pk=membership_id, elder_id=elder_id)
        serializer = MembershipRoleChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            membership = change_membership_role(
                actor=request.user,
                membership=membership,
                role_code=serializer.validated_data["role_code"],
            )
        except IdentityAccessError as exc:
            return _domain_error_response(exc)
        return Response(MembershipSerializer(membership).data)


class MembershipSuspendView(APIView):
    permission_classes = [IsAuthenticated, CanManageMembers]

    def post(self, request: Request, elder_id, membership_id) -> Response:
        membership = get_object_or_404(Membership, pk=membership_id, elder_id=elder_id)
        try:
            membership = suspend_membership(actor=request.user, membership=membership)
        except IdentityAccessError as exc:
            return _domain_error_response(exc)
        return Response(MembershipSerializer(membership).data)


class MembershipRevokeView(APIView):
    permission_classes = [IsAuthenticated, CanManageMembers]

    def post(self, request: Request, elder_id, membership_id) -> Response:
        membership = get_object_or_404(Membership, pk=membership_id, elder_id=elder_id)
        try:
            membership = revoke_membership(actor=request.user, membership=membership)
        except IdentityAccessError as exc:
            return _domain_error_response(exc)
        return Response(MembershipSerializer(membership).data)


class InvitationListCreateView(APIView):
    permission_classes = [IsAuthenticated, CanManageMembers]

    def get(self, request: Request, elder_id) -> Response:
        elder = get_object_or_404(Elder, pk=elder_id)
        invitations = Invitation.objects.filter(elder=elder).order_by("-created_at")
        return Response(InvitationSerializer(invitations, many=True).data)

    def post(self, request: Request, elder_id) -> Response:
        elder = get_object_or_404(Elder, pk=elder_id)
        serializer = InvitationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            invitation = create_invitation(
                actor=request.user,
                elder=elder,
                role_code=serializer.validated_data["role_code"],
                expires_at=serializer.validated_data["expires_at"],
            )
        except IdentityAccessError as exc:
            return _domain_error_response(exc)
        return Response(InvitationSerializer(invitation).data, status=status.HTTP_201_CREATED)


class InvitationAcceptView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = InvitationAcceptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invitation = get_object_or_404(
            Invitation,
            invite_code=serializer.validated_data["invite_code"],
        )
        try:
            membership = accept_invitation(user=request.user, invitation=invitation)
        except IdentityAccessError as exc:
            return _domain_error_response(exc)
        return Response(MembershipSerializer(membership).data, status=status.HTTP_201_CREATED)


class InvitationRevokeView(APIView):
    permission_classes = [IsAuthenticated, CanManageMembers]

    def post(self, request: Request, elder_id, invitation_id) -> Response:
        invitation = get_object_or_404(Invitation, pk=invitation_id, elder_id=elder_id)
        try:
            invitation = revoke_invitation(actor=request.user, invitation=invitation)
        except IdentityAccessError as exc:
            return _domain_error_response(exc)
        return Response(InvitationSerializer(invitation).data)


class EmergencyRecipientListConfigureView(APIView):
    permission_classes = [IsAuthenticated, CanManageMembers]

    def get(self, request: Request, elder_id) -> Response:
        elder = get_object_or_404(Elder, pk=elder_id)
        recipients = get_emergency_recipients(elder)
        return Response(EmergencyRecipientSerializer(recipients, many=True).data)

    def put(self, request: Request, elder_id) -> Response:
        elder = get_object_or_404(Elder, pk=elder_id)
        serializer = EmergencyRecipientConfigureSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            recipients = configure_emergency_recipients(
                actor=request.user,
                elder=elder,
                membership_ids=serializer.validated_data["membership_ids"],
            )
        except IdentityAccessError as exc:
            return _domain_error_response(exc)
        return Response(EmergencyRecipientSerializer(recipients, many=True).data)


class MyPermissionsView(APIView):
    permission_classes = [IsAuthenticated, HasElderAccess]

    def get(self, request: Request, elder_id) -> Response:
        elder = get_object_or_404(Elder, pk=elder_id)
        permissions = sorted(get_permissions(request.user, elder))
        return Response(PermissionsListSerializer({"permissions": permissions}).data)


class PermissionCheckView(APIView):
    permission_classes = [IsAuthenticated, HasElderAccess]

    def post(self, request: Request, elder_id) -> Response:
        elder = get_object_or_404(Elder, pk=elder_id)
        serializer = PermissionCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        allowed = can(
            request.user,
            serializer.validated_data["permission_code"],
            elder,
        )
        return Response(PermissionCheckResponseSerializer({"allowed": allowed}).data)
