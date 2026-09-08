# Yara — Billing Domain Contract

**Domain:** Billing  
**Classification:** Supporting Domain  
**Status:** Frozen  
**Version:** 1.0  
**Related ADR:** ADR-016  

---

## 1. Purpose

دامنه Billing مسئول ثبت و مدیریت **حقایق مالی، صورتحساب‌ها، سوابق پرداخت و قیمت‌گذاری تجاری** در اکوسیستم Yara است.

این Domain پاسخ می‌دهد:
> چه صورتحسابی برای چه کسی (Caregiver) و در ازای کدام سالمند صادر شده، چه مبلغی باید پرداخت شود، وضعیت تراکنش بانکی چیست و آیا وجه وصول شده است؟

اصل بنیادی:
> **Billing determines what has been charged and paid; Licensing determines what access is granted; Infrastructure executes payment transports.**

Billing به هیچ عنوان منطق ارزیابی دسترسی‌ها، فیچرها، یا کدهای SDK بانک‌ها را در خود جای نمی‌دهد.

---

## 2. Ubiquitous Language

### Invoice (صورتحساب)
سند قطعی بار مالی صادرشده برای یک مراقب (`payer_user_id`) جهت پوشش خدمات یک سالمند (`elder_id`).
شامل شناسه فاکتور، جمع کل، واحد پول، تاریخ صدور، مهلت پرداخت و وضعیت مالی (`DRAFT`, `UNPAID`, `PAID`, `VOID`, `REFUNDED`).

### InvoiceLineItem (ردیف صورتحساب)
تفکیک اقلام مندرج در صورتحساب (حق اشتراک پلن، ودیعه یا اجاره تجهیزات، تخفیف).

### PaymentAttempt (تلاش پرداخت)
لاگ غیرقابل تغییر از هر تلاش برای پرداخت صورتحساب از طریق درگاه پرداخت. شامل شناسه یکتای مرجع درگاه (`authority` یا `payment_intent_id`)، کلید Idempotency، مبلغ، ارائه‌دهنده و وضعیت تلاش (`INITIATED`, `REDIRECTED`, `SUCCESSFUL`, `FAILED`, `CANCELLED`).

### PlanPrice (قیمت تجاری پلن)
تعریف قیمت و دوره صورتحساب برای یک پلن (مثلاً ماهانه یا سالانه با ارز ریال/تومان). کاملاً مجزا از مدل فنی `Plan` در دامنه Licensing.

---

## 3. Aggregates

### Invoice — Aggregate Root
- `id`: UUID
- `invoice_number`: شناسه خوانا و یکتای حسابداری
- `elder_id`: UUID خام (عدم وجود Foreign Key مستقیم به دامنه Identity)
- `payer_user_id`: UUID خام کاربر پرداخت‌کننده
- `subscription_id`: UUID خام اشتراک مرتبط (اختیاری)
- `total_amount`: مبلغ کل فاکتور
- `currency`: واحد پول (`IRR`, `TOMAN`)
- `status`: `InvoiceStatus`
- `due_date`: مهلت پرداخت
- `paid_at`: زمان قطعی پرداخت
- `created_at`: زمان صدور

### PaymentAttempt — Entity
- `id`: UUID
- `invoice_id`: ForeignKey به Invoice
- `provider`: نام ارائه‌دهنده (`FAKE`, `ZARINPAL`, `STRIPE`)
- `provider_reference`: شناسه درگاه (Authority / Token)
- `idempotency_key`: کلید جلوگیری از تکرار
- `amount`: مبلغ تراکنش
- `status`: `PaymentAttemptStatus`
- `created_at`: تاریخ ایجاد

### PlanPrice — Aggregate
- `id`: UUID
- `plan_code`: کد متناظر پلن در Licensing (`BASIC`, `PLUS`, `PREMIUM`)
- `interval`: بازه زمانی (`MONTHLY`, `ANNUAL`)
- `amount`: مبلغ
- `currency`: واحد پول
- `is_active`: وضعیت فعال بودن فروش

---

## 4. Invariants

1. صورتحساب با وضعیت `PAID` هرگز مجدداً پرداخت یا ویرایش نمی‌شود.
2. اعتبارسنجی تراکنش‌های درگاه پرداخت باید ۱۰۰٪ Idempotent باشد؛ فراخوانی مجدد Callback با یک Authority قبلاً پردازش‌شده، نباید وضعیت مضاعف ایجاد کند.
3. دامنه‌ی Billing هیچ ارتباط و کلاسی از SDKهای درگاه‌های پرداخت (مثل ZarinPal یا Stripe) وارد نمی‌کند؛ تعامل با درگاه منحصراً از طریق پورت `PaymentProvider` در `backend/infrastructure/payment/` صورت می‌پذیرد.
4. مبالغ مالی نمی‌توانند منفی باشند.
5. ارجاع به دامنه‌های دیگر (`Elder`, `User`, `Subscription`) منحصراً از طریق UUID خام صورت می‌گیرد، نه Foreign Key مستقیم دیتابیسی (Cross-Domain Loose Coupling).

---

## 5. Boundaries

### Billing owns:
- فاکتورها (`Invoice`, `InvoiceLineItem`)
- قیمت‌گذاری تجاری (`PlanPrice`)
- ثبت رکوردهای تلاش پرداخت (`PaymentAttempt`)
- صدور رسیدهای مالی و وضعیت تسویه

### Billing does NOT own:
- حقوق دسترسی، سقف‌ها و قابلیت‌ها (متعلق به `Licensing`)
- دوره‌های زمانی لایسنس و اشتراک (متعلق به `Licensing`)
- هویت مراقب و سالمند (متعلق به `Identity & Access`)
- تجهیزات و تخصیص سخت‌افزار (متعلق به `Device`)
- کد درگاه‌های پرداخت و اتصالات HTTP (متعلق به `Infrastructure/Payment`)

---

## 6. Integration & ADR-016 Compliance

- **استثنای هماهنگی همگام (Synchronous Exception):** به هنگام تایید پرداخت در Callback، جهت حفظ تجربه کاربری اپلیکیشن و سرعت عمل، هماهنگ‌کننده اپلیکیشن بلافاصله پس از تسویه فاکتور، سرویس فعال‌سازی اشتراک در Licensing را فراخوانی می‌کند.
- **انتشار رویداد (Event Duality):** به موازات فراخوانی مستقیم، رویداد رسمی `PaymentSucceeded` در Event Domain منتشر می‌شود تا فرآیندهای پس‌زمینه (حسابرسی، هشدارهای درون‌برنامه‌ای، پیامک) را تغذیه کند.
