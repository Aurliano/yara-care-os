"""Licensing API routes."""

from django.urls import path

from domains.licensing.api.views import (
    ElderEntitlementCheckView,
    ElderEntitlementsView,
    ElderLicenseActivateView,
    ElderLicenseChangePlanView,
    ElderLicenseExpireView,
    ElderLicenseResumeView,
    ElderLicenseRevokeView,
    ElderLicenseSuspendView,
    ElderLicenseView,
    ElderLimitView,
    PlanDetailView,
    PlanListCreateView,
)

urlpatterns = [
    path("plans/", PlanListCreateView.as_view(), name="licensing-plan-list-create"),
    path("plans/<str:plan_code>/", PlanDetailView.as_view(), name="licensing-plan-detail"),
    path("elders/<uuid:elder_id>/license/", ElderLicenseView.as_view(), name="licensing-elder-license"),
    path(
        "elders/<uuid:elder_id>/license/activate/",
        ElderLicenseActivateView.as_view(),
        name="licensing-elder-license-activate",
    ),
    path(
        "elders/<uuid:elder_id>/license/<uuid:license_id>/suspend/",
        ElderLicenseSuspendView.as_view(),
        name="licensing-elder-license-suspend",
    ),
    path(
        "elders/<uuid:elder_id>/license/<uuid:license_id>/resume/",
        ElderLicenseResumeView.as_view(),
        name="licensing-elder-license-resume",
    ),
    path(
        "elders/<uuid:elder_id>/license/<uuid:license_id>/revoke/",
        ElderLicenseRevokeView.as_view(),
        name="licensing-elder-license-revoke",
    ),
    path(
        "elders/<uuid:elder_id>/license/<uuid:license_id>/expire/",
        ElderLicenseExpireView.as_view(),
        name="licensing-elder-license-expire",
    ),
    path(
        "elders/<uuid:elder_id>/license/<uuid:license_id>/change-plan/",
        ElderLicenseChangePlanView.as_view(),
        name="licensing-elder-license-change-plan",
    ),
    path(
        "elders/<uuid:elder_id>/entitlements/",
        ElderEntitlementsView.as_view(),
        name="licensing-elder-entitlements",
    ),
    path(
        "elders/<uuid:elder_id>/entitlements/check/",
        ElderEntitlementCheckView.as_view(),
        name="licensing-elder-entitlement-check",
    ),
    path(
        "elders/<uuid:elder_id>/entitlements/limits/<str:entitlement_key>/",
        ElderLimitView.as_view(),
        name="licensing-elder-limit",
    ),
]
