"""Licensing API views."""

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from domains.identity_access.api.permissions import CanManageSubscription, HasElderAccess
from domains.licensing.api.serializers import (
    EntitlementCheckResponseSerializer,
    EntitlementCheckSerializer,
    EntitlementMapSerializer,
    LicenseActivateSerializer,
    LicenseChangePlanSerializer,
    LicenseSerializer,
    LimitResponseSerializer,
    PlanCreateSerializer,
    PlanSerializer,
)
from domains.licensing.exceptions import InvalidEntitlementError, LicensingError
from domains.licensing.models import License, Plan
from domains.licensing.services.entitlements import (
    can_use_feature,
    evaluate_entitlements_for_elder,
    get_limit,
)
from domains.licensing.services.licenses import (
    activate_license,
    change_license_plan,
    expire_license,
    get_active_license_for_elder,
    resume_license,
    revoke_license,
    suspend_license,
)
from domains.licensing.services.plans import create_plan, get_plan


def _licensing_error_response(exc: LicensingError) -> Response:
    code = status.HTTP_400_BAD_REQUEST
    if isinstance(exc, InvalidEntitlementError):
        code = status.HTTP_400_BAD_REQUEST
    return Response({"detail": str(exc)}, status=code)


class PlanListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        plans = Plan.objects.order_by("code")
        return Response(PlanSerializer(plans, many=True).data)

    def post(self, request: Request) -> Response:
        serializer = PlanCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        plan = create_plan(**serializer.validated_data)
        return Response(PlanSerializer(plan).data, status=status.HTTP_201_CREATED)


class PlanDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, plan_code: str) -> Response:
        plan = get_plan(plan_code)
        return Response(PlanSerializer(plan).data)


class ElderLicenseView(APIView):
    permission_classes = [IsAuthenticated, HasElderAccess]

    def get(self, request: Request, elder_id) -> Response:
        license = get_active_license_for_elder(elder_id)
        if license is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(LicenseSerializer(license).data)


class ElderLicenseActivateView(APIView):
    permission_classes = [IsAuthenticated, CanManageSubscription]

    def post(self, request: Request, elder_id) -> Response:
        serializer = LicenseActivateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            license = activate_license(elder_id=elder_id, **serializer.validated_data)
        except LicensingError as exc:
            return _licensing_error_response(exc)
        return Response(LicenseSerializer(license).data, status=status.HTTP_201_CREATED)


class ElderLicenseSuspendView(APIView):
    permission_classes = [IsAuthenticated, CanManageSubscription]

    def post(self, request: Request, elder_id, license_id) -> Response:
        license = get_object_or_404(License, pk=license_id, elder_id=elder_id)
        try:
            license = suspend_license(license_id=license.id)
        except LicensingError as exc:
            return _licensing_error_response(exc)
        return Response(LicenseSerializer(license).data)


class ElderLicenseResumeView(APIView):
    permission_classes = [IsAuthenticated, CanManageSubscription]

    def post(self, request: Request, elder_id, license_id) -> Response:
        license = get_object_or_404(License, pk=license_id, elder_id=elder_id)
        try:
            license = resume_license(license_id=license.id)
        except LicensingError as exc:
            return _licensing_error_response(exc)
        return Response(LicenseSerializer(license).data)


class ElderLicenseRevokeView(APIView):
    permission_classes = [IsAuthenticated, CanManageSubscription]

    def post(self, request: Request, elder_id, license_id) -> Response:
        license = get_object_or_404(License, pk=license_id, elder_id=elder_id)
        license = revoke_license(license_id=license.id)
        return Response(LicenseSerializer(license).data)


class ElderLicenseExpireView(APIView):
    permission_classes = [IsAuthenticated, CanManageSubscription]

    def post(self, request: Request, elder_id, license_id) -> Response:
        license = get_object_or_404(License, pk=license_id, elder_id=elder_id)
        try:
            license = expire_license(license_id=license.id)
        except LicensingError as exc:
            return _licensing_error_response(exc)
        return Response(LicenseSerializer(license).data)


class ElderLicenseChangePlanView(APIView):
    permission_classes = [IsAuthenticated, CanManageSubscription]

    def post(self, request: Request, elder_id, license_id) -> Response:
        license = get_object_or_404(License, pk=license_id, elder_id=elder_id)
        serializer = LicenseChangePlanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            license = change_license_plan(
                license_id=license.id,
                plan_code=serializer.validated_data["plan_code"],
            )
        except LicensingError as exc:
            return _licensing_error_response(exc)
        return Response(LicenseSerializer(license).data)


class ElderEntitlementCheckView(APIView):
    permission_classes = [IsAuthenticated, HasElderAccess]

    def post(self, request: Request, elder_id) -> Response:
        serializer = EntitlementCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        key = serializer.validated_data["entitlement_key"]
        try:
            allowed = can_use_feature(elder_id, key)
        except LicensingError as exc:
            return _licensing_error_response(exc)
        return Response(EntitlementCheckResponseSerializer({"allowed": allowed}).data)


class ElderLimitView(APIView):
    permission_classes = [IsAuthenticated, HasElderAccess]

    def get(self, request: Request, elder_id, entitlement_key: str) -> Response:
        try:
            limit = get_limit(elder_id, entitlement_key)
        except LicensingError as exc:
            return _licensing_error_response(exc)
        return Response(LimitResponseSerializer({"limit": limit}).data)


class ElderEntitlementsView(APIView):
    permission_classes = [IsAuthenticated, HasElderAccess]

    def get(self, request: Request, elder_id) -> Response:
        entitlements = evaluate_entitlements_for_elder(elder_id)
        return Response(EntitlementMapSerializer({"entitlements": entitlements}).data)
