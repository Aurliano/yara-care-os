# Yara — Scheduling Domain Contract

**Domain:** Scheduling  
**Classification:** Supporting Domain  
**Status:** Frozen  
**Version:** 1.1

---

## 1. Purpose

Scheduling مسئول تعریف و محاسبه زمان وقوع کارهای برنامه‌ریزی‌شده در Yara است.

این Domain پاسخ می‌دهد:

> چه چیزی و چه زمانی باید آماده اجرا شود؟

Scheduling تصمیم نمی‌گیرد پس از رسیدن آن زمان چه اتفاقی بیفتد.

اصل بنیادی:

> **Scheduling decides when; Workflow decides what happens next.**

مثلاً Scheduling می‌گوید:

`OccurrenceDue at 08:00`

اما نمی‌گوید:

`ShowMedicationReminder`

یا:

`OpenCompartment`

این تصمیم‌ها متعلق به Workflow هستند.

---

# 2. Ubiquitous Language

## Schedule Definition

تعریف یک برنامه زمانی.

مثلاً:

- هر روز ساعت 08:00
- شنبه و چهارشنبه ساعت 18:00
- یک تاریخ مشخص ساعت 15:00
- هر 8 ساعت

ScheduleDefinition مستقل از معنای Care است.

---

## Occurrence

یک وقوع مشخص از ScheduleDefinition در یک زمان معین.

مثلاً:

Schedule:

`Every day at 08:00`

Occurrence:

`2026-07-26 08:00`

Occurrence واحدی است که در زمان مقرر آماده اجرای Workflow می‌شود.

---

## Recurrence Rule

قانون تکرار Schedule.

Scheduling تنها مالک تفسیر و محاسبه Recurrence است.

Domainهای دیگر نباید RRULE یا منطق recurrence را مستقلاً Parse یا Evaluate کنند.

---

## Time Zone

منطقه زمانی‌ای که Schedule بر اساس آن تعریف شده است.

Schedule باید معنای محلی زمان را حفظ کند.

---

## Schedule Exception

تغییری محدود روی یک Occurrence بدون تغییر تعریف اصلی Schedule.

مثلاً:

- Skip یک Occurrence
- تغییر زمان یک وقوع خاص
- لغو یک Occurrence آینده

---

# 3. Aggregates

## ScheduleDefinition — Aggregate Root

تعریف برنامه زمانی.

حداقل شامل:

- owner_reference
- recurrence_definition
- timezone
- start_at
- end_at
- status

Status پایه:

- ACTIVE
- PAUSED
- ENDED
- CANCELLED

Scheduling معنای `owner_reference` را تفسیر نمی‌کند.

---

## Occurrence — Aggregate Root

نماینده یک وقوع مشخص و قابل ردیابی از Schedule.

حداقل شامل:

- schedule_definition_id
- scheduled_for
- status

Status پایه:

- SCHEDULED
- DUE
- CANCELLED
- SKIPPED

Occurrence وضعیت اجرای Workflow را نگه نمی‌دارد.

---

# 4. Scheduling Flow

Flow پایه:

`ScheduleDefinition`
↓
`Calculate Occurrence`
↓
`Occurrence`
↓
`OccurrenceDue`
↓
`Workflow`

مثلاً Care می‌تواند Schedule لازم را تعریف کند.

Scheduling زمان وقوع را محاسبه می‌کند.

در زمان مقرر:

`OccurrenceDue`

منتشر می‌شود و Workflow تصمیم می‌گیرد چه فرآیندی اجرا شود.

---

# 5. Public Interface

## Commands

- `CreateSchedule`
- `UpdateSchedule`
- `PauseSchedule`
- `ResumeSchedule`
- `CancelSchedule`
- `AddScheduleException`
- `CancelOccurrence`
- `SkipOccurrence`

## Queries

- `GetSchedule`
- `GetNextOccurrence`
- `GetUpcomingOccurrences`
- `GetOccurrencesBetween`
- `GetOccurrence`

---

# 6. Published Events

- `ScheduleCreated`
- `ScheduleUpdated`
- `SchedulePaused`
- `ScheduleResumed`
- `ScheduleCancelled`
- `OccurrenceScheduled`
- `OccurrenceDue`
- `OccurrenceSkipped`
- `OccurrenceCancelled`

مهم‌ترین Contract با Workflow:

`OccurrenceDue`

Scheduling فقط اعلام می‌کند زمان وقوع رسیده است.

---

# 7. Idempotency

هر Occurrence باید Identity پایدار داشته باشد.

محاسبه مجدد Schedule، اجرای Offline یا Sync مجدد نباید برای همان وقوع منطقی Occurrence دیگری ایجاد کند.

اصل:

> **One logical occurrence = one stable identity.**

همچنین دریافت تکراری `OccurrenceDue` نباید باعث ایجاد چند WorkflowExecution برای یک Occurrence شود.

---

# 8. Time & Timezone Rules

Scheduling باید timezone-aware باشد.

قواعد پایه:

