"""Tests for payment provider infrastructure."""

from __future__ import annotations

import io
import json
import urllib.error
import urllib.request
import uuid
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from infrastructure.payment.exceptions import (
    PaymentFailureReason,
    PaymentProviderError,
    PaymentProviderTimeoutError,
    PaymentProviderUnavailableError,
)
from infrastructure.payment.factory import get_payment_provider, reset_fake_provider
from infrastructure.payment.fake import FakePaymentProvider
from infrastructure.payment.ports import (
    PaymentProvider,
    PaymentRequest,
    PaymentRequestResult,
    PaymentVerificationResult,
)
from infrastructure.payment.zarinpal import (
    ZARINPAL_ALREADY_VERIFIED_CODE,
    ZARINPAL_SUCCESS_CODE,
    ZarinpalPaymentProvider,
)


@pytest.fixture(autouse=True)
def clean_fake_provider():
    reset_fake_provider()
    yield
    reset_fake_provider()


# ==============================================================================
# Protocol Conformance Tests
# ==============================================================================


def test_fake_payment_provider_conforms_to_protocol():
    provider = FakePaymentProvider()
    assert isinstance(provider, PaymentProvider)


def test_zarinpal_payment_provider_conforms_to_protocol():
    provider = ZarinpalPaymentProvider(merchant_id="test-merchant-id", sandbox=True)
    assert isinstance(provider, PaymentProvider)


# ==============================================================================
# FakePaymentProvider Tests
# ==============================================================================


def test_fake_provider_request_payment_success():
    provider = FakePaymentProvider()
    request = PaymentRequest(
        invoice_id=uuid.uuid4(),
        amount=Decimal("150000"),
        currency="TOMAN",
        callback_url="https://api.yara.test/callback",
        description="Subscription renewal",
        payer_mobile="09121112233",
    )

    result = provider.request_payment(request)

    assert isinstance(result, PaymentRequestResult)
    assert result.provider_reference.startswith("FAKE-AUTH-")
    assert f"/pay/{result.provider_reference}" in result.redirect_url
    assert len(provider.request_calls) == 1
    assert provider.requests[result.provider_reference] == request


def test_fake_provider_verify_payment_default_success():
    provider = FakePaymentProvider()
    ref = "FAKE-AUTH-1000"
    amount = Decimal("150000")

    result = provider.verify_payment(
        provider_reference=ref,
        amount=amount,
        currency="TOMAN",
    )

    assert isinstance(result, PaymentVerificationResult)
    assert result.is_successful is True
    assert result.provider_reference == ref
    assert result.tracking_code == f"TRK-{ref}"
    assert result.amount_paid == amount
    assert result.card_pan_masked == "5022-29**-****-1234"
    assert len(provider.verify_calls) == 1


def test_fake_provider_verify_payment_nok_callback():
    provider = FakePaymentProvider()
    result = provider.verify_payment(
        provider_reference="FAKE-AUTH-1000",
        amount=Decimal("100000"),
        currency="TOMAN",
        callback_payload={"Status": "NOK", "Authority": "FAKE-AUTH-1000"},
    )

    assert result.is_successful is False
    assert result.error_code == "CANCELLED_BY_USER"
    assert "cancelled" in result.error_message.lower()


def test_fake_provider_verify_payment_override_decline():
    provider = FakePaymentProvider()
    ref = "FAKE-AUTH-FAIL"
    provider.verification_overrides[ref] = False

    result = provider.verify_payment(
        provider_reference=ref,
        amount=Decimal("100000"),
        currency="TOMAN",
    )

    assert result.is_successful is False
    assert result.error_code == "VERIFICATION_FAILED"


def test_fake_provider_simulate_network_error():
    provider = FakePaymentProvider()
    provider.simulate_network_error = True

    with pytest.raises(PaymentProviderUnavailableError):
        provider.request_payment(
            PaymentRequest(
                invoice_id=uuid.uuid4(),
                amount=Decimal("100000"),
                currency="TOMAN",
                callback_url="https://test/cb",
            )
        )

    with pytest.raises(PaymentProviderUnavailableError):
        provider.verify_payment(
            provider_reference="FAKE-AUTH-1",
            amount=Decimal("100000"),
            currency="TOMAN",
        )


