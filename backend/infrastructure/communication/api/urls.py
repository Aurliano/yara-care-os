from django.urls import path

from infrastructure.communication.api.views import CallEndView, CallStartView, LoginUrlView

urlpatterns = [
    path("communication/call/start/", CallStartView.as_view(), name="communication-call-start"),
    path("communication/call/end/", CallEndView.as_view(), name="communication-call-end"),
    path("communication/login-url/", LoginUrlView.as_view(), name="communication-login-url"),
]
