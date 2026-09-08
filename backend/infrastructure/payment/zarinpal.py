"""ZarinPal payment gateway adapter."""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from decimal import Decimal
from typing import Any

from django.conf import settings

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

logger = logging.getLogger("yara.payment.zarinpal")

ZARINPAL_SUCCESS_CODE = 100
ZARINPAL_ALREADY_VERIFIED_CODE = 101


class ZarinpalPaymentProvider(PaymentProvider):
    """Production adapter for ZarinPal v4 JSON REST API."""

    def __init__(
        self,
        *,
        merchant_id: str | None = None,
        sandbox: bool | None = None,
        timeout_seconds: int = 15,
    ) -> None:
        raw_merchant = (
            merchant_id
            if merchant_id is not None
            else getattr(settings, "ZARINPAL_MERCHANT_ID", "")
        )
        self._merchant_id = (raw_merchant or "").strip()
        self._sandbox = (
            sandbox
            if sandbox is not None
            else getattr(settings, "ZARINPAL_SANDBOX", True)
        )
        self._timeout_seconds = timeout_seconds

        if self._sandbox:
            self._api_base_url = "https://sandbox.zarinpal.com/pg/v4/payment/"
            self._redirect_base_url = "https://sandbox.zarinpal.com/pg/StartPay/"
        else:
            self._api_base_url = "https://payment.zarinpal.com/pg/v4/payment/"
            self._redirect_base_url = "https://payment.zarinpal.com/pg/StartPay/"

        # In production mode (non-sandbox), merchant ID must be configured
        if not self._sandbox and not self._merchant_id:
            raise PaymentProviderError(
                "ZarinPal merchant ID is not configured.",
                reason=PaymentFailureReason.NOT_CONFIGURED,
            )

    @property
    def merchant_id(self) -> str:
        return self._merchant_id

    @property
    def is_sandbox(self) -> bool:
        return self._sandbox

    def _normalize_amount_to_tomans(self, amount: Decimal, currency: str) -> int:
        """ZarinPal v4 API expects amount in Tomans (integer)."""
        curr = currency.upper()
        if curr in {"TOMAN", "TMN"}:
            return int(amount)
        if curr == "IRR":
            return int(amount // 10)
        return int(amount)

    def _execute_post(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self._api_base_url}{endpoint}"
        body_bytes = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "YaraCareOS/2.0",
        }
        req = urllib.request.Request(
            url, data=body_bytes, headers=headers, method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=self._timeout_seconds) as response:
                response_data = response.read().decode("utf-8")
                return json.loads(response_data)
        except urllib.error.HTTPError as err:
            try:
                error_body = err.read().decode("utf-8")
                parsed_error = json.loads(error_body)
                return parsed_error
            except Exception:
                raise PaymentProviderError(
                    f"ZarinPal HTTP error {err.code}: {err.reason}",
                    reason=PaymentFailureReason.REQUEST_REJECTED,
                ) from err
        except TimeoutError as err:
            raise PaymentProviderTimeoutError("ZarinPal request timed out.") from err
        except urllib.error.URLError as err:
            import socket

            if isinstance(err.reason, (socket.timeout, TimeoutError)):
                raise PaymentProviderTimeoutError(
                    "ZarinPal request timed out."
                ) from err
            raise PaymentProviderUnavailableError(
                f"Failed to connect to ZarinPal: {err}"
            ) from err
        except (ConnectionError, OSError) as err:
            raise PaymentProviderUnavailableError(
                f"Failed to connect to ZarinPal: {err}"
            ) from err
        except json.JSONDecodeError as err:
            raise PaymentProviderError(
                "Received malformed JSON from ZarinPal.",
                reason=PaymentFailureReason.INVALID_RESPONSE,
            ) from err

    def request_payment(self, request: PaymentRequest) -> PaymentRequestResult:
        toman_amount = self._normalize_amount_to_tomans(
            request.amount, request.currency
        )
        description = (
            request.description or f"Yara Care payment for invoice {request.invoice_id}"
        )

        payload: dict[str, Any] = {
            "merchant_id": self._merchant_id or "00000000-0000-0000-0000-000000000000",
            "amount": toman_amount,
            "callback_url": request.callback_url,
            "description": description,
            "metadata": {},
        }
        if request.payer_mobile:
            payload["metadata"]["mobile"] = request.payer_mobile
        if request.payer_email:
            payload["metadata"]["email"] = request.payer_email

        response_json = self._execute_post("request.json", payload)
        data = response_json.get("data")
        errors = response_json.get("errors")

        if (
            not data
            or not isinstance(data, dict)
            or data.get("code") != ZARINPAL_SUCCESS_CODE
        ):
            err_msg = (
                str(errors)
                if errors
                else f"ZarinPal request failed with response: {response_json}"
            )
            raise PaymentProviderError(
                err_msg,
                reason=PaymentFailureReason.REQUEST_REJECTED,
            )

        authority = data.get("authority")
        if not authority:
            raise PaymentProviderError(
                "ZarinPal response missing authority.",
                reason=PaymentFailureReason.INVALID_RESPONSE,
            )

        redirect_url = f"{self._redirect_base_url}{authority}"
        return PaymentRequestResult(
            provider_reference=authority,
            redirect_url=redirect_url,
            raw_response=response_json,
        )

    def verify_payment(
        self,
        *,
        provider_reference: str,
        amount: Decimal,
        currency: str,
        callback_payload: dict[str, Any] | None = None,
    ) -> PaymentVerificationResult:
        if callback_payload:
            status_param = str(callback_payload.get("Status", "")).upper()
            if status_param and status_param != "OK":
                return PaymentVerificationResult(
                    is_successful=False,
                    provider_reference=provider_reference,
                    error_code="CANCELLED_BY_USER",
                    error_message="Payment cancelled or declined at gateway return.",
                    raw_response=callback_payload,
                )

        toman_amount = self._normalize_amount_to_tomans(amount, currency)
        payload = {
            "merchant_id": self._merchant_id or "00000000-0000-0000-0000-000000000000",
            "amount": toman_amount,
            "authority": provider_reference,
        }

        response_json = self._execute_post("verify.json", payload)
        data = response_json.get("data")
        errors = response_json.get("errors")

        if data and isinstance(data, dict):
            code = data.get("code")
            if code in {ZARINPAL_SUCCESS_CODE, ZARINPAL_ALREADY_VERIFIED_CODE}:
                ref_id = str(data.get("ref_id", ""))
                card_pan = str(data.get("card_pan", ""))
                return PaymentVerificationResult(
                    is_successful=True,
                    provider_reference=provider_reference,
                    tracking_code=ref_id,
                    amount_paid=amount,
                    card_pan_masked=card_pan,
                    raw_response=response_json,
                )

        err_code = str(data.get("code", "")) if data and "code" in data else "-1"
        err_message = (
            data.get("message", "") if data else str(errors or "Verification failed.")
        )
        return PaymentVerificationResult(
            is_successful=False,
            provider_reference=provider_reference,
            error_code=err_code,
            error_message=err_message,
            raw_response=response_json,
        )