def test_fake_provider_simulate_timeout():
    provider = FakePaymentProvider()
    provider.simulate_timeout = True

    with pytest.raises(PaymentProviderTimeoutError):
        provider.request_payment(
            PaymentRequest(
                invoice_id=uuid.uuid4(),
                amount=Decimal("100000"),
                currency="TOMAN",
                callback_url="https://test/cb",
            )
        )

    with pytest.raises(PaymentProviderTimeoutError):
        provider.verify_payment(
            provider_reference="FAKE-AUTH-1",
            amount=Decimal("100000"),
            currency="TOMAN",
        )


def test_fake_provider_simulate_rejection():
    provider = FakePaymentProvider()
    provider.simulate_rejection = True
    provider.rejection_message = "Card blocked."

    with pytest.raises(PaymentProviderError) as exc_info:
        provider.request_payment(
            PaymentRequest(
                invoice_id=uuid.uuid4(),
                amount=Decimal("100000"),
                currency="TOMAN",
                callback_url="https://test/cb",
            )
        )

    assert exc_info.value.reason == PaymentFailureReason.REQUEST_REJECTED
    assert "Card blocked" in str(exc_info.value)


def test_fake_provider_reset():
    provider = FakePaymentProvider()
    provider.request_payment(
        PaymentRequest(
            invoice_id=uuid.uuid4(),
            amount=Decimal("100000"),
            currency="TOMAN",
            callback_url="https://test/cb",
        )
    )
    provider.simulate_network_error = True
    provider.verification_overrides["abc"] = False

    provider.reset()

    assert len(provider.request_calls) == 0
    assert len(provider.requests) == 0
    assert provider.simulate_network_error is False
    assert len(provider.verification_overrides) == 0


# ==============================================================================
# Factory Resolution Tests
# ==============================================================================


def test_factory_returns_fake_singleton(settings):
    settings.PAYMENT_PROVIDER = "fake"
    provider1 = get_payment_provider()
    provider2 = get_payment_provider()

    assert isinstance(provider1, FakePaymentProvider)
    assert provider1 is provider2


def test_factory_returns_zarinpal(settings):
    settings.PAYMENT_PROVIDER = "zarinpal"
    settings.ZARINPAL_MERCHANT_ID = "00000000-0000-0000-0000-000000000000"
    settings.ZARINPAL_SANDBOX = True

    provider = get_payment_provider()
    assert isinstance(provider, ZarinpalPaymentProvider)


def test_factory_raises_on_unsupported_provider(settings):
    settings.PAYMENT_PROVIDER = "unknown_gateway"

    with pytest.raises(PaymentProviderError) as exc_info:
        get_payment_provider()

    assert exc_info.value.reason == PaymentFailureReason.UNSUPPORTED_PROVIDER


# ==============================================================================
# ZarinpalPaymentProvider Tests
# ==============================================================================


def test_zarinpal_requires_merchant_id_in_production():
    with pytest.raises(PaymentProviderError) as exc_info:
        ZarinpalPaymentProvider(merchant_id="", sandbox=False)

    assert exc_info.value.reason == PaymentFailureReason.NOT_CONFIGURED


def test_zarinpal_amount_normalization():
    provider = ZarinpalPaymentProvider(merchant_id="test", sandbox=True)

    # TOMAN / TMN -> as-is
    assert provider._normalize_amount_to_tomans(Decimal("250000"), "TOMAN") == 250000
    assert provider._normalize_amount_to_tomans(Decimal("250000"), "TMN") == 250000

    # IRR -> divide by 10
    assert provider._normalize_amount_to_tomans(Decimal("2500000"), "IRR") == 250000


@patch("urllib.request.urlopen")
def test_zarinpal_request_payment_success(mock_urlopen):
    response_payload = {
        "data": {
            "code": ZARINPAL_SUCCESS_CODE,
            "message": "Success",
            "authority": "A00000000000000000000000000000000000",
            "fee_type": "Merchant",
            "fee": 100,
        },
        "errors": [],
    }
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(response_payload).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp
    mock_urlopen.return_value = mock_resp

    provider = ZarinpalPaymentProvider(
        merchant_id="00000000-0000-0000-0000-000000000000", sandbox=True
    )
    req = PaymentRequest(
        invoice_id=uuid.uuid4(),
        amount=Decimal("150000"),
        currency="TOMAN",
        callback_url="https://api.yara.care/callback",
        description="Test payment",
        payer_mobile="09123456789",
    )

    result = provider.request_payment(req)

    assert isinstance(result, PaymentRequestResult)
    assert result.provider_reference == "A00000000000000000000000000000000000"
    assert (
        "https://sandbox.zarinpal.com/pg/StartPay/A00000000000000000000000000000000000"
        == result.redirect_url
    )

    # Inspect HTTP request dispatched
    called_req = mock_urlopen.call_args[0][0]
    assert (
        called_req.full_url == "https://sandbox.zarinpal.com/pg/v4/payment/request.json"
    )
    sent_body = json.loads(called_req.data.decode("utf-8"))
    assert sent_body["amount"] == 150000
    assert sent_body["callback_url"] == "https://api.yara.care/callback"
    assert sent_body["metadata"]["mobile"] == "09123456789"


