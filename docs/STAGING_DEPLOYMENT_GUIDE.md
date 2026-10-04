# Yara Care OS — Staging Deployment Guide (R2-A)

**Version:** 1.0  
**Status:** Approved / Active  
**Scope:** R2-A Staging Environment & Deployment Readiness  
**Target:** Local & Dedicated Staging Hosts (Pre-Physical QA)

---

## ۱. نمای کلی و فلسفه محیط Staging

محیط Staging در سیستم عامل مراقبت یارا (Yara Care OS) با هدف فراهم‌سازی یک بستر کاملاً ایزوله، آزمون‌پذیر و مشابه پروداکشن برای انجام ارزیابی‌های فیزیکی (Physical QA) بدون خطر نشت داده، دستکاری ناخواسته دیتابیس‌های توسعه، یا اجرای فرامین مخرب ایجاد شده است.

این سند دقیقاً منعکس‌کننده‌ی پیاده‌سازی‌های واقعی انجام‌شده در اسپرینت‌های **R2-A.0 تا R2-A.5** است.

---

## ۲. ماتریس محیط‌ها (Environment Matrix)

سیستم بر پایه‌ی متغیر محیطی بنیادین `YARA_ENVIRONMENT` کنترل می‌شود (تنظیم `DEBUG` صرفاً یک ویژگی رفتاری فریم‌ورک است و به عنوان شناسه محیط در نظر گرفته نمی‌شود).

| محیط (`YARA_ENVIRONMENT`) | نام دیتابیس استاندارد | فایل Settings پیش‌فرض | رفتار گارد استارتاپ (`validate_database_environment`) |
| :--- | :--- | :--- | :--- |
| **`development`** | `yara` | `config.settings.development` | اتصال مجاز به `yara` یا دیتابیس محلی توسعه. در صورت اتصال به دیتابیس‌های حاوی پسوند `_production` بلاک می‌شود. |
| **`test`** | `yara_test` | `config.settings.test` | مجاز به اتصال به دیتابیس تست (`yara_test`). |
| **`staging`** | `yara_staging` | `config.settings.staging` | **گارد سخت‌گیرانه:** استارتاپ پروژه بلافاصله متوقف (`ImproperlyConfigured`) می‌شود اگر نام دیتابیس دقیقاً `yara_staging` نباشد. اتصال به `yara` یا هر دیتابیس دیگر در این حالت ممنوع است. |
| **`production`** | دیتابیس اختصاصی (مثلاً `yara_production`) | `config.settings.production` | **گارد محافظتی:** اتصال به دیتابیس‌های `yara`، `yara_staging`، `yara_test` ممنوع است. تمام فرامین seed و reset بلاک می‌شوند. |

---

## ۳. امنیت فرامین مدیریتی (Management Command Safety)

