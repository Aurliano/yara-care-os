# Yara — Workflow Domain Contract

**Domain:** Workflow  
**Classification:** Core Domain  
**Status:** Frozen  
**Version:** 1.1

---

## 1. Purpose

Workflow Domain مسئول orchestration اجرای فرآیندهای زمان‌دار و قابل‌تأیید Yara است.

این Domain پاسخ می‌دهد:

> برای یک Occurrence چه Actionهایی باید انجام شوند، چه Evidenceهایی برای تأیید معتبرند، در صورت عدم پاسخ چه اتفاقی بیفتد و Execution چگونه پایان یابد؟

Workflow معنای کسب‌وکاری نتیجه را تفسیر نمی‌کند.

اصل بنیادی:

> **Workflow coordinates execution; business domains interpret meaning.**

مثلاً Workflow می‌تواند اعلام کند:

`ExecutionConfirmed`

اما نمی‌تواند اعلام کند:

`MedicationTaken`

تفسیر دوم متعلق به Care است.

---

# 2. Ubiquitous Language

## Occurrence

یک وقوع مشخص و زمان‌دار که توسط Scheduling ایجاد شده است.

Occurrence ورودی اصلی WorkflowExecution است.

Workflow مسئول محاسبه recurrence یا زمان وقوع نیست.

---

## Workflow Definition

تعریف Policy اجرای یک Workflow.

مشخص می‌کند:

- Initial Action
- Confirmation Policy
- Timeout
- Postpone Rules
- Retry Rules
- Escalation Steps

در MVP، WorkflowDefinition یک BPMN Engine یا Generic Graph Engine نیست.

---

## Workflow Execution

یک اجرای مشخص Workflow برای یک Occurrence.

Lifecycle پایه:

`PENDING → ACTIVE → CONFIRMED`

Terminal Stateهای دیگر:

- MISSED
- CANCELLED
- FAILED

---

## Action

درخواستی که Workflow برای انجام یک عملیات صادر می‌کند.

نمونه:

- SHOW_REMINDER
- PLAY_AUDIO
- OPEN_COMPARTMENT
- REQUEST_CONFIRMATION
- INITIATE_CALL
- NOTIFY_CAREGIVER

Domain مقصد مالک اجرای واقعی Action و lifecycle داخلی آن است.

مثلاً:

`OPEN_COMPARTMENT → Device`

`INITIATE_CALL → Communication`

Workflow مالک PillBox یا CommunicationSession نمی‌شود.

---

## Confirmation Evidence

یک Fact یا تعامل معتبر که می‌تواند به‌عنوان شاهد اجرای Workflow بررسی شود.

Evidence به‌تنهایی business completion نیست.

دو Source رسمی برای Evidence داریم:

### Domain Event Evidence

Fact منتشرشده توسط Domain دیگر.

مثلاً:

`Device → CompartmentClosed`

یا:

`Communication → CommunicationSessionEnded`

### Direct Interaction Evidence

تعامل مستقیمی که از یک Interface معتبر Yara به Workflow گزارش می‌شود.

مثلاً:

`Hub UI → SubmitConfirmationEvidence`

یا:

`Family App → SubmitConfirmationEvidence`

بنابراین UI مجبور نیست برای هر Confirmation یک Domain Event مصنوعی تولید کند.

---

## Confirmation Policy

قانونی که مشخص می‌کند چه Evidenceهایی برای یک WorkflowExecution معتبرند.

مثلاً:

`CompartmentClosed`

یا:

`HubConfirmation`

یا ترکیبی از Evidenceهای مجاز.

Workflow فقط نتیجه می‌گیرد:

`ExecutionConfirmed`

و business meaning را به Domain مالک واگذار می‌کند.

---

## Postpone

تعویق موقت Execution طبق Policy.

Postpone:

- Completion نیست.
- Cancellation نیست.
- ScheduleDefinition اصلی را تغییر نمی‌دهد.

فقط اجرای جاری را طبق Policy به زمان دیگری منتقل می‌کند.

---

## Retry

تلاش مجدد برای یک Action در همان Execution.

Retry با Postpone متفاوت است.

مثلاً:

`Reminder → timeout → Reminder again`

می‌تواند Retry باشد.

---

## Escalation

انتقال Execution به Action بعدی در صورت برآورده نشدن شرط مورد انتظار.

مثلاً:

`Reminder`
↓
`Wait`
↓
`Retry Reminder`
↓
`Wait`
↓
`Notify Caregiver`

Workflow مالک تصمیم Escalation است.

Domain مقصد مالک اجرای Action است.

---

# 3. Aggregates

