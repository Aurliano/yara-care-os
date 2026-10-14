"""Tests for the SAYDA Care landing page and its coexistence with API endpoints."""

import pytest
from django.test import Client
from django.urls import reverse


@pytest.fixture
def client():
    return Client()


@pytest.mark.django_db
def test_landing_page_renders_successfully(client):
    """Verify that the landing page renders with HTTP 200 and correct Persian content."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response["Content-Type"]
    content = response.content.decode("utf-8")

    # Check Persian Title & Core Value Proposition
    assert "سایدا" in content
    assert "استقلال و عزت سالمند" in content
    assert "آرامش خاطر خانواده" in content

    # Check Sections
    assert 'id="hero"' in content
    assert 'id="value"' in content
    assert 'id="capabilities"' in content
    assert 'id="how-it-works"' in content
    assert 'id="trust"' in content
    assert 'id="download"' in content
    assert 'id="faq"' in content

    # Check CTAs and Disclaimer
    assert "دانلود اپلیکیشن مراقب" in content
    assert "سلب مسئولیت پزشکی" in content
    assert "سایدا یک سامانه همراه مراقبت خانوادگی است" in content


@pytest.mark.django_db
def test_privacy_policy_page_renders(client):
    """Verify that the privacy policy page renders with HTTP 200."""
    response = client.get(reverse("landing:privacy"))
    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "حریم خصوصی" in content
    assert "عدم فروش و عدم اشتراک اطلاعات" in content


@pytest.mark.django_db
def test_terms_of_service_page_renders(client):
    """Verify that the terms of service page renders with HTTP 200."""
    response = client.get(reverse("landing:terms"))
    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "سلب صریح مسئولیت پزشکی" in content
    assert "سایدا یک وسیله پزشکی" in content


@pytest.mark.django_db
def test_robots_txt_protects_api(client):
    """Verify robots.txt disallows /api/ and allows root."""
    response = client.get("/robots.txt")
    assert response.status_code == 200
    assert "text/plain" in response["Content-Type"]
    content = response.content.decode("utf-8")
    assert "Disallow: /api/" in content
    assert "Allow: /" in content


@pytest.mark.django_db
def test_sitemap_xml(client):
    """Verify sitemap.xml returns valid public URLs."""
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    assert "application/xml" in response["Content-Type"]
    content = response.content.decode("utf-8")
    assert "<loc>https://care-app.saydatech.ir/</loc>" in content
    assert "<loc>https://care-app.saydatech.ir/privacy/</loc>" in content


@pytest.mark.django_db
def test_api_v1_coexistence(client):
    """Verify that /api/v1/ endpoints are not shadowed or broken by the landing page."""
    # Hub provision endpoint requires POST and validates input
    response = client.post("/api/v1/hub/provision/authenticate/", {}, content_type="application/json")
    # Should be 400 (Bad Request due to missing fields) or 401, NOT 404
    assert response.status_code in [400, 401]