طبق پیاده‌سازی گارد اشتراکی در [backend/common/guards.py](file:///c:/yara-care-os/backend/common/guards.py) با تابع `ensure_not_production`، رفتار ۵ دستور حساس مدیریتی به تفکیک محیط‌ها به شرح جدول زیر است:

| دستور مدیریتی (`manage.py`) | محیط Development | محیط Staging | محیط Production | نیاز به تایید صریح (`--confirm`) |
| :--- | :--- | :--- | :--- | :--- |
| **`seed_family_lab`** | ✅ مجاز | ✅ مجاز | ⛔ **بلاک قطعی** (`CommandError`) | خیر |
| **`seed_hub_provision`** | ✅ مجاز | ✅ مجاز | ⛔ **بلاک قطعی** (`CommandError`) | خیر |
| **`seed_hub_dev_sync`** | ✅ مجاز | ✅ مجاز | ⛔ **بلاک قطعی** (`CommandError`) | خیر |
| **`reset_test_environment`** | ✅ مجاز (با تایید) | ✅ مجاز | ⛔ **بلاک قطعی** (`CommandError`) | **بله** (فلگ `--confirm` الزامی است، در غیر این صورت پرامپت تعاملی و در حالت غیرتعاملی خطا صادر می‌شود). |
| **`remove_test_device`** | ✅ مجاز | ✅ مجاز | ⛔ **بلاک قطعی** (`CommandError`) | **بله** (به‌طور پیش‌فرض `--dry-run` فعال است؛ حذف واقعی نیازمند ارسال صریح `--confirm` است). |

> [!CAUTION]
> هیچ دستور `seed_*` یا `reset_*` تحت هیچ شرایطی امکان اجرا در محیط پروداکشن را ندارد. گارد امنیتی قبل از هرگونه تغییر یا اتصال مخرب، اجرای دستور را متوقف می‌کند.

---

## ۴. پروب‌های سلامت و آمادگی (Health & Readiness Endpoints)

سه نقطه پایانی برای تفکیک سطوح مختلف مانیتورینگ پیاده‌سازی شده‌اند. همه این اندپوینت‌ها **بدون نیاز به احراز هویت (Unauthenticated)** جهت پایش توسط Orchestrator یا Load Balancer در دسترس هستند:

```
/api/v1/health/live/   → فقط پاسخگویی پروسس (Liveness)
/api/v1/health/ready/  → اتصال دیتابیس + کامل بودن مایگریشن‌ها (Readiness)
/api/v1/health/        → عیب‌یابی عمیق ماژول‌های اینتگریشن و صف‌ها (Diagnostics)
```

### ۱. پروب زنده بودن (`GET /api/v1/health/live/`)
- **هدف:** بررسی اجرای پروسس سرور پایتون برای Liveness Probe (تصمیم‌گیری ریستارت کانتینر توسط سیستم عامل/ارکستریتور).
- **کوئری دیتابیس:** **دقیقاً صفر کوئری**. حتی در صورت قطعی کامل دیتابیس، این اندپوینت ۲۰۰ برمی‌گرداند.
- **پاسخ موفق (HTTP 200):**
  ```json
  {"status": "alive"}
  ```

### ۲. پروب آمادگی ترافیک (`GET /api/v1/health/ready/`)
- **هدف:** تایید اتصال دیتابیس و عدم وجود مایگریشن اعمال‌نشده قبل از هدایت ترافیک به سمت پاد/اینستنس.
- **بررسی مایگریشن:** با استفاده مستقیم از `MigrationExecutor(connection)` داخلی جنگو و بدون فراخوانی subprocess.
- **پاسخ موفق (HTTP 200):**
  ```json
  {
    "status": "ready",
    "checks": {
      "database": {"status": "ok"},
      "migrations": {"status": "ok"}
    }
  }
  ```
- **پاسخ خطا در قطعی دیتابیس (HTTP 503 Service Unavailable):**
  *(پیام خطا کاملاً Sanitize شده و هیچ نام کاربری، هاست یا جزئیات اتصالی به بیرون نشت نمی‌کند)*
  ```json
  {
    "status": "unready",
    "checks": {
      "database": {
        "status": "error",
        "detail": "Database connectivity check failed."
      },
      "migrations": {
        "status": "unavailable",
        "detail": "Database unreachable."
      }
    }
  }
  ```
- **پاسخ خطا هنگام وجود مایگریشن معلق (HTTP 503 Service Unavailable):**
  ```json
  {
    "status": "unready",
    "checks": {
      "database": {"status": "ok"},
      "migrations": {
        "status": "error",
        "detail": "2 unapplied migration(s) pending."
      }
    }
  }
  ```

### ۳. پروب عیب‌یابی پلتفرم (`GET /api/v1/health/`)
- **هدف:** مانیتورینگ عملکردی وضعیت داخلی پلتفرم یارا شامل وضعیت صف Outbox، رویدادهای پردازش‌شده اینتگریشن، و نشست‌های همگام‌سازی (Synchronization).

---

## ۵. راهنمای راه‌اندازی گام‌به‌گام Staging روی سرور جدید

### گام ۱: ساخت دیتابیس فیزیکی در PostgreSQL
در سرور PostgreSQL، دیتابیس مجزای `yara_staging` را ایجاد کنید:
```sql
CREATE DATABASE yara_staging OWNER yara;
```

### گام ۲: تنظیم فایل محیطی Staging در Backend
از روی فایل الگو کپی بگیرید:
```bash
cp backend/env.staging.example backend/.env.staging
```
محتوای `backend/.env.staging` را ویرایش و اطلاعات اتصال PostgreSQL را وارد کنید:
```ini
YARA_ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO

# نام دیتابیس حتماً باید yara_staging باشد:
STAGING_DATABASE_URL=postgres://yara:YOUR_PASSWORD@localhost:5432/yara_staging
DATABASE_URL=postgres://yara:YOUR_PASSWORD@localhost:5432/yara_staging

SECRET_KEY=generate-a-strong-random-secret-key-with-at-least-50-characters
```

### گام ۳: اعمال مایگریشن‌ها بر روی دیتابیس Staging
```bash
cd backend
python manage.py migrate --settings=config.settings.staging
```

### گام ۴: مقداردهی اولیه داده‌های آزمایشی (Seed)
برای سناریوهای تست آزمایشگاهی (Physical QA)، دستور زیر را اجرا کنید تا مراقب و سالمند تستی ساخته شوند:
```bash
python manage.py seed_family_lab --settings=config.settings.staging
```
*(این دستور مراقب با شماره تلفن `+989121111111` و هاب متصل را ثبت می‌کند).*

### گام ۵: اجرای وب‌سرور و اعتبارسنجی
```bash
python manage.py runserver 0.0.0.0:8000 --settings=config.settings.staging
```
سپس از یک ترمینال دیگر، وضعیت را تست کنید:
```bash
curl http://localhost:8000/api/v1/health/ready/
```
باید پاسخ `200 OK` با بدنه `{"status": "ready", ...}` دریافت شود.

---

## ۶. پیکربندی کلاینت‌ها (Clients Configuration)

> [!IMPORTANT]
> فایل‌های با پسوند `.example` درون مخزن Git نگهداری می‌شوند و تعمداً **هیچ‌گونه رمز عبور یا کلید دسترسی واقعی ندارند**. مقادیر واقعی را در فایل‌های محلی قرار دهید.

### الف) اپلیکیشن خانواده (Family App - Expo / React Native)
1. فایل الگو در مسیر [apps/family/.env.staging.example](file:///c:/yara-care-os/apps/family/.env.staging.example) قرار دارد.
2. آن را به `apps/family/.env.staging` یا `apps/family/.env` کپی کنید:
   ```bash
   cp apps/family/.env.staging.example apps/family/.env
   ```
3. متغیر `EXPO_PUBLIC_API_BASE_URL` را بر اساس آدرس سرور استیجینگ تنظیم کنید:
   - برای تست روی دستگاه فیزیکی در شبکه محلی آزمایشگاه: `http://10.254.230.230:8000/api/v1` (یا IP سرور در LAN)
   - برای شبیه‌ساز اندروید: `http://10.0.2.2:8000/api/v1`
4. این فایل توسط `.gitignore` محافظت شده و کامیت نمی‌شود.

### ب) تبلت هاب (Android Hub)
1. فایل الگو در مسیر [apps/hub/local.properties.staging.example](file:///c:/yara-care-os/apps/hub/local.properties.staging.example) قرار دارد.
2. محتوای آن را در `apps/hub/local.properties` قرار دهید:
   ```properties
   hub.backend.url=http://10.254.230.230:8000/api/v1/
   hub.provision.phone=+989121111111
   hub.provision.password=<STAGING_CAREGIVER_PASSWORD>
   hub.livekit.url=wss://yara-care-8qxaz9wd.livekit.cloud
   sdk.dir=C\:\\Users\\YourUser\\AppData\\Local\\Android\\Sdk
   ```
3. مقدار `<STAGING_CAREGIVER_PASSWORD>` را با رمز تعیین‌شده در فرآیند seed جایگزین کنید.
4. فایل‌های `local.properties` و `local.properties.*` در `.gitignore` محافظت شده‌اند.

---

## ۷. رویه پشتیبان‌گیری و بازگردانی (Backup & Rollback)

قبل از اجرای هر تست مخرب یا تغییر ساختار در `yara_staging`، از رویه زیر استفاده کنید:

### تهیه نسخه پشتیبان دستی (Backup via pg_dump)
```bash
pg_dump -U postgres -h localhost -d yara_staging -F c -b -v -f yara_staging_pre_qa.dump
```
یا خروجی به صورت متن SQL ساده:
```bash
pg_dump -U postgres -h localhost -d yara_staging > yara_staging_backup.sql
```

### بازگردانی نسخه پشتیبان (Rollback via pg_restore / psql)
در صورت بروز خطا یا نیاز به پاکسازی وضعیت آزمایشگاه:
```bash
# بستن اتصالات فعال و بازگردانی تمیز
pg_restore -U postgres -h localhost -d yara_staging --clean --if-exists -v yara_staging_pre_qa.dump
```
یا در صورت استفاده از فایل SQL:
```bash
psql -U postgres -h localhost -d yara_staging < yara_staging_backup.sql
```

---

## ۸. وضعیت‌های مسدود و کارهای شروع‌نشده (Explicit BLOCKED Statuses)

بخش‌های زیر **تعمداً در این فاز پیاده‌سازی نشده‌اند** و تا زمان اتخاذ تصمیم قطعی در مورد زیرساخت میزبانی در وضعیت **BLOCKED** هستند:

1. **HTTPS عمومی و مدیریت گواهینامه TLS:**
   - وضعیت: **BLOCKED / Not Started**.
   - دلیل: انتخاب وب‌سرور نهایی و Reverse Proxy (Caddy / Nginx / Traefik / Cloudflare) وابسته به انتخاب ارائه‌دهنده میزبانی نهایی است. در این فاز تست‌ها بر روی شبکه محلی امن (LAN / Dedicated Host) انجام می‌شوند.
2. **دامنه خارجی و تنظیمات Public DNS:**
   - وضعیت: **BLOCKED / Not Started**.
   - دلیل: نام دامنه و رکوردهای DNS عمومی نیازمند تصمیم‌گیری تیم محصول در مورد استراتژی زیرساخت و آدرس‌دهی سرورهای عملیاتی است.
3. **دیپلوی محیط Production:**
   - وضعیت: **BLOCKED / Not Started**.
   - دلیل: کارهای دیپلوی Production، مانیتورینگ سراسری (Observability) و پایپ‌لاین‌های CI/CD در فازهای بعدی نقشه راه (از جمله T8) زمان‌بندی شده‌اند.

---

## ۹. موارد باز و مستلزم بررسی فنی (Known Open Items)

- **خطای وابستگی دامنه‌ای (Scheduling → Workflow Import Violation):**
  - شرح: در سورس ماژول `domains.scheduling.services.occurrences` و `schedules`، ایمپورت مستقیم از `domains.workflow` وجود دارد که ناقض قراردادهای معماری تفکیک دامنه‌ها است.
  - این مورد علت شکست ۳ تست موجود در سوئیت معماری است:
    - `tests/architecture/test_import_linter.py`
    - `tests/architecture/test_scheduling.py`
    - `tests/architecture/test_workflow.py`
  - تصمیم: این مورد قبل از اسپرینت C3 نیازمند یک بررسی کالبدشکافی (Forensic Audit) و ریفکتورینگ معماری خواهد بود و در این اسپرینت زیرساختی تعمداً دست نخورده باقی مانده است.

---

## ۱۰. چک‌لیست اعتبارسنجی تطابق سند با کد واقعی (Agent Verification Checklist)

| مورد ادعا | کد منبع متناظر | وضعیت تطابق با کد واقعی |
| :--- | :--- | :---: |
| اعتبارسنجی نام دیتابیس `yara_staging` در استارتاپ | [backend/common/guards.py](file:///c:/yara-care-os/backend/common/guards.py) و [backend/common/apps.py](file:///c:/yara-care-os/backend/common/apps.py) | ✅ تطابق ۱۰۰٪ |
| مسدود بودن فرامین ۵‌گانه در پروداکشن | دکوراتورهای `@ensure_not_production` در `integration/management/commands/` | ✅ تطابق ۱۰۰٪ |
| پروب `/health/live/` بدون کوئری دیتابیس | [backend/integration/api/views.py](file:///c:/yara-care-os/backend/integration/api/views.py) (`ProcessLivenessView`) | ✅ تطابق ۱۰۰٪ |
| پروب `/health/ready/` با استفاده از `MigrationExecutor` | [backend/integration/health.py](file:///c:/yara-care-os/backend/integration/health.py) (`check_migrations`) | ✅ تطابق ۱۰۰٪ |
| عدم نیاز به احراز هویت در اندپوینت‌های سلامت | `authentication_classes = []`, `permission_classes = []` در هر سه کلاس ویو | ✅ تطابق ۱۰۰٪ |
| ایزوله بودن فایل‌های واقعی در `.gitignore` | [.gitignore](file:///c:/yara-care-os/.gitignore) و [apps/hub/.gitignore](file:///c:/yara-care-os/apps/hub/.gitignore) | ✅ تطابق ۱۰۰٪ |
| عدم وجود secret واقعی در فایل‌های `.example` | [apps/hub/local.properties.staging.example](file:///c:/yara-care-os/apps/hub/local.properties.staging.example) و [apps/family/.env.staging.example](file:///c:/yara-care-os/apps/family/.env.staging.example) | ✅ تطابق ۱۰۰٪ |
| وضعیت تست‌های معماری و ۳ خطای شناخته‌شده | اجرای `pytest` (۴۹۹ پاس‌شده، ۳ خطای شناخته‌شده موروثی) | ✅ تطابق ۱۰۰٪ |
