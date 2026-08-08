from django.urls import path

from integration.api.provisioning_views import (
    HubProvisionAuthenticateView,
    HubProvisionRegisterView,
    HubProvisionRevokeView,
    HubProvisionStatusView,
)
from integration.api.views import (
    HubCommandCompleteView,
    HubCommandDeliverView,
    HubCommandFailView,
    HubConfirmationView,
    HubDeviceStateView,
    HubSessionAcceptView,
    HubSessionEndView,
    HubSyncDeltaView,
    HubSyncCompleteView,
    HubSyncSnapshotView,
    HubSyncStartView,
    PlatformHealthView,
    RuntimeHealthView,
    RuntimeProcessView,
)

urlpatterns = [
    path("hub/provision/register/", HubProvisionRegisterView.as_view(), name="hub-provision-register"),
    path("hub/provision/authenticate/", HubProvisionAuthenticateView.as_view(), name="hub-provision-authenticate"),
    path("hub/provision/status/", HubProvisionStatusView.as_view(), name="hub-provision-status"),
    path("hub/provision/revoke/", HubProvisionRevokeView.as_view(), name="hub-provision-revoke"),
    path("health/", PlatformHealthView.as_view(), name="platform-health"),
    path("hub/runtime/health/", RuntimeHealthView.as_view(), name="hub-runtime-health"),
    path("hub/runtime/process/", RuntimeProcessView.as_view(), name="hub-runtime-process"),
    path("hub/confirmations/", HubConfirmationView.as_view(), name="hub-confirmations"),
    path("hub/device/state/", HubDeviceStateView.as_view(), name="hub-device-state"),
    path("hub/device/commands/<uuid:command_id>/deliver/", HubCommandDeliverView.as_view(), name="hub-command-deliver"),
    path("hub/device/commands/<uuid:command_id>/complete/", HubCommandCompleteView.as_view(), name="hub-command-complete"),
    path("hub/device/commands/<uuid:command_id>/fail/", HubCommandFailView.as_view(), name="hub-command-fail"),
    path("hub/sync/start/", HubSyncStartView.as_view(), name="hub-sync-start"),
    path("hub/sync/sessions/<uuid:session_id>/delta/", HubSyncDeltaView.as_view(), name="hub-sync-delta"),
    path("hub/sync/sessions/<uuid:session_id>/snapshot/", HubSyncSnapshotView.as_view(), name="hub-sync-snapshot"),
    path("hub/sync/sessions/<uuid:session_id>/complete/", HubSyncCompleteView.as_view(), name="hub-sync-complete"),
    path("hub/communication/sessions/<uuid:session_id>/accept/", HubSessionAcceptView.as_view(), name="hub-session-accept"),
    path("hub/communication/sessions/<uuid:session_id>/end/", HubSessionEndView.as_view(), name="hub-session-end"),
]
