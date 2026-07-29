# Yara — Licensing Domain Contract

**Domain:** Licensing  
**Classification:** Supporting Domain  
**Status:** Draft for Review  
**Version:** 1.0

---

## 1. Purpose

Licensing مسئول تعیین **حق استفاده از قابلیت‌ها و منابع Yara** بر اساس محصول یا پلن فعال مشتری است.

این Domain پاسخ می‌دهد:

> این Elder/اشتراک در حال حاضر اجازه استفاده از چه قابلیت‌هایی و با چه محدودیت‌هایی را دارد؟

مثلاً:

- حداکثر چند Caregiver می‌تواند متصل باشد؟
- چند Hub مجاز است؟
- آیا PillBox پشتیبانی می‌شود؟
- آیا Video Call فعال است؟
- آیا قابلیت خاصی در این پلن وجود دارد؟

اصل بنیادی:

> **Licensing decides entitlement; other domains enforce their own operations.**

Licensing مالک پرداخت یا هویت کاربران نیست.

---

# 2. Ubiquitous Language

## Plan

تعریف تجاری یک سطح از سرویس Yara.

مثلاً:

- Basic
- Plus
- Premium

Plan مشخص می‌کند چه Entitlementهایی ارائه می‌شوند.

---

## License

مجوز فعال استفاده از Yara برای یک Elder/محیط مراقبتی.

License نقطه اتصال Plan به استفاده واقعی از محصول است.

یک License می‌تواند در طول زمان Plan متفاوتی داشته باشد، اما Identity پایدار خود را حفظ می‌کند.

---

## Entitlement

یک حق یا محدودیت قابل بررسی که توسط Plan فراهم می‌شود.

دو نوع اصلی:

### Feature Entitlement

فعال/غیرفعال بودن قابلیت.

مثلاً:

`VIDEO_CALL = enabled`

### Limit Entitlement

محدودیت مقداری.

مثلاً:

`MAX_CAREGIVERS = 5`

`MAX_HUBS = 1`

---

## License Status

وضعیت قابل استفاده بودن License.

حداقل:

- ACTIVE
- SUSPENDED
- EXPIRED
- REVOKED

---

## Subscription

رابطه زمانی/تجاری‌ای که باعث فعال ماندن یک License یا Plan می‌شود.

Subscription با License یکی نیست.

License پاسخ می‌دهد:

> چه چیزی مجاز است؟

Subscription پاسخ می‌دهد:

> این دسترسی برای چه دوره‌ای فعال است؟

جزئیات مالی متعلق به Billing است.

---

# 3. Aggregates

## License — Aggregate Root

نماینده مجوز استفاده از Yara.

حداقل شامل:

- license_id
- elder_id
- current_plan_id
- status
- valid_from
- valid_until

License باید مستقل از Device خاص باشد.

تعویض Hub نباید License سالمند را از بین ببرد.

---

## Plan — Aggregate Root

تعریف یک پلن تجاری.

Plan مجموعه‌ای از Entitlementها را ارائه می‌کند.

مثلاً:

`Plan Plus`
- MAX_CAREGIVERS = 5
- MAX_HUBS = 1
- PILLBOX = enabled
- VIDEO_CALL = enabled

---

## Entitlement

تعریف یک قابلیت یا محدودیت قابل بررسی.

Entitlement باید با یک Key پایدار شناخته شود تا Domainهای دیگر به نام تجاری Plan وابسته نشوند.

مثلاً Domain نباید بپرسد:

`IsPlanPremium?`

بلکه:

`HasEntitlement(VIDEO_CALL)`

---

# 4. Entitlement Model

Domainهای دیگر نباید Plan Name را تفسیر کنند.

غلط:

`if plan == PREMIUM`

درست:

`CanUse(VIDEO_CALL)`

یا:

`GetLimit(MAX_CAREGIVERS)`

این طراحی اجازه می‌دهد Planها بدون تغییر Care، Device یا Identity بازطراحی شوند.

---

# 5. Public Interface

## Commands

- `CreatePlan`
- `UpdatePlan`
- `ActivateLicense`
- `ChangeLicensePlan`
- `SuspendLicense`
- `ResumeLicense`
- `ExpireLicense`
- `RevokeLicense`

## Queries

- `GetLicense`
- `GetActiveLicenseForElder`
- `GetPlan`
- `HasEntitlement`
- `GetEntitlement`
- `GetLimit`
- `CanUseFeature`

---

# 6. Published Events

- `LicenseActivated`
- `LicenseSuspended`
- `LicenseResumed`
- `LicenseExpired`
- `LicenseRevoked`
- `LicensePlanChanged`
- `PlanUpdated`

Domainهای مصرف‌کننده می‌توانند در صورت تغییر Entitlement واکنش نشان دهند.

---

# 7. Caregiver Limits

Identity & Access اجازه می‌دهد یک Elder Membershipهای متعدد داشته باشد.

Licensing محدودیت تجاری را تعیین می‌کند.

مثلاً:

`MAX_CAREGIVERS = 2`

Flow:

`Create/Activate Membership`
↓
`Check MAX_CAREGIVERS`
↓
`Current Active Caregivers < Limit`
↓
`Allow`

در Plan دیگر:

