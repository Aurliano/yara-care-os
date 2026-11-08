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
        "available": True,
        "url": "https://cafebazaar.ir/app/ir.sayda.yara.family",
        "status_label": "دانلود مستقیم از کافه‌بازار",
        "badge_text": "نسخه رسمی اندروید",
    },
    "myket": {
        "name": "مایکت",
        "name_en": "Myket",
        "available": False,
        "url": "#download",
        "status_label": "به‌زودی در مایکت",
        "badge_text": "بزودی",
    },
    "sibapp": {
        "name": "سیب‌اپ (iOS)",
        "name_en": "SibApp",
        "available": False,
        "url": "#download",
        "status_label": "به‌زودی برای آیفون و آیپد",
        "badge_text": "بزودی",
    },
}

PRODUCTS_CATALOG = [
    {
        "id": "product-sayda-hub",
        "title": "هاب رومیزی سایدا (SAYDA Hub)",
        "subtitle": "همراه آرام و باوقار سالمند در خانه",
        "description": "دستگاه رومیزی مستقل با صفحه‌نمایش لمسی، ساعت و تاریخ شمسی بزرگ، یادآوری صوتی ملایم نوبت‌های دارو و دکمه تک‌لمسی تأیید مصرف. کارکرد مستقل حتی در زمان قطعی اینترنت.",
        "badge_label": "آماده سفارش",
        "badge_class": "badge-available",
        "price_summary": "۳۸,۹۰۰,۰۰۰ تومان (خرید قطعی)",
        "price_original": "۴۲,۰۰۰,۰۰۰ تومان",
        "price_note": "شامل ۳ ماه اشتراک رایگان سامانه و پشتیبانی دائمی | امکان اجاره مدت‌دار دستگاه",
        "features": [
            "یادآوری صوتی و لمسی سر ساعت با حروف درشت",
            "امکان برقراری تماس صوتی و تصویری مستقیم با خانواده",
            "کارکرد کاملاً مستقل ساعت و داروها به صورت آفلاین",
            "بلندگوی رسا و تنظیم خودکار روشنایی روز و شب",
        ],
        "items_included": [
            "تبلت هاب رومیزی سایدا",
            "پایه چوبی باوقار",
            "آداپتور و کابل تغذیه دائم",
            "راهنمای راه‌اندازی فارسی",
        ],
        "status": "available",
        "icon": "hub",
        "image_webp": "landing/images/products/sayda-hub.png",
        "image_png": "landing/images/products/sayda-hub.png",
        "image_alt": "هاب رومیزی هوشمند سایدا",
        "cta_label": "ثبت سفارش و مشاوره خرید",
        "cta_subject": "درخواست خرید هاب رومیزی سایدا",
        "cta_type": "order",
    },
    {
        "id": "product-smart-pillbox",
        "title": "جعبه داروی هوشمند سایدا",
        "subtitle": "محفظه ۷ روزه با راهنمای نوری خانه دارو",
        "description": "جعبه داروی متصل به هاب خانگی با نشانگرهای نوری که در هر نوبت، فقط درب خانهٔ داروی همان وعده را مشخص می‌کند تا از اشتباهات دارویی پیشگیری شود.",
        "badge_label": "به‌زودی عرضه می‌شود",
        "badge_class": "badge-coming-soon",
        "price_summary": "در حال آماده‌سازی برای تولید انبوه",
        "price_note": "اولویت دریافت با اعضایی است که زودتر نوبت رزرو کرده باشند",
        "features": [
            "روشن شدن چراغ خانهٔ داروی همان وعده",
            "سنسور تشخیص باز شدن درب محفظه دارویی",
            "همگام‌سازی خودکار با هاب و اپلیکیشن خانواده",
            "باتری شارژی بادوام با درگاه Type-C",
        ],
        "items_included": [
            "جعبه داروی هوشمند ۷ روزه",
            "کابل شارژ اختصاصی",
            "دفترچه راهنمای فارسی",
        ],
        "status": "coming_soon",
        "icon": "pillbox",
        "image_webp": "landing/images/products/smart-pillbox.jpg",
        "image_png": "landing/images/products/smart-pillbox.jpg",
        "image_alt": "جعبه داروی هوشمند سایدا",
        "cta_label": "رزرو در نوبت اول عرضه",
        "cta_subject": "درخواست رزرو جعبه داروی هوشمند سایدا",
        "cta_type": "reserve",
    },
    {
        "id": "product-health-band",
        "title": "دستبند سلامت و پایش آرام",
        "subtitle": "پایش ضربان قلب و ایمنی عزیز سالخورده",
        "description": "دستبند ضدآب و بسیار سبک با باتری بادوام که ضربان قلب و پایداری فیزیکی سالمند را به آرامی ثبت و به هاب رومیزی منتقل می‌کند.",
        "badge_label": "به‌زودی عرضه می‌شود",
        "badge_class": "badge-coming-soon",
        "price_summary": "در حال آماده‌سازی برای تولید انبوه",
        "price_note": "امکان اتصال مستقیم به هاب رومیزی بدون نیاز به گوشی",
        "features": [
            "پایش پیوسته ضربان قلب در طول شبانه‌روز",
            "طراحی سبک و ارگونومیک بدون دکمه‌های گیج‌کننده",
            "هشدار باتری در برنامه خانواده قبل از خاموش شدن",
            "شارژر مغناطیسی آسان و ضدآب بودن بدنه",
        ],
        "items_included": [
            "دستبند پایش سلامت",
            "بند ضدحساسیت و سبک",
            "شارژر مغناطیسی اختصاصی",
        ],
        "status": "coming_soon",
        "icon": "heart",
        "image_webp": "landing/images/products/smart-band.jpg",
        "image_png": "landing/images/products/smart-band.jpg",
        "image_alt": "دستبند سلامت و پایش آرام سایدا",
        "cta_label": "رزرو در نوبت اول عرضه",
        "cta_subject": "درخواست رزرو دستبند سلامت سایدا",
        "cta_type": "reserve",
    },
]

