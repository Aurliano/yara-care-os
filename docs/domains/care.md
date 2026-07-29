# Yara — Care Domain Contract

**Domain:** Care  
**Classification:** Core Domain  
**Status:** Frozen  
**Version:** 1.1

---

## 1. Purpose

Care Domain مسئول تعریف و تفسیر فعالیت‌های مراقبتی سالمند در Yara است.

این Domain پاسخ می‌دهد:

> سالمند چه Care Activityای دارد، آن فعالیت چه معنایی دارد و نتیجه اجرای آن از دید Care چیست؟

Care زمان‌بندی recurrence، orchestration اجرا یا تعامل مستقیم با سخت‌افزار را انجام نمی‌دهد.

اصل بنیادی:

> **Care owns business meaning; Workflow owns execution.**

مثلاً:

Workflow اعلام می‌کند:

`ExecutionConfirmed`

Care با توجه به CareActivity مربوطه می‌تواند آن را تفسیر کند:

`MedicationTaken`

---

# 2. Ubiquitous Language

## Care Activity

تعریف یک فعالیت مراقبتی برای Elder.

نمونه:

- Medication
- Exercise
- Daily Check-in
- فعالیت‌های مراقبتی آینده

CareActivity مدل عمومی Care است و Activityهای تخصصی می‌توانند آن را Specialize کنند.

---

## Prescription

Specialization دارویی CareActivity.

Prescription مشخص می‌کند:

- چه دارویی
- با چه دستور مصرفی
- برای کدام Elder
- با چه توضیحات قابل فهم برای سالمند

باید بتوان برای سالمندانی که خواندن برایشان دشوار است اطلاعاتی مانند:

- توضیح ساده
- توضیح شخصی‌سازی‌شده
- تصویر دارو

تعریف کرد.

Media از طریق Reference به Media Domain نگهداری می‌شود.

---

## Care Completion

تفسیر Care از نتیجه یک WorkflowExecution.

مثلاً:

`ExecutionConfirmed`
↓
`Prescription context`
↓
`MedicationTaken`

Completion یک Hardware Fact یا Workflow State نیست.

---

## Confirmation Requirement

نیاز CareActivity به نحوه تأیید اجرای فعالیت.

Care می‌تواند هنگام تعریف فعالیت مشخص کند چه نوع Confirmation موردنیاز است، اما Runtime evaluation متعلق به Workflow است.

اصطلاحات رسمی Runtime:

- `ConfirmationPolicy`
- `ConfirmationEvidence`

Care از مفهوم قدیمی `ConfirmationMethod` به‌عنوان مدل Runtime استفاده نمی‌کند.

---

# 3. Aggregates

## CareActivity — Aggregate Root

Aggregate عمومی فعالیت مراقبتی.

حداقل شامل:

- elder_id
- activity_type
- status
- schedule_definition_id
- workflow_definition_id
- display information

Status پایه:

- ACTIVE
- PAUSED
- ENDED
- CANCELLED

---

## Prescription — Specialization

Prescription یک Specialization واقعی CareActivity است.

مدل:

`CareActivity`
↓
`Prescription`

برای Physical Model استفاده از Shared Primary Key مجاز و ترجیحی است.

Prescription می‌تواند شامل:

- medication reference
- dosage information
- elder-friendly description
- media reference

باشد.

---

## CareCompletion — Aggregate / Historical Record

ثبت نتیجه Care-specific یک Occurrence اجراشده.

حداقل ارتباط مفهومی:

- care_activity_id
- occurrence_id
- workflow_execution_id
- completion state
- interpreted_at

CareCompletion نتیجه را تفسیر می‌کند؛ WorkflowExecution را جایگزین نمی‌کند.

---

# 4. Care Execution Flow

Flow اصلی:

`CareActivity`
↓
`ScheduleDefinition`
↓
`Occurrence`
↓
`WorkflowExecution`
↓
`Execution Result`
↓
`Care Interpretation`

مثلاً:

`Prescription`
↓
`08:00 Occurrence`
↓
`WorkflowExecution`
↓
`ExecutionConfirmed`
↓
`MedicationTaken`

