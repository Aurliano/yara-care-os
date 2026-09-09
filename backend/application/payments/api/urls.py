"""URL routing for Payment Application."""

from django.urls import path

from application.payments.api.views import CheckoutView, PaymentVerifyView

urlpatterns = [
    path("payments/checkout/", CheckoutView.as_view(), name="payment-checkout"),
    path("payments/verify/", PaymentVerifyView.as_view(), name="payment-verify"),
]