`MAX_CAREGIVERS = 5`

هیچ تغییری در Identity Schema لازم نیست.

---

# 8. Device Limits

همین الگو برای Device استفاده می‌شود.

مثلاً:

- MAX_HUBS = 1
- MAX_PILLBOXES = 1
- SENSOR_SUPPORT = enabled

Device Domain مالک DeviceAssignment است.

Licensing فقط مشخص می‌کند Assignment جدید از نظر تجاری مجاز هست یا خیر.

---

# 9. Rental Model

اجاره کوتاه‌مدت نباید License Model جداگانه‌ای ایجاد کند.

License می‌تواند دارای اعتبار محدود باشد:

`valid_from → valid_until`

DeviceAssignment نیز مستقل مشخص می‌کند:

`assignment_type = RENTED`

بنابراین:

- Device → حقیقت تخصیص فیزیکی
- Licensing → حق استفاده
- Billing → هزینه و پرداخت

از یکدیگر جدا باقی می‌مانند.

---

# 10. Subscription Boundary

Subscription و License نباید یکی شوند.

مثلاً ممکن است:

- پرداخت انجام شده باشد ولی License هنوز Provision نشده باشد.
- Subscription تمام شود ولی Grace Period وجود داشته باشد.
- License توسط پشتیبانی موقتاً Suspend شود.
- Device تعویض شود ولی License ثابت بماند.

بنابراین Lifecycle آن‌ها مستقل است.

---

# 11. Invariants

1. هر License باید به یک Elder معتبر مرتبط باشد.

2. هر License باید Plan معتبر داشته باشد.

3. License غیرACTIVE اجازه استفاده از Entitlementهای نیازمند License فعال را نمی‌دهد.

4. Domainهای دیگر نباید Plan Name را برای Authorization تجاری بررسی کنند.

5. Entitlement Key باید پایدار و یکتا باشد.

6. Limit Entitlement نباید مقدار منفی داشته باشد.

7. تغییر Plan نباید تاریخچه License را نابود کند.

8. تعویض Device نباید باعث ایجاد License جدید شود.

9. Expiration باید بدون حذف تاریخچه License انجام شود.

10. Licensing وضعیت Payment را به‌عنوان حقیقت مالی مدیریت نمی‌کند.

---

# 12. Boundaries

## Licensing owns

- Plan
- License
- Entitlement
- Feature availability
- Resource limits
- License lifecycle
- Commercial access rules

## Licensing does NOT own

- User identity
- Membership
- Device
- DeviceAssignment
- Care
- Payment
- Invoice
- Payment Gateway
- Notification delivery
- Workflow
- Subscription billing transaction

---

# 13. Dependencies

| Domain | Relationship |
|---|---|
| Identity & Access | بررسی limits و feature entitlement |
| Device | بررسی entitlement تجهیزات |
| Communication | بررسی قابلیت‌هایی مانند Video Call |
| Care | بررسی قابلیت‌های Care در صورت نیاز |
| Billing | دریافت وضعیت تجاری لازم برای فعال/تمدید License |
| Event | انتشار تغییرات License |

---

# 14. Billing Boundary

Billing پاسخ می‌دهد:

> چه مبلغی، برای چه چیزی و آیا پرداخت شده است؟

Licensing پاسخ می‌دهد:

> اکنون چه استفاده‌ای مجاز است؟

مثلاً:

`PaymentSucceeded`
↓
`Subscription Renewed`
↓
`License Validity Extended`

اما Licensing خودش Payment Transaction ایجاد نمی‌کند.

---

# 15. Future Compatibility

مدل Licensing نباید فرض کند:

> یک Elder همیشه فقط یک مدل خرید دائمی دارد.

باید بدون بازطراحی بنیادی امکان پشتیبانی از موارد زیر را داشته باشد:

- خرید دستگاه + اشتراک
- اجاره کوتاه‌مدت
- Trial
- Promotional access
- Device replacement
- پلن‌های جدید
- Add-onهای آینده

اما این مدل‌های تجاری تا زمانی که Use Case واقعی ندارند به Entityهای جداگانه تبدیل نمی‌شوند.

---

# 16. Architectural Decisions

1. License و Subscription دو مفهوم مستقل هستند.

2. Plan مجموعه‌ای از Entitlementها است.

3. Domainهای دیگر Plan Name را نمی‌شناسند.

4. Feature و Limit از طریق Entitlement بررسی می‌شوند.

5. محدودیت تعداد Caregiver متعلق به Licensing است، نه Identity.

6. محدودیت Device متعلق به Licensing است، نه Device Domain.

7. License به Elder/محیط مراقبتی متصل است، نه Hub خاص.

8. تعویض Hub License را تغییر نمی‌دهد.

9. مدل اجاره با License محدود زمانی + DeviceAssignment نوع RENTED قابل پشتیبانی است.

10. Billing و Licensing مستقل باقی می‌مانند.

11. Add-on، Trial و مدل‌های تجاری پیچیده تا زمان وجود Use Case واقعی وارد Schema نمی‌شوند.

---

# Final Principle

> **Identity determines who has access.  
> Licensing determines what the customer is entitled to use.  
> Device represents what hardware is assigned.  
> Billing determines what has been purchased and paid for.**