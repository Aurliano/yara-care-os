**Domain:** Identity & Access
**Classification:** Supporting Domain
**Status:** Frozen
**Version:** 1.1
---

## 1. Purpose

Identity & Access مسئول هویت کاربران، ارتباط آن‌ها با سالمند و کنترل دسترسی به منابع Yara است.

این Domain پاسخ می‌دهد:

> چه کسی وارد سیستم شده، به کدام Elder دسترسی دارد و چه عملیاتی مجاز است انجام دهد؟

اصل بنیادی:

> **Identity establishes who you are; Access determines what you may do.**

این Domain مالک Care، Device، Licensing یا Billing نیست.

---

# 2. Ubiquitous Language

## User

یک شخص دارای حساب کاربری در Yara.

User می‌تواند نسبت به Elderهای مختلف نقش‌ها و دسترسی‌های متفاوت داشته باشد.

---

## Elder

شخصی که خدمات Yara برای او ارائه می‌شود.

Elder لزوماً User نیست و برای استفاده از Hub نیازی به حساب کاربری مستقل ندارد.

---

## Membership

رابطه بین User و Elder.

مثلاً:

`Ali → Mother`

Membership مشخص می‌کند User به Context آن Elder دسترسی دارد.

یک Elder می‌تواند تعداد زیادی Membership داشته باشد.

---

## Role

مجموعه‌ای نام‌گذاری‌شده از Permissionها.

نمونه:

- PRIMARY_CAREGIVER
- CAREGIVER
- VIEWER

Role ابزار مدیریت Permissionها است، نه جایگزین آن‌ها.

---

## Permission

مجوز انجام یک Operation مشخص.

مثلاً:

- VIEW_ELDER_STATUS
- MANAGE_MEDICATION
- MANAGE_CONTACTS
- MANAGE_DEVICES
- INITIATE_CALL
- MANAGE_MEMBERS
- MANAGE_SUBSCRIPTION

Business Domain می‌تواند Permission موردنیاز را درخواست کند، اما تعریف و ارزیابی Access متعلق به Identity & Access است.

---

## Invitation

دعوت یک User برای دسترسی به Elder.

Invitation می‌تواند از طریق:

- Invite Code
- Link
- QR Code

ارائه شود.

دعوت تا زمان Accept شدن به معنی Membership فعال نیست.

---

## Emergency Recipient

Membership/Userای که برای دریافت هشدارهای مهم Elder انتخاب شده است.

این مفهوم فقط مشخص می‌کند **چه کسی مقصد مجاز هشدار است**.

تصمیم اینکه چه زمانی هشدار ارسال شود متعلق به Workflow و نحوه ارسال متعلق به Notification است.

---

# 3. Aggregates

## User — Aggregate Root

مالک هویت حساب کاربری.

مسئول:

- account identity
- profile
- account status

است.

Credential و Authentication mechanism می‌تواند توسط Infrastructure/Auth Provider مدیریت شود.

---

## Elder — Aggregate Root

هویت سالمند در Yara.

Elder مستقل از User است.

این جداسازی اجازه می‌دهد سالمند بدون Login یا Smartphone از Hub استفاده کند.

---

## Membership — Aggregate Root

رابطه دسترسی User به Elder.

حداقل شامل:

- user_id
- elder_id
- role
- status
- joined_at

Status پایه:

- INVITED
- ACTIVE
- SUSPENDED
- REVOKED

Membership محل اصلی اعمال Role و Permissionهای وابسته به Elder است.

---

## Invitation — Aggregate Root

دعوت برای ایجاد Membership.

هر Invitation علاوه بر Elder و دعوت‌کننده، Role موردنظر برای Membership آینده را مشخص می‌کند.

حداقل شامل:

- elder_id
- invited_by_user_id
- role_id
- invite_code
- status
- expires_at
- accepted_at

Lifecycle پایه:

`PENDING → ACCEPTED`

Terminal States:

- EXPIRED
- REVOKED

قواعد:

- Invitation باید قابل انقضا باشد.
- Invitation باید قابل لغو باشد.
- Invitation Single-use است.
- فقط Invitation با وضعیت PENDING قابل Accept است.
- Accept موفق، Membership را با همان `role_id` تعریف‌شده در Invitation ایجاد می‌کند.
- Accept کردن Invitation نباید Role را به‌صورت implicit یا default انتخاب کند.
- اگر یک PENDING Invitation پس از `expires_at` مورد ارزیابی قرار گیرد، ابتدا وضعیت آن به EXPIRED منتقل و persist می‌شود و سپس عملیات درخواست‌شده رد می‌شود.
- EXPIRED یک وضعیت terminal و persisted است.

# 4. Access Model

مدل اولیه Yara:

`User → Membership → Elder → Role → Permissions`

مثلاً:

`Ali`
↓
`Membership(Mother)`
↓
`PRIMARY_CAREGIVER`
↓
`MANAGE_MEDICATION`

همان User ممکن است برای Elder دیگری فقط:

`VIEWER`

باشد.

بنابراین Role به User به‌صورت Global متصل نمی‌شود؛ در Context Membership معنا دارد.

---

# 5. Roles & Permissions

Roleهای MVP محدود باقی می‌مانند.

### PRIMARY_CAREGIVER

دسترسی مدیریتی اصلی Elder.

### CAREGIVER

دسترسی مراقبتی معمولی بر اساس Permissionهای تعریف‌شده.

### VIEWER

دسترسی عمدتاً مشاهده‌ای.

Permission باید معیار نهایی Authorization باشد.

کد Domainها نباید منطق‌هایی مانند:

`if role == PRIMARY_CAREGIVER`

را در سراسر سیستم Hard-code کند.

به‌جای آن:

`Can(user, MANAGE_MEDICATION, elder)`

بررسی می‌شود.

---

# 6. Multi-Caregiver Model

یک Elder می‌تواند Membershipهای متعدد داشته باشد.

مثلاً:

`Elder`
├── Daughter
├── Son
├── Grandchild
└── Caregiver

Identity & Access تعداد Caregiverهای مجاز توسط Plan را تعیین نمی‌کند.

Licensing تعیین می‌کند:

> این License حداکثر چند Membership فعال از نوع موردنظر اجازه می‌دهد؟

Identity فقط Membership را مدیریت می‌کند و هنگام ایجاد/فعال‌سازی می‌تواند Entitlement را از Licensing بررسی کند.

---

# 7. Public Interface

## Commands

- `CreateUser`
- `CreateElder`
- `UpdateUserProfile`
- `UpdateElderProfile`
- `CreateInvitation`
- `AcceptInvitation`
- `RevokeInvitation`
- `ChangeMembershipRole`
- `SuspendMembership`
- `RevokeMembership`
- `ConfigureEmergencyRecipients`

## Queries

- `GetUser`
- `GetElder`
- `GetUserElders`
- `GetElderMembers`
- `GetMembership`
- `GetPermissions`
- `Can`
- `GetEmergencyRecipients`

---

# 8. Published Events

- `UserCreated`
- `ElderCreated`
- `MembershipCreated`
- `MembershipActivated`
- `MembershipRoleChanged`
- `MembershipSuspended`
- `MembershipRevoked`
- `InvitationCreated`
- `InvitationAccepted`
- `InvitationExpired`
- `EmergencyRecipientsChanged`

---

# 9. Authentication vs Authorization

Authentication پاسخ می‌دهد:

> این شخص کیست؟

Authorization پاسخ می‌دهد:

> این شخص اجازه انجام این Operation را دارد؟

Identity & Access مدل هویت و Access Policy را مالک است، اما لازم نیست سیستم Authentication اختصاصی پیچیده‌ای بسازیم.

در MVP می‌توان Authentication را با مکانیزم استاندارد Backend پیاده کرد و Domain Contract را به Provider خاصی وابسته نکرد.

---

# 10. Invariants

1. هر Membership دقیقاً یک User و یک Elder دارد.

2. یک User نباید برای یک Elder Membership فعال تکراری داشته باشد.

3. Membership لغوشده اجازه دسترسی ندارد.

4. Role فقط در Context Membership معنا دارد.

5. Permission معیار نهایی Authorization است.

6. Invitation منقضی یا Revoked قابل Accept نیست.

7. Invitation Single-use است.

8. Accept Invitation نباید Membership تکراری ایجاد کند.

