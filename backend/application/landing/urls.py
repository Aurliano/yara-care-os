from django.urls import path
from .views import LandingPageView, PrivacyPolicyView, TermsOfServiceView, robots_txt, sitemap_xml

app_name = "landing"

urlpatterns = [
    path("", LandingPageView.as_view(), name="home"),
    path("privacy/", PrivacyPolicyView.as_view(), name="privacy"),
    path("terms/", TermsOfServiceView.as_view(), name="terms"),
    path("robots.txt", robots_txt, name="robots"),
    path("sitemap.xml", sitemap_xml, name="sitemap"),
]
