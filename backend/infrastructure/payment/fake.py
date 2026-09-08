"""In-memory FakePaymentProvider for deterministic tests and offline local development."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from infrastructure.payment.exceptions import (
    PaymentFailureReason,
    PaymentProviderError,
    PaymentProviderTimeoutError,
    PaymentProviderUnavailableError,
)
from infrastructure.payment.ports import (
    PaymentProvider,
    PaymentRequest,
    PaymentRequestResult,
    PaymentVerificationResult,
)


class FakePaymentProvider(PaymentProvider):
    """Deterministic, zero-network payment provider for automated testing."""

    def __init__(self) -> None:
        self.requests: dict[str, PaymentRequest] = {}
        self.request_calls: list[PaymentRequest] = []
        self.verify_calls: list[dict[str, Any]] = []
        self._next_reference_counter: int = 1000

        # Failure & behavior simulation hooks
        self.simulate_network_error: bool = False
        self.simulate_timeout: bool = False
        self.simulate_rejection: bool = False
        self.rejection_message: str = "Transaction rejected by mock bank."
        self.default_verify_success: bool = True
        self.verification_overrides: dict[str, bool] = {}

    def request_payment(self, request: PaymentRequest) -> PaymentRequestResult:
        self.request_calls.append(request)

        if self.simulate_network_error:
            raise PaymentProviderUnavailableError(
                "Simulated network outage in fake payment provider."
            )
        if self.simulate_timeout:
            raise PaymentProviderTimeoutError(
                "Simulated HTTP timeout in fake payment provider."
            )
        if self.simulate_rejection:
            raise PaymentProviderError(
                self.rejection_message,
                reason=PaymentFailureReason.REQUEST_REJECTED,
            )

        ref = f"FAKE-AUTH-{self._next_reference_counter}"
        self._next_reference_counter += 1
        self.requests[ref] = request

        redirect_url = f"https://mock-gateway.yara.test/pay/{ref}"
        return PaymentRequestResult(
            provider_reference=ref,
            redirect_url=redirect_url,
            raw_response={"mock": True, "reference": ref},
        )

    def verify_payment(
        self,
        *,
        provider_reference: str,
        amount: Decimal,
        currency: str,
        callback_payload: dict[str, Any] | None = None,
    ) -> PaymentVerificationResult:
        call_record = {
            "provider_reference": provider_reference,
            "amount": amount,
            "currency": currency,
            "callback_payload": callback_payload or {},
        }
        self.verify_calls.append(call_record)

        if self.simulate_network_error:
            raise PaymentProviderUnavailableError(
                "Simulated network outage during verification."
            )
        if self.simulate_timeout:
            raise PaymentProviderTimeoutError(
                "Simulated HTTP timeout during verification."
            )

        # If callback payload indicates explicit cancellation/failure from gateway return:
        if (
            callback_payload
            and str(callback_payload.get("Status", "")).upper() == "NOK"
        ):
            return PaymentVerificationResult(
                is_successful=False,
                provider_reference=provider_reference,
                error_code="CANCELLED_BY_USER",
                error_message="User cancelled payment at the gateway.",
                raw_response=callback_payload,
            )

        should_succeed = self.verification_overrides.get(
            provider_reference, self.default_verify_success
        )

        if should_succeed:
            tracking_code = f"TRK-{provider_reference}"
            return PaymentVerificationResult(
                is_successful=True,
                provider_reference=provider_reference,
                tracking_code=tracking_code,
                amount_paid=amount,
                card_pan_masked="5022-29**-****-1234",
                raw_response={
                    "status": "OK",
                    "code": 100,
                    "tracking_code": tracking_code,
                },
            )
        else:
            return PaymentVerificationResult(
                is_successful=False,
                provider_reference=provider_reference,
                error_code="VERIFICATION_FAILED",
                error_message="Simulated verification decline from payment provider.",
                raw_response={"status": "NOK", "code": -51},
            )

    def reset(self) -> None:
        self.requests.clear()
        self.request_calls.clear()
        self.verify_calls.clear()
        self.simulate_network_error = False
        self.simulate_timeout = False
        self.simulate_rejection = False
        self.rejection_message = "Transaction rejected by mock bank."
        self.default_verify_success = True
        self.verification_overrides.clear()
