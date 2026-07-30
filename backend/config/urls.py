"""Root URL configuration."""

from django.urls import include, path

urlpatterns = [
    path("api/v1/", include("common.urls")),
    path("api/v1/", include("domains.identity_access.api.urls")),
    path("api/v1/", include("domains.licensing.api.urls")),
    path("api/v1/", include("domains.event.api.urls")),
    path("api/v1/", include("domains.scheduling.api.urls")),
    path("api/v1/", include("domains.workflow.api.urls")),
]