PRICING_DATA = {
    "hub": {
        "title": "همراه رومیزی سالمند (هاب سایدا)",
        "subtitle": "خرید قطعی دستگاه هاب رومیزی به همراه کلیه ملحقات و پایه اختصاصی",
        "original_price": "۴۲,۰۰۰,۰۰۰",
        "price": "۳۸,۹۰۰,۰۰۰",
        "discount_badge": "تخفیف ۳,۱۰۰,۰۰۰ تومانی",
        "features": [
            "تبلت لمسی اختصاصی هاب با اعداد و ساعت بزرگ فارسی",
            "پایه چوبی باوقار رومیزی متناسب با دکوراسیون منزل",
            "۳ ماه اشتراک کامل سامانه ابری و خدمات نرم‌افزاری رایگان",
            "پشتیبانی دائمی و به‌روزرسانی‌های نرم‌افزاری",
            "مالکیت قطعی بدون محدودیت زمانی",
        ],
    },
    "subscriptions": [
        {
            "id": "sub-monthly",
            "title": "اشتراک ماهانه",
            "duration": "۱ ماه",
            "price": "۶۵۰,۰۰۰",
            "period": "ماهانه",
            "badge": None,
            "desc": "مناسب برای استفاده منعطف و همراهی کوتاه‌مدت",
            "features": [
                "همگام‌سازی آنی میان هاب و اپلیکیشن خانواده",
                "تعریف نامحدود نوبت‌های دارویی و گزارش مصرف",
                "تماس صوتی و تصویری درون‌برنامه‌ای با تبلت خانه",
                "پشتیبانی فنی و راهنمایی خانواده",
            ],
        },
        {
            "id": "sub-quarterly",
            "title": "اشتراک سه‌ماهه",
            "duration": "۳ ماه",
            "original_price": "۱,۹۵۰,۰۰۰",
            "price": "۱,۸۵۰,۰۰۰",
            "period": "سه‌ماهه",
            "badge": "محبوب‌ترین انتخاب",
            "discount_label": "۱۰۰,۰۰۰ تومان تخفیف",
            "desc": "بهترین توازن اقتصادی برای پیگیری مداوم درمان",
            "features": [
                "کلیه امکانات اشتراک کامل سایدا",
                "صرفه‌جویی اقتصادی نسبت به تمدید ماهانه",
                "گزارش‌های جامع روند پایش و مصرف دارویی",
                "اولویت پاسخگویی در پشتیبانی خانواده",
            ],
        },
        {
            "id": "sub-yearly",
            "title": "اشتراک سالانه",
            "duration": "۱۲ ماه",
            "original_price": "۷,۸۰۰,۰۰۰",
            "price": "۶,۵۰۰,۰۰۰",
            "period": "سالانه",
            "badge": "بیشترین صرفه‌جویی (۲ ماه هدیه)",
            "discount_label": "۱,۳۰۰,۰۰۰ تومان تخفیف",
            "desc": "یک سال آرامش خاطر کامل بدون دغدغه تمدید مکرر",
            "features": [
                "کلیه امکانات اشتراک کامل سایدا",
                "۲ ماه اشتراک هدیه رایگان در طول سال",
                "پشتیبانی ویژه و اختصاصی برای کل اعضای خانواده",
                "تضمین ثبات هزینه اشتراک در طول یک سال",
            ],
        },
    ],
    "rental": {
        "monthly_sub": 650000,
        "daily_sub_rate": 21667,  # 650,000 / 30
        "surcharge_percent": 60,
        "daily_rental_rate": 34667,  # 21,667 * 1.6
    },
}