مرز مسئولیت‌ها:

`Care → What`

`Scheduling → When`

`Workflow → How execution progresses`

`Device → Physical facts/actions`

---

# 5. Scheduling Integration

Care درخواست ایجاد یا تغییر ScheduleDefinition را به Scheduling می‌دهد.

Care می‌تواند:

`schedule_definition_id`

را نگه دارد.

اما Care:

- RRULE را Parse نمی‌کند.
- Occurrence تولید نمی‌کند.
- Due Time را محاسبه نمی‌کند.

Scheduling تنها مالک recurrence logic است.

---

# 6. Workflow Integration

Care مشخص می‌کند Activity برای اجرا به چه Workflow Definition نیاز دارد.

Workflow سپس Execution را برای Occurrence مدیریت می‌کند.

Care می‌تواند Eventهایی مانند:

- `ExecutionConfirmed`
- `ExecutionMissed`
- `ExecutionCancelled`
- `ExecutionFailed`

را دریافت کند و بر اساس Context فعالیت تفسیر کند.

Workflow نباید Care-specific result تولید کند.

---

# 7. Confirmation Contract

Care ممکن است نیاز Confirmation یک Activity را هنگام تعریف آن مشخص کند.

مثلاً Prescription ممکن است نیاز داشته باشد:

- بسته‌شدن محفظه PillBox
- تأیید مستقیم سالمند روی Hub
- یا fallback تعریف‌شده دیگری

اما این نیاز به یک `ConfirmationPolicy` قابل اجرای Workflow تبدیل می‌شود.

Runtime:

`ConfirmationEvidence`
↓
`Workflow ConfirmationPolicy`
↓
`ExecutionConfirmed`
↓
`Care Interpretation`

بنابراین:

Care مالک **معنای Confirmation Requirement** است.

Workflow مالک **ConfirmationPolicy و ارزیابی ConfirmationEvidence** است.

Device فقط Fact سخت‌افزاری تولید می‌کند.

---

# 8. PillBox Integration

Care مستقیماً PillBox را کنترل نمی‌کند.

مثلاً Care می‌تواند مشخص کند Prescription به یک Compartment Assignment مرتبط است.

اما:

`Care → OPEN_COMPARTMENT`

مستقیم اجرا نمی‌شود.

Flow:

`Care Context`
↓
`Scheduling`
↓
`Workflow`
↓
`Device Action`
↓
`DeviceCommand`
↓
`PillBox`

در برگشت:

`CompartmentClosed`
↓
`Workflow Evidence`
↓
`ExecutionConfirmed`
↓
`Care`
↓
`MedicationTaken`

---

# 9. Public Interface

## Commands

- `CreateCareActivity`
- `UpdateCareActivity`
- `PauseCareActivity`
- `ResumeCareActivity`
- `EndCareActivity`
- `CreatePrescription`
- `UpdatePrescription`
- `InterpretExecutionResult`

## Queries

- `GetCareActivity`
- `GetElderCareActivities`
- `GetPrescription`
- `GetActivePrescriptions`
- `GetCareCompletionHistory`
- `GetCareActivityStatus`

---

# 10. Published Events

نمونه Eventهای Care:

- `CareActivityCreated`
- `CareActivityUpdated`
- `CareActivityPaused`
- `CareActivityResumed`
- `CareActivityEnded`
- `PrescriptionCreated`
- `PrescriptionUpdated`
- `CareActivityCompleted`
- `MedicationTaken`
- `MedicationMissed`

این Eventها business meaning دارند و به همین دلیل توسط Care منتشر می‌شوند.

Device یا Workflow نباید `MedicationTaken` تولید کنند.

---

# 11. Invariants

1. هر CareActivity متعلق به یک Elder است.

2. Prescription بدون CareActivity پایه وجود ندارد.

3. CareActivity زمان‌بندی recurrence را خودش محاسبه نمی‌کند.

4. CareActivity WorkflowExecution را خودش اجرا نمی‌کند.

5. Care Completion فقط بر اساس Execution Result معتبر و Context مربوطه ایجاد می‌شود.

