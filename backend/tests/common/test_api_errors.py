"""Common API error mapping tests."""

import pytest
from rest_framework import status

from common.api.errors import domain_error_response
from domains.workflow.exceptions import ExecutionNotFoundError, InvalidExecutionStateError, WorkflowError


class _SampleNotFound(WorkflowError):
    pass


def test_domain_error_response_maps_not_found():
    response = domain_error_response(
        _SampleNotFound("missing"),
        base_type=WorkflowError,
        not_found=(_SampleNotFound, ExecutionNotFoundError),
        conflict=(InvalidExecutionStateError,),
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.data == {"detail": "missing"}


def test_domain_error_response_maps_conflict():
    response = domain_error_response(
        InvalidExecutionStateError("bad state"),
        base_type=WorkflowError,
        conflict=(InvalidExecutionStateError,),
    )
    assert response.status_code == status.HTTP_409_CONFLICT