SUPPORT_INFO = {
    "email": "info@saydatech.ir",
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
            "products": PRODUCTS_CATALOG,
            "pricing": PRICING_DATA,
            "canonical_url": f"https://{SUPPORT_INFO['domain']}/",
            "page_title": "سایدا (SAYDA Care) — زیست‌بوم مراقبت آرام و هوشمند از سالمندان",
            "meta_description": (
                "سایدا سامانه همراه مراقبت خانوادگی است؛ با یادآوری آرام داروها، هماهنگی خانواده و هاب هوشمند خانگی، "
                "آرامش خاطر را برای سالمندان و مراقبان به ارمغان می‌آورد."
            ),
        }
        return render(request, "landing/index.html", context)


class PrivacyPolicyView(View):
    """Honest, transparent privacy policy."""

    def get(self, request):
        context = {
            "support": SUPPORT_INFO,
            "canonical_url": f"https://{SUPPORT_INFO['domain']}/privacy/",
            "page_title": "سیاست حفظ حریم خصوصی — سایدا",
            "meta_description": "تعهدنامه حفظ محرمانگی و امانت‌داری داده‌های خانواده و سالمندان در زیست‌بوم سایدا.",
        }
        return render(request, "landing/privacy.html", context)


class TermsOfServiceView(View):
    """Clear, human-readable terms of service with explicit medical disclaimer."""

    def get(self, request):
        context = {
            "support": SUPPORT_INFO,
            "canonical_url": f"https://{SUPPORT_INFO['domain']}/terms/",
            "page_title": "شرایط استفاده و سلب مسئولیت پزشکی — سایدا",
            "meta_description": "قوانین و شرایط استفاده از خدمات سایدا به همراه سلب صریح مسئولیت پزشکی.",
        }
        return render(request, "landing/terms.html", context)


def robots_txt(request):
    """Standard robots.txt protecting API routes."""
    lines = [
        "User-agent: *",
        "Disallow: /api/",
        "Disallow: /admin/",
        "Allow: /",
        f"Sitemap: https://{SUPPORT_INFO['domain']}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")


def sitemap_xml(request):
    """Simple sitemap for public landing pages."""
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