6. یک نتیجه Execution تکراری نباید CareCompletion تکراری ایجاد کند.

7. تغییر CareActivity نباید تاریخچه Completionهای گذشته را بازنویسی کند.

8. Care مستقیماً Hardware Fact را به Completion تبدیل نمی‌کند؛ Confirmation ابتدا توسط Workflow ارزیابی می‌شود.

9. Care نباید DeviceCommand ایجاد یا lifecycle آن را مدیریت کند.

10. Media مربوط به Care از طریق Reference نگهداری می‌شود.

---

# 12. Boundaries

## Care owns

- CareActivity
- Prescription
- Care-specific rules
- Elder-friendly care information
- Care Completion
- Business interpretation of execution results
- Confirmation requirements در سطح Care meaning

## Care does NOT own

- Recurrence calculation
- Occurrence generation
- WorkflowExecution
- ConfirmationPolicy runtime evaluation
- ConfirmationEvidence processing
- DeviceCommand
- PillBox state
- BLE
- Notification delivery
- Synchronization transport
- Media storage

---

# 13. Dependencies

| Domain | Relationship |
|---|---|
| Identity & Access | Elder/Actor reference + Authorization |
| Scheduling | ایجاد/مدیریت ScheduleDefinition |
| Workflow | Workflow definition contract + دریافت Execution results |
| Device | Reference فقط در موارد لازم مانند Compartment Assignment؛ بدون کنترل مستقیم |
| Media | Reference برای تصویر و محتوای Care |
| Event | Publish / Consume |
| Synchronization | انتقال state موردنیاز Hub |

Care در MVP وابستگی به Licensing ندارد.

اگر در آینده یک قابلیت Care-specific به Entitlement تجاری وابسته شد، همان زمان این Dependency اضافه می‌شود.

---

# 14. Confirmation Terminology

اصطلاح `ConfirmationMethod` از مدل Runtime حذف می‌شود.

مدل رسمی:

### Care

`Confirmation Requirement`

یعنی:

> این CareActivity برای معتبر شدن اجرا چه نیازی دارد؟

### Workflow

`ConfirmationPolicy`

یعنی:

> چه Evidenceهایی و تحت چه قواعدی Execution را Confirm می‌کنند؟

### Runtime Input

`ConfirmationEvidence`

یعنی:

> چه Fact یا Interactionی برای ارزیابی دریافت شده است؟

مثال:

`Prescription`
↓
`Confirmation Requirement`
↓
`Workflow ConfirmationPolicy`
↓
`CompartmentClosed Evidence`
↓
`ExecutionConfirmed`
↓
`MedicationTaken`

---

# 15. Architectural Decisions — Frozen

1. Care مالک business meaning فعالیت‌های مراقبتی است.

2. CareActivity Aggregate عمومی Care است.

3. Prescription Specialization واقعی CareActivity است.

4. Scheduling تنها مالک recurrence و Occurrence generation است.

5. Workflow تنها مالک WorkflowExecution است.

6. Care نتیجه Workflow را تفسیر می‌کند.

7. `MedicationTaken` متعلق به Care است، نه Workflow یا Device.

8. `ConfirmationMethod` مدل Runtime رسمی نیست.

9. Care از `Confirmation Requirement` برای بیان نیاز کسب‌وکاری استفاده می‌کند.

10. Workflow مالک `ConfirmationPolicy` و ارزیابی `ConfirmationEvidence` است.

11. Hardware Fact ابتدا توسط Workflow ارزیابی می‌شود و مستقیماً Completion ایجاد نمی‌کند.

12. Care مستقیماً Device را کنترل نمی‌کند.

13. CareCompletion تاریخچه مستقل و idempotent دارد.

14. Care در MVP به Licensing وابستگی ندارد.

15. Media با Reference مدیریت می‌شود و داخل Care ذخیره نمی‌شود.

---

# Final Principle

> **Care defines what the activity means.  
> Scheduling determines when it occurs.  
> Workflow determines how execution proceeds and evaluates evidence.  
> Device reports physical facts.  
> Care interprets the final execution result.**