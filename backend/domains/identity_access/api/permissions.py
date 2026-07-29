"""DRF permission classes for Identity & Access."""

from rest_framework.permissions import BasePermission

from domains.identity_access.models import Elder
from domains.identity_access.services.authorization import can, user_is_associated_with_elder


class HasElderAccess(BasePermission):
    """Require an active membership for the Elder in the URL."""

    def has_permission(self, request, view) -> bool:
        elder_id = view.kwargs.get("elder_id")
        if elder_id is None:
            return False
        try:
            elder = Elder.objects.get(pk=elder_id)
        except Elder.DoesNotExist:
            return False
        return user_is_associated_with_elder(request.user, elder)


class HasElderPermission(BasePermission):
    """Require a specific permission code for the Elder in the URL."""

    permission_code: str = ""

    def has_permission(self, request, view) -> bool:
        elder_id = view.kwargs.get("elder_id")
        if elder_id is None or not self.permission_code:
            return False
        try:
            elder = Elder.objects.get(pk=elder_id)
        except Elder.DoesNotExist:
            return False
        return can(request.user, self.permission_code, elder)


class CanManageMembers(HasElderPermission):
    permission_code = "MANAGE_MEMBERS"


class CanManageSubscription(HasElderPermission):
    permission_code = "MANAGE_SUBSCRIPTION"