## WorkflowExecution — Aggregate Root

Aggregate اصلی Runtime در Workflow.

حداقل شامل:

- occurrence_id
- workflow_definition_id
- status
- current_step
- started_at
- completed_at
- postpone_count
- retry_count

Confirmation Evidence و وضعیت Escalation در Context همین Execution مدیریت می‌شوند.

هر Execution به یک Occurrence پایدار اشاره می‌کند.

---

## WorkflowDefinition — Aggregate Root

Policy قابل استفاده برای WorkflowExecutionها.

حداقل تعریف می‌کند:

- Initial Action
- Confirmation Policy
- Timeout
- Retry Rules
- Postpone Rules
- Escalation Steps

Definition در MVP محدود و صریح باقی می‌ماند.

---

# 4. Execution Flow

Flow پایه:

`OccurrenceDue`
↓
`WorkflowExecution`
↓
`Initial Action`
↓
`Wait for Evidence`
↓
`Confirmation / Timeout / Postpone`

در صورت Evidence:

`Evidence`
↓
`Confirmation Policy`
↓
`ExecutionConfirmed`

در صورت Timeout:

`Timeout`
↓
`Retry / Escalation`
↓
`Next Action`

اگر تمام مسیر بدون Confirmation پایان یابد:

`ExecutionMissed`

---

# 5. Evidence Sources

Workflow دو مسیر رسمی برای دریافت Evidence دارد.

## A. Domain Event

مثلاً:

`PillBox`
↓
`Device: CompartmentClosed`
↓
`Event`
↓
`Workflow`
↓
`Confirmation Policy`

Device فقط Fact سخت‌افزاری را منتشر می‌کند.

---

## B. Direct Interaction

مثلاً سالمند روی Hub انتخاب می‌کند:

`قرص را خوردم`

Flow:

`Hub UI`
↓
`SubmitConfirmationEvidence`
↓
`Workflow`
↓
`Confirmation Policy`

همین الگو می‌تواند برای Family App یا Interface معتبر دیگری استفاده شود.

Authorization Actor در صورت نیاز توسط Identity & Access بررسی می‌شود.

---

## Evidence Source Rule

Evidence Typeهایی که هنوز Domain یا Interaction Contract مشخص ندارند وارد مدل نمی‌شوند.

بنابراین `VoiceConfirmed` فعلاً جزو Evidenceهای رسمی Yara نیست.

اگر Voice Interaction در آینده طراحی شود، Evidence معتبر خودش را طبق Contract همان Domain ارائه خواهد کرد.

---

# 6. Public Interface

## Commands

- `StartExecution`
- `SubmitConfirmationEvidence`
- `PostponeExecution`
- `CancelExecution`
- `AdvanceEscalation`
- `ReportActionResult`

## Queries

- `GetExecution`
- `GetActiveExecutions`
- `GetExecutionStatus`
- `GetWorkflowDefinition`

---

# 7. Published Events

- `ExecutionStarted`
- `ExecutionConfirmed`
- `ExecutionMissed`
- `ExecutionPostponed`
- `ExecutionCancelled`
- `ExecutionFailed`
- `EscalationTriggered`

Workflow فقط Execution Fact منتشر می‌کند.

مثلاً:

`ExecutionConfirmed`

نه:

`MedicationTaken`

---

# 8. Action Contracts

Workflow Action را درخواست می‌کند، ولی Domain مقصد مالک اجرای آن است.

### Device

`Workflow`
→ `OPEN_COMPARTMENT`
→ `DeviceCommand`

Device مالک Command lifecycle است.

---

### Communication

`Workflow`
→ `INITIATE_CALL`
→ `CommunicationSession`

Communication مالک Session lifecycle است.

---

### Notification

`Workflow`
→ `NOTIFY_CAREGIVER`
→ `Notification`

Notification مالک delivery است.

---

Workflow نباید مدل داخلی Domain مقصد را مدیریت کند.

---

# 9. Confirmation Policy

Confirmation Policy متعلق به Workflow است.

Care می‌تواند هنگام تعریف فرآیند مشخص کند چه نوع تأییدی موردنیاز است، اما ارزیابی Evidence در Runtime توسط Workflow انجام می‌شود.

اصطلاحات رسمی:

- `ConfirmationPolicy`
- `ConfirmationEvidence`

اصطلاح مبهم `ConfirmationMethod` در مدل نهایی استفاده نمی‌شود.

---

# 10. Idempotency

Workflow باید در برابر Event، Evidence و Action Result تکراری مقاوم باشد.

مثلاً دریافت دوباره:

`CompartmentClosed`

نباید:

- Execution را دوباره Confirm کند.
- Event نتیجه را دوباره ایجاد کند.
- Action دیگری ناخواسته اجرا کند.

همچنین یک Occurrence نباید چند WorkflowExecution فعال ناسازگار ایجاد کند.

---

# 11. Offline-First

Workflowهای ضروری باید بدون Backend روی Hub قابل اجرا باشند.

Hub باید بتواند:

- WorkflowExecution را شروع کند.
- Actionهای محلی را اجرا کند.
- Evidence دریافت کند.
- ConfirmationPolicy را ارزیابی کند.
- Postpone و Retry را مدیریت کند.
- Escalation محلی را ادامه دهد.
- نتیجه را برای Sync بعدی نگه دارد.

قطع اینترنت نباید Workflow حیاتی سالمند را متوقف کند.

Actionهایی که ذاتاً به سرویس Remote نیاز دارند ممکن است طبق Policy Fail، Retry یا Defer شوند.

---

# 12. Invariants

1. هر WorkflowExecution دقیقاً متعلق به یک Occurrence است.

2. برای یک Occurrence نباید چند Execution فعال ناسازگار وجود داشته باشد.

3. Terminal Execution دوباره Active نمی‌شود.

4. فقط Evidence معتبر طبق ConfirmationPolicy می‌تواند Execution را Confirm کند.

5. Evidence تکراری نباید اثر Business/Execution تکراری ایجاد کند.

6. Postpone فقط طبق Policy مجاز است.

7. Retry فقط طبق Policy مجاز است.

8. Escalation فقط طبق ترتیب Definition انجام می‌شود.

9. Workflow business meaning مانند `MedicationTaken` تولید نمی‌کند.

10. Workflow lifecycle داخلی DeviceCommand، CommunicationSession یا Notification را مالک نیست.

11. Workflow recurrence و Occurrence generation را انجام نمی‌دهد.

---

# 13. Boundaries

## Workflow owns

- WorkflowDefinition
- WorkflowExecution
- Action orchestration
- ConfirmationPolicy
- ConfirmationEvidence evaluation
- Postpone
- Retry policy
- Escalation decision
- Execution lifecycle

## Workflow does NOT own

- Care meaning
- Medication
- Schedule recurrence
- Occurrence generation
- Device state
- DeviceCommand lifecycle
- BLE
- CommunicationSession lifecycle
- Notification delivery
- Synchronization transport
- Historical telemetry

---

# 14. Dependencies

| Domain | Relationship |
|---|---|
| Scheduling | دریافت `OccurrenceDue` |
| Care | انتشار Execution result برای business interpretation |
| Device | Action Contract + دریافت hardware facts |
| Communication | Action Contract + دریافت session results |
| Notification | Action Contract |
| Identity & Access | Authorization/Actor reference در interactionهای لازم |
| Event | Publish/Consume |
| Synchronization | انتقال state و events بین Hub و Backend |

---

# 15. Architectural Decisions — Frozen

1. Occurrence ورودی اصلی WorkflowExecution است.

2. Scheduling زمان را تعیین می‌کند؛ Workflow زمان‌بندی recurrence انجام نمی‌دهد.

3. Workflow business meaning تولید نمی‌کند.

4. `ConfirmationPolicy` و `ConfirmationEvidence` اصطلاحات رسمی مدل هستند.

5. Confirmation Evidence می‌تواند از Domain Event یا Direct Interaction دریافت شود.

6. UI برای Confirmation ساده مجبور به تولید Domain Event مصنوعی نیست.

7. Evidenceهای بدون Contract مشخص، مانند Voice Confirmation فعلاً وارد مدل نمی‌شوند.

8. Device فقط hardware fact تولید می‌کند.

9. Workflow می‌تواند Device Action درخواست کند ولی DeviceCommand را مالک نیست.

10. Workflow می‌تواند Communication Action درخواست کند ولی CommunicationSession را مالک نیست.

11. Escalation decision متعلق به Workflow است؛ delivery متعلق به Domain مقصد است.

12. Workflowهای ضروری Offline روی Hub اجرا می‌شوند.

13. Workflow باید نسبت به Evidence/Event تکراری idempotent باشد.

14. WorkflowDefinition در MVP ساده و محدود باقی می‌ماند.

15. BPMN، Generic Graph Engine و Workflow Designer فعلاً ساخته نمی‌شوند.

---

# Final Principle

> **Scheduling decides when.  
> Workflow coordinates what happens next.  
> Device and Communication perform operations and report facts.  
> Workflow evaluates evidence.  
> Care interprets the final result.**