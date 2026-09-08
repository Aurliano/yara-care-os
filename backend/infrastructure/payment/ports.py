"""Payment provider protocol and result data transfer objects."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class PaymentRequest:
    """Input parameters for initiating a payment transaction."""

    invoice_id: uuid.UUID
    amount: Decimal
    currency: str  # TOMAN or IRR
    callback_url: str
    description: str = ""
    payer_mobile: str | None = None
    payer_email: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PaymentRequestResult:
    """Normalized response from initiating a payment transaction."""

    provider_reference: str  # Opaque gateway reference token or authority
    redirect_url: str  # Gateway URL to redirect the user to complete payment
    raw_response: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PaymentVerificationResult:
    """Normalized result from verifying a payment transaction outcome."""

    is_successful: bool
    provider_reference: str
    tracking_code: str = ""  # Bank reference ID (e.g. ref_id)
    amount_paid: Decimal | None = None
    card_pan_masked: str = ""
    error_code: str = ""
    error_message: str = ""
    raw_response: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class PaymentProvider(Protocol):
    """Abstract provider port for external payment gateways."""

    def request_payment(self, request: PaymentRequest) -> PaymentRequestResult:
        """Initiate payment transaction with provider and return redirect credentials."""
        ...

    def verify_payment(
        self,
        *,
        provider_reference: str,
        amount: Decimal,
        currency: str,
        callback_payload: dict[str, Any] | None = None,
    ) -> PaymentVerificationResult:
        """Verify payment outcome with provider server-to-server."""
        ...
