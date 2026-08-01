"""Consistent domain exception to HTTP response mapping."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Type

from rest_framework import status
from rest_framework.response import Response


def domain_error_response(
    exc: Exception,
    *,
    base_type: Type[Exception],
    not_found: Iterable[Type[Exception]] = (),
    conflict: Iterable[Type[Exception]] = (),
    forbidden: Iterable[Type[Exception]] = (),
    bad_request: Iterable[Type[Exception]] = (),
) -> Response:
    """Map a domain exception to a consistent ``{"detail": ...}`` response."""
    if isinstance(exc, not_found):
        code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, forbidden):
        code = status.HTTP_403_FORBIDDEN
    elif isinstance(exc, conflict):
        code = status.HTTP_409_CONFLICT
    elif isinstance(exc, bad_request):
        code = status.HTTP_400_BAD_REQUEST
    elif isinstance(exc, base_type):
        code = status.HTTP_400_BAD_REQUEST
    else:
        raise exc
    return Response({"detail": str(exc)}, status=code)