9. Elder برای استفاده از Yara مجبور به داشتن User Account نیست.

10. حذف User نباید Audit و تاریخچه عملیاتی گذشته را نابود کند.

11. حداقل یک مسیر مدیریتی معتبر برای Elder باید باقی بماند؛ عملیات حذف/لغو دسترسی نباید Elder را ناخواسته بدون مدیریت رها کند.

12. هر Invitation دقیقاً یک Role برای Membership آینده مشخص می‌کند.

13. Membership ایجادشده از Invitation باید Role همان Invitation را دریافت کند.

14. AcceptInvitation نباید Role پیش‌فرض مانند VIEWER را به‌صورت implicit انتخاب کند.

15. PENDING Invitation که از expires_at عبور کرده است، هنگام ارزیابی باید به EXPIRED منتقل و persist شود.

16. EXPIRED و REVOKED terminal هستند و قابل Accept نیستند.

---

# 11. Emergency Access

مقصدهای اضطراری می‌توانند از میان Membershipهای معتبر Elder انتخاب شوند.

مثلاً:

`Mother`
├── Daughter — Emergency
├── Son — Emergency
└── Grandchild

Identity مشخص می‌کند چه کسانی انتخاب شده‌اند.

Workflow مشخص می‌کند چه زمانی Escalation لازم است.

Notification مشخص می‌کند هشدار چگونه ارسال شود.

بنابراین Identity پیامک یا Push ارسال نمی‌کند.

---

# 12. Boundaries

## Identity & Access owns

- User
- Elder identity
- Membership
- Role
- Permission
- Invitation
- Access Policy
- Emergency Recipient configuration

## Identity & Access does NOT own

- Care Plan
- Medication
- Device Assignment
- Workflow
- Notification delivery
- Subscription limits
- Payment
- Call Session
- Hub pairing
- Authentication transport/protocol

---

# 13. Dependencies

| Domain | Relationship |
|---|---|
| Care | Authorization + User/Elder references |
| Communication | Authorization + participant references |
| Device | Authorization + Elder/Actor references |
| Licensing | Entitlement validation |
| Notification | Recipient references |
| Event | Publish identity/access events |
| Audit | Actor identity |

---

# 14. Licensing Boundary

این Domain نباید قوانینی مانند:

- Plan A = دو Caregiver
- Plan B = پنج Caregiver
- Video Call فقط در Premium

را بداند.

این قوانین متعلق به Licensing هستند.

Flow نمونه:

`Invite Caregiver`
↓
`Identity validates access`
↓
`Licensing validates entitlement`
↓
`Membership activated`

در نتیجه تغییر Plan نیازی به تغییر Identity Model ندارد.

---

# 15. Future Roles

مدل باید در آینده بتواند Roleهای جدیدی مانند:

- DOCTOR
- NURSE
- ORGANIZATION_ADMIN

را بدون بازطراحی Membership پشتیبانی کند.

اما این Roleها و Organization Domain تا زمانی که Use Case واقعی وارد محصول نشده، پیاده‌سازی نمی‌شوند.

---

# 16. Architectural Decisions

1. User و Elder موجودیت‌های مستقل هستند.

2. Elder برای استفاده از Hub نیاز به User Account ندارد.

3. دسترسی User به Elder از طریق Membership مدل می‌شود.

4. تعداد Membershipهای یک Elder ذاتاً محدود نیست.

5. محدودیت تجاری تعداد Caregiver متعلق به Licensing است.

6. Role در Context Membership تعریف می‌شود، نه User.

7. Permission معیار نهایی Authorization است.

8. Roleهای MVP محدود باقی می‌مانند.

9. Invitation مکانیزم اصلی اتصال User جدید به Elder است.

10. Invitation باید Expirable، Revocable و Single-use باشد.

11. Emergency Recipient فقط مقصد هشدار را مشخص می‌کند؛ ارسال هشدار خارج از این Domain است.

12. Organization و نقش‌های سازمانی فعلاً وارد Schema نمی‌شوند.

---

# Final Principle

> **User identifies the person.  
> Membership establishes the relationship.  
> Role groups permissions.  
> Permission decides access.  
> Licensing decides commercial entitlement.**