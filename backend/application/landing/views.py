"""Views for the SAYDA Care official product landing page."""

from django.http import HttpResponse
from django.shortcuts import render
from django.views import View

# Single source of truth for store download destinations
# When official store listings are published, update URLs and set 'available': True
DOWNLOAD_CHANNELS = {
    "bazaar": {
        "name": "کافه‌بازار",
        "name_en": "Cafe Bazaar",
        "available": False,
        "url": "#download",
        "status_label": "به‌زودی در کافه‌بازار",
        "badge_text": "نسخه اندروید",
    },
    "myket": {
        "name": "مایکت",
        "name_en": "Myket",
        "available": False,
        "url": "#download",
        "status_label": "به‌زودی در مایکت",
        "badge_text": "نسخه اندروید",
    },
    "google_play": {
        "name": "گوگل‌پلی",
        "name_en": "Google Play",
        "available": False,
        "url": "#download",
        "status_label": "به‌زودی در گوگل‌پلی",
        "badge_text": "Android 7.0+",
    },
}

SUPPORT_INFO = {
    "email": "support@saydatech.ir",
    "domain": "care-app.saydatech.ir",
    "brand_name": "سایدا",
    "brand_en": "SAYDA Care",
    "tagline": "فناوری پنهان، آرامش پیدا — زیست‌بوم همراه مراقبت از عزیزانتان",
}


class LandingPageView(View):
    """Main responsive, Persian-first product landing page."""

    def get(self, request):
        context = {
            "channels": DOWNLOAD_CHANNELS,
            "support": SUPPORT_INFO,
            "canonical_url": f"https://{SUPPORT_INFO['domain']}/",
            "page_title": "سایدا (SAYDA Care) — زیست‌بوم مراقبت آرام و هوشمند از سالمندان",
            "meta_description": (
                "سایدا سامانه همراه مراقبت خانوادگی است؛ با یادآوری آرام داروها، هماهنگی خانواده و هاب هوشمند خانگی، "
                "آرامش خاطر را برای سالمندان و مراقبان به ارمغان می‌آورد."
            ),
        }
        return render(request, "landing/index.html", context)


class PrivacyPolicyView(View):
    """Transparent, verified Privacy Policy page."""

    def get(self, request):
        context = {
            "support": SUPPORT_INFO,
            "canonical_url": f"https://{SUPPORT_INFO['domain']}/privacy/",
            "page_title": "حریم خصوصی و حفاظت از داده‌ها — سایدا",
        }
        return render(request, "landing/privacy.html", context)


class TermsOfServiceView(View):
    """Terms of Service and non-medical disclaimer."""

    def get(self, request):
        context = {
            "support": SUPPORT_INFO,
            "canonical_url": f"https://{SUPPORT_INFO['domain']}/terms/",
            "page_title": "شرایط استفاده و سلب مسئولیت پزشکی — سایدا",
        }
        return render(request, "landing/terms.html", context)


def robots_txt(request):
    """Robots.txt ensuring search engines only index landing pages, protecting API routes."""
    lines = [
        "User-agent: *",
        "Disallow: /api/",
        "Disallow: /admin/",
        f"Allow: /",
        f"Sitemap: https://{SUPPORT_INFO['domain']}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")


def sitemap_xml(request):
    """Simple sitemap for public pages."""
    domain = SUPPORT_INFO["domain"]
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://{domain}/</loc>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://{domain}/privacy/</loc>
    <changefreq>monthly</changefreq>
    <priority>0.5</priority>
  </url>
  <url>
    <loc>https://{domain}/terms/</loc>
    <changefreq>monthly</changefreq>
    <priority>0.5</priority>
  </url>
</urlset>"""
    return HttpResponse(xml, content_type="application/xml; charset=utf-8")