@patch("urllib.request.urlopen")
def test_zarinpal_request_payment_rejected(mock_urlopen):
    response_payload = {
        "data": [],
        "errors": {"code": -9, "message": "Validation error"},
    }
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(response_payload).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp
    mock_urlopen.return_value = mock_resp

    provider = ZarinpalPaymentProvider(merchant_id="test-merchant", sandbox=True)
    req = PaymentRequest(
        invoice_id=uuid.uuid4(),
        amount=Decimal("150000"),
        currency="TOMAN",
        callback_url="https://api.yara.care/callback",
    )

    with pytest.raises(PaymentProviderError) as exc_info:
        provider.request_payment(req)

    assert exc_info.value.reason == PaymentFailureReason.REQUEST_REJECTED


@patch("urllib.request.urlopen")
def test_zarinpal_verify_payment_success(mock_urlopen):
    response_payload = {
        "data": {
            "code": ZARINPAL_SUCCESS_CODE,
            "message": "Paid",
            "card_hash": "...",
            "card_pan": "502229******1234",
            "ref_id": 987654321,
            "fee_type": "Merchant",
            "fee": 0,
        },
        "errors": [],
    }
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(response_payload).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp
    mock_urlopen.return_value = mock_resp

    provider = ZarinpalPaymentProvider(merchant_id="test-merchant", sandbox=True)
    result = provider.verify_payment(
        provider_reference="A0001",
        amount=Decimal("150000"),
        currency="TOMAN",
        callback_payload={"Status": "OK", "Authority": "A0001"},
    )

    assert result.is_successful is True
    assert result.tracking_code == "987654321"
    assert result.card_pan_masked == "502229******1234"
    assert result.amount_paid == Decimal("150000")


@patch("urllib.request.urlopen")
def test_zarinpal_verify_payment_already_verified(mock_urlopen):
    response_payload = {
        "data": {
            "code": ZARINPAL_ALREADY_VERIFIED_CODE,
            "message": "Transaction already verified",
            "card_pan": "502229******1234",
            "ref_id": 987654321,
        },
        "errors": [],
    }
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(response_payload).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp
    mock_urlopen.return_value = mock_resp

    provider = ZarinpalPaymentProvider(merchant_id="test-merchant", sandbox=True)
    result = provider.verify_payment(
        provider_reference="A0001",
        amount=Decimal("150000"),
        currency="TOMAN",
    )

    assert result.is_successful is True
    assert result.tracking_code == "987654321"


def test_zarinpal_verify_payment_nok_callback_no_http():
    provider = ZarinpalPaymentProvider(merchant_id="test-merchant", sandbox=True)

    result = provider.verify_payment(
        provider_reference="A0001",
        amount=Decimal("150000"),
        currency="TOMAN",
        callback_payload={"Status": "NOK", "Authority": "A0001"},
    )

    assert result.is_successful is False
    assert result.error_code == "CANCELLED_BY_USER"


@patch("urllib.request.urlopen")
def test_zarinpal_verify_payment_declined_by_gateway(mock_urlopen):
    response_payload = {
        "data": {
            "code": -51,
            "message": "Session is not valid, done or canceled.",
        },
        "errors": [],
    }
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(response_payload).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp
    mock_urlopen.return_value = mock_resp

    provider = ZarinpalPaymentProvider(merchant_id="test-merchant", sandbox=True)
    result = provider.verify_payment(
        provider_reference="A0001",
        amount=Decimal("150000"),
        currency="TOMAN",
    )

    assert result.is_successful is False
    assert result.error_code == "-51"
    assert "Session is not valid" in result.error_message


