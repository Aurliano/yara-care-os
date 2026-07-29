"""Root URL configuration."""

from django.urls import include, path

urlpatterns = [
    path("api/v1/", include("common.urls")),
    path("api/v1/", include("domains.identity_access.api.urls")),
]
