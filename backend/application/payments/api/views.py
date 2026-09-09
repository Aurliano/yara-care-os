"""REST API views for payment orchestration."""

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from application.payments.api.serializers import (
    CheckoutRequestSerializer,
    CheckoutResponseSerializer,
    PaymentCallbackResponseSerializer,
)
from application.payments.coordinator import (
    handle_payment_callback,
    initiate_checkout,
)
from application.payments.exceptions import (
    ElderNotFoundError,
    InvalidCallbackError,
    PaymentAttemptNotFoundError,
    PaymentCoordinatorError,
    PermissionDeniedError,
    PlanNotFoundError,
    PlanPriceNotFoundError,
)
from common.api.errors import domain_error_response
from domains.licensing.exceptions import (
    InvalidLicenseStateError,
    InvalidSubscriptionStateError,
)
from infrastructure.payment.exceptions import PaymentProviderError


class CheckoutView(APIView):
    """Initiate a payment checkout flow for an Elder subscription."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = CheckoutRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            result = initiate_checkout(
                payer_user=request.user,
                elder_id=data["elder_id"],
                plan_code=data["plan_code"],
                interval=data.get("interval", "MONTHLY"),
                callback_url=data.get("callback_url"),
                idempotency_key=data.get("idempotency_key"),
                payer_mobile=data.get("payer_mobile"),
                payer_email=data.get("payer_email"),
            )
        except (
            PermissionDeniedError,
            PlanPriceNotFoundError,
            PlanNotFoundError,
            ElderNotFoundError,
            InvalidLicenseStateError,
            InvalidSubscriptionStateError,
            PaymentProviderError,
            PaymentCoordinatorError,
        ) as exc:
            return domain_error_response(
                exc,
                base_type=PaymentCoordinatorError,
                forbidden=(PermissionDeniedError,),
                not_found=(
                    ElderNotFoundError,
                    PlanNotFoundError,
                    PlanPriceNotFoundError,
                ),
                conflict=(),
                bad_request=(
                    InvalidLicenseStateError,
                    InvalidSubscriptionStateError,
                    PaymentProviderError,
                ),
            )

        resp_serializer = CheckoutResponseSerializer(result)
        return Response(resp_serializer.data, status=status.HTTP_200_OK)


class PaymentVerifyView(APIView):
    """Handle bank gateway redirect/callback to verify payment."""

    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        return self._process_callback(request)

    def post(self, request: Request) -> Response:
        return self._process_callback(request)

    def _process_callback(self, request: Request) -> Response:
        # Support parameters from query params (GET) or body (POST)
        params = (
            request.query_params.dict() if request.method == "GET" else request.data
        )
        if not isinstance(params, dict):
            params = {}

        authority = (
            params.get("Authority")
            or params.get("authority")
            or params.get("provider_reference")
            or ""
        )

        try:
            result = handle_payment_callback(
                provider_reference=authority,
                callback_payload=params,
            )
        except (InvalidCallbackError, PaymentAttemptNotFoundError) as exc:
            return domain_error_response(
                exc,
                base_type=PaymentCoordinatorError,
                not_found=(PaymentAttemptNotFoundError,),
                bad_request=(InvalidCallbackError,),
            )

        resp_serializer = PaymentCallbackResponseSerializer(result)
        return Response(resp_serializer.data, status=status.HTTP_200_OK)