1. هر Schedule دارای timezone مشخص است.
2. زمان اجرا باید به یک instant استاندارد مانند UTC قابل تبدیل باشد.
3. معنای زمان محلی Schedule باید حفظ شود.
4. تغییر timezone نباید silently زمان اجرای Schedule را تغییر دهد.
5. اختلاف ساعت Hub و Backend نباید به Business Domainها منتقل شود.

---

# 9. Offline-First

Scheduleهای ضروری باید روی Hub بدون اتصال Backend قابل اجرا باشند.

Hub باید بتواند:

- ScheduleDefinition موردنیاز را به‌صورت محلی داشته باشد.
- Occurrenceهای لازم را محاسبه کند.
- رسیدن زمان Occurrence را تشخیص دهد.
- `OccurrenceDue` تولید کند.
- Occurrenceهای ایجادشده را بعداً Sync کند.

Backend و Hub نباید برای یک وقوع منطقی دو Occurrence مستقل ایجاد کنند.

Stable Identity و Idempotency این مسئله را کنترل می‌کنند.

---

# 10. Invariants

1. هر Occurrence دقیقاً متعلق به یک ScheduleDefinition است.

2. هر وقوع منطقی فقط یک Occurrence معتبر دارد.

3. Schedule غیرفعال نباید Occurrence جدید فعال ایجاد کند.

4. Occurrence لغوشده یا Skipشده نباید Due شود.

5. Scheduling WorkflowExecution ایجاد نمی‌کند.

6. Scheduling business meaning Schedule را نمی‌شناسد.

7. Recurrence فقط توسط Scheduling تفسیر می‌شود.

8. Schedule باید timezone مشخص داشته باشد.

9. تغییر Schedule نباید تاریخچه Occurrenceهای گذشته را بازنویسی کند.

10. Occurrenceهای گذشته باید قابل ردیابی باقی بمانند.

---

# 11. Boundaries

## Scheduling owns

- ScheduleDefinition
- Recurrence
- Timezone
- ScheduleException
- Occurrence generation
- Due-time calculation
- Occurrence lifecycle

## Scheduling does NOT own

- Medication
- CareActivity
- Reminder UI
- Confirmation
- WorkflowExecution
- Escalation
- DeviceCommand
- Notification delivery
- Sync transport

---

# 12. Dependencies

| Domain | Relationship |
|---|---|
| Care | درخواست ایجاد/تغییر Schedule و Reference |
| Workflow | انتشار `OccurrenceDue` |
| Event | انتشار Scheduling Events |
| Synchronization | انتقال Schedule/Occurrence بین Backend و Hub |
| Identity & Access | Actor reference / Authorization برای عملیات مدیریتی |

Scheduling به مدل داخلی Care وابسته نیست.

---

# 13. Care Integration

Care می‌تواند یک ScheduleDefinition را Reference کند:

`CareActivity → schedule_definition_id`

برای نمونه:

`Prescription → CareActivity → ScheduleDefinition`

اما Scheduling نمی‌داند Schedule مربوط به:

- Medication
- Exercise
- Doctor Appointment
- Daily Check-in
- یا Use Case دیگری

است.

فقط زمان را مدیریت می‌کند.

---

# 14. Domain Classification Decision

Scheduling رسماً یک **Supporting Domain مستقل** در معماری Yara است.

تصمیم قبلی که Scheduling را صرفاً یک Shared Module در نظر می‌گرفت، با این Contract جایگزین می‌شود.

دلیل این تغییر، شکل‌گیری مسئولیت‌ها و Invariantهای مستقل زیر است:

- ScheduleDefinition ownership
- Occurrence lifecycle
- Recurrence evaluation
- Timezone semantics
- Schedule exceptions
- Idempotent occurrence generation
- Offline scheduling

این جداسازی به معنی ایجاد Microservice مستقل نیست.

در MVP، Scheduling می‌تواند یک Module مستقل در همان Backend و Hub باشد.

> **Domain Boundary ≠ Deployment Boundary**

---

# 15. Architectural Decisions — Frozen

1. Scheduling یک Supporting Domain مستقل است.

2. Scheduling تنها مالک recurrence logic است.

3. Domainهای دیگر RRULE را Parse یا Evaluate نمی‌کنند.

4. ScheduleDefinition و Occurrence مفاهیم جدا هستند.

5. Occurrence ورودی Workflow است.

6. Scheduling هیچ Workflow Action اجرا نمی‌کند.

7. Occurrence دارای Identity پایدار و idempotent است.

8. Scheduling timezone-aware است.

9. Scheduleهای ضروری Offline روی Hub قابل محاسبه‌اند.

10. Backend و Hub نباید برای یک وقوع منطقی Occurrence تکراری ایجاد کنند.

11. تغییر Schedule تاریخچه Occurrenceهای گذشته را بازنویسی نمی‌کند.

12. Scheduling Domain مستقل است، اما در MVP سرویس مستقل نیست.

13. Calendar Engine عمومی، Distributed Scheduler پیچیده و Scheduling Microservice فعلاً ساخته نمی‌شوند.

---

# Final Principle

> **Care defines what is needed.  
> Scheduling determines when it becomes due.  
> Workflow determines what happens next.**