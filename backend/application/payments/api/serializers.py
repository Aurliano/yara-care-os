"""Serializers for Payment Application REST API."""

from rest_framework import serializers

from domains.billing.enums import BillingInterval


class CheckoutRequestSerializer(serializers.Serializer):
    elder_id = serializers.UUIDField(required=True)
    plan_code = serializers.CharField(required=True, max_length=64)
    interval = serializers.ChoiceField(
        choices=BillingInterval.choices,
        default=BillingInterval.MONTHLY,
    )
    callback_url = serializers.URLField(required=False, allow_null=True)
    idempotency_key = serializers.CharField(
        required=False, max_length=128, allow_null=True
    )
    payer_mobile = serializers.CharField(required=False, max_length=32, allow_null=True)
    payer_email = serializers.EmailField(required=False, allow_null=True)


class CheckoutResponseSerializer(serializers.Serializer):
    provider_reference = serializers.CharField()
    redirect_url = serializers.CharField()
    invoice_id = serializers.UUIDField()
    payment_attempt_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=14, decimal_places=0)
    currency = serializers.CharField()


class PaymentCallbackResponseSerializer(serializers.Serializer):
    is_successful = serializers.BooleanField()
    invoice_id = serializers.UUIDField(allow_null=True)
    provider_reference = serializers.CharField()
    tracking_code = serializers.CharField(allow_blank=True)
    amount_paid = serializers.DecimalField(
        max_digits=14, decimal_places=0, allow_null=True
    )
    error_code = serializers.CharField(allow_blank=True)
    error_message = serializers.CharField(allow_blank=True)
    already_settled = serializers.BooleanField()