@patch("urllib.request.urlopen")
def test_zarinpal_handles_network_error(mock_urlopen):
    mock_urlopen.side_effect = urllib.error.URLError("Network unreachable")

    provider = ZarinpalPaymentProvider(merchant_id="test-merchant", sandbox=True)
    req = PaymentRequest(
        invoice_id=uuid.uuid4(),
        amount=Decimal("150000"),
        currency="TOMAN",
        callback_url="https://api.yara.care/callback",
    )

    with pytest.raises(PaymentProviderUnavailableError):
        provider.request_payment(req)


@patch("urllib.request.urlopen")
def test_zarinpal_handles_timeout(mock_urlopen):
    mock_urlopen.side_effect = TimeoutError("Connection timed out")

    provider = ZarinpalPaymentProvider(merchant_id="test-merchant", sandbox=True)
    req = PaymentRequest(
        invoice_id=uuid.uuid4(),
        amount=Decimal("150000"),
        currency="TOMAN",
        callback_url="https://api.yara.care/callback",
    )

    with pytest.raises(PaymentProviderTimeoutError):
        provider.request_payment(req)


@patch("urllib.request.urlopen")
def test_zarinpal_handles_malformed_json(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.read.return_value = b"<!DOCTYPE html><html>Internal Error</html>"
    mock_resp.__enter__.return_value = mock_resp
    mock_urlopen.return_value = mock_resp

    provider = ZarinpalPaymentProvider(merchant_id="test-merchant", sandbox=True)
    req = PaymentRequest(
        invoice_id=uuid.uuid4(),
        amount=Decimal("150000"),
        currency="TOMAN",
        callback_url="https://api.yara.care/callback",
    )

    with pytest.raises(PaymentProviderError) as exc_info:
        provider.request_payment(req)

    assert exc_info.value.reason == PaymentFailureReason.INVALID_RESPONSE


@patch("urllib.request.urlopen")
def test_zarinpal_handles_url_error_socket_timeout(mock_urlopen):
    import socket

    mock_urlopen.side_effect = urllib.error.URLError(socket.timeout("timed out"))

    provider = ZarinpalPaymentProvider(merchant_id="test-merchant", sandbox=True)
    req = PaymentRequest(
        invoice_id=uuid.uuid4(),
        amount=Decimal("150000"),
        currency="TOMAN",
        callback_url="https://api.yara.care/callback",
    )

    with pytest.raises(PaymentProviderTimeoutError):
        provider.request_payment(req)


@patch("urllib.request.urlopen")
def test_zarinpal_handles_http_error_with_json_response(mock_urlopen):
    error_fp = io.BytesIO(
        json.dumps({"errors": {"code": -12, "message": "Bad request"}}).encode("utf-8")
    )
    mock_urlopen.side_effect = urllib.error.HTTPError(
        url="https://sandbox.zarinpal.com/pg/v4/payment/request.json",
        code=400,
        msg="Bad Request",
        hdrs={},
        fp=error_fp,
    )

    provider = ZarinpalPaymentProvider(merchant_id="test-merchant", sandbox=True)
    req = PaymentRequest(
        invoice_id=uuid.uuid4(),
        amount=Decimal("150000"),
        currency="TOMAN",
        callback_url="https://api.yara.care/callback",
    )

    with pytest.raises(PaymentProviderError) as exc_info:
        provider.request_payment(req)

    assert exc_info.value.reason == PaymentFailureReason.REQUEST_REJECTED


@patch("urllib.request.urlopen")
def test_zarinpal_handles_http_error_non_json(mock_urlopen):
    error_fp = io.BytesIO(b"Bad Gateway 502")
    mock_urlopen.side_effect = urllib.error.HTTPError(
        url="https://sandbox.zarinpal.com/pg/v4/payment/request.json",
        code=502,
        msg="Bad Gateway",
        hdrs={},
        fp=error_fp,
    )

    provider = ZarinpalPaymentProvider(merchant_id="test-merchant", sandbox=True)
    req = PaymentRequest(
        invoice_id=uuid.uuid4(),
        amount=Decimal("150000"),
        currency="TOMAN",
        callback_url="https://api.yara.care/callback",
    )

    with pytest.raises(PaymentProviderError) as exc_info:
        provider.request_payment(req)

    assert exc_info.value.reason == PaymentFailureReason.REQUEST_REJECTED
