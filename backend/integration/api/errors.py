"""Hub API error mapping for cross-domain service calls."""

from __future__ import annotations

from rest_framework.response import Response

from common.api.errors import domain_error_response
from domains.care.exceptions import CareError
from domains.communication.exceptions import CommunicationError
from domains.device.exceptions import DeviceError
from domains.synchronization.exceptions import SynchronizationError
from domains.workflow.exceptions import WorkflowError
from integration.exceptions import IntegrationError


def hub_error_response(exc: Exception) -> Response:
    if isinstance(exc, DeviceError):
        from domains.device.api.views import _device_error_response

        return _device_error_response(exc)
    if isinstance(exc, WorkflowError):
        from domains.workflow.api.views import _workflow_error_response

        return _workflow_error_response(exc)
    if isinstance(exc, CommunicationError):
        from domains.communication.api.views import _communication_error_response

        return _communication_error_response(exc)
    if isinstance(exc, SynchronizationError):
        from domains.synchronization.api.views import _sync_error_response

        return _sync_error_response(exc)
    if isinstance(exc, CareError):
        from domains.care.api.views import _care_error_response

        return _care_error_response(exc)
    if isinstance(exc, IntegrationError):
        return domain_error_response(exc, base_type=IntegrationError, bad_request=(IntegrationError,))
    raise exc
