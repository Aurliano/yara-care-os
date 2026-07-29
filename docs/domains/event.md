# Yara — Event Domain Contract

**Domain:** Event  
**Classification:** Supporting Domain  
**Status:** Frozen  
**Version:** 1.1

---

## 1. Purpose

Event Domain مسئول ثبت و انتشار Factهای مهمی است که در Domainهای Yara رخ داده‌اند و سایر بخش‌های سیستم ممکن است به آن‌ها واکنش نشان دهند.

مثال:

- ExecutionConfirmed
- CompartmentClosed
- DeviceOffline
- CommunicationSessionEnded
- CareActivityCreated
- OccurrenceDue

اصل بنیادی:

> **Events describe facts that already happened.**

Event دستور انجام کار نیست و معنای Domain تولیدکننده را تغییر نمی‌دهد.

---

# 2. Ubiquitous Language

## Domain Event

یک Fact تغییرناپذیر درباره اتفاقی که در یک Domain رخ داده است.

مثال:

`ExecutionConfirmed`

نه:

`ConfirmExecution`

اولی Event است؛ دومی Command.

---

## Event Producer

Domainای که Event را تولید می‌کند و مالک معنای آن Fact است.

مثلاً:

`Device → CompartmentClosed`

Producer مالک business meaning همان Event است.

---

## Event Consumer

Domain یا Componentای که به Event علاقه دارد و پس از دریافت آن واکنش نشان می‌دهد.

Producer نباید Consumerهای خود را بشناسد.

---

## Event Envelope

Metadata مشترک Eventها برای شناسایی، tracing و پردازش قابل‌اعتماد.

حداقل:

- event_id
- event_type
- event_version
- producer
- occurred_at
- recorded_at
- correlation_id
- causation_id
- payload

---

## Correlation ID

شناسه‌ای برای مرتبط کردن عملیات و Eventهایی که بخشی از یک جریان منطقی مشترک هستند.

مثلاً:

`Occurrence`
↓
`WorkflowExecution`
↓
`DeviceCommand`
↓
`CompartmentClosed`
↓
`ExecutionConfirmed`

می‌توانند correlation مشترکی داشته باشند.

`correlation_id` برای **distributed tracing** است.

این شناسه:

- مالک Aggregate نیست.
- FK بین Domainها نیست.
- جایگزین Domain Identity نیست.
- برای enforce کردن business invariant استفاده نمی‌شود.

مثلاً:

`occurrence_id`

همچنان Identity مربوط به Occurrence است.

`workflow_execution_id`

همچنان Identity مربوط به WorkflowExecution است.

`command_id`

همچنان Identity مربوط به DeviceCommand است.

حتی اگر همه آن‌ها یک `correlation_id` مشترک داشته باشند.

---

## Causation ID

مشخص می‌کند کدام Command یا Event مستقیماً باعث ایجاد Event جاری شده است.

مثلاً:

`DeviceCommandCompleted`

ممکن است:

`causation_id = device_command_id`

داشته باشد.

Causation برای tracing رابطه علت مستقیم است و جایگزین Referenceهای Domain نمی‌شود.

---

# 3. Event Record

EventRecord نماینده Fact ثبت‌شده در Event Domain است.

حداقل شامل:

- event_id
- event_type
- event_version
- producer
- occurred_at
- recorded_at
- correlation_id
- causation_id
- payload

Event پس از ثبت Immutable است.

Event Domain نباید مدل داخلی Producer را داخل schema خودش بازسازی کند.

---

# 4. Public Interface

## Commands

- `PublishEvent`
- `RecordEvent`

## Queries

- `GetEvent`
- `GetEventsByCorrelation`
- `GetEventsByProducer`
- `GetEventsForEntity`
- `GetEventsSince`

این Queryها برای:

- Trace
- Debug
- Operational investigation

مفید هستند.

Event Domain جای Reporting یا Analytics نیست.

---

# 5. Event Flow

Flow پایه:

`Domain Transaction`
↓
`Domain Event Created`
↓
`Event Recorded`
↓
`Published`
↓
`Consumer(s)`
↓
`Consumer Action`

Producer به Consumer وابستگی مستقیم ندارد.

مثلاً:

`Device`
↓
`CompartmentClosed`
↓
`Workflow`
↓
`ExecutionConfirmed`
↓
`Care`
↓
`MedicationTaken`

هر Domain معنای خودش را مالک است.

---

# 6. Correlation vs Domain References

Correlation و Domain Reference دو مسئله متفاوت هستند.

### Correlation

پاسخ می‌دهد:

> چه عملیات‌هایی بخشی از یک جریان منطقی مشترک هستند؟

### Domain Reference

پاسخ می‌دهد:

> این رکورد مشخصاً به کدام Entity/Aggregate مرتبط است؟

مثلاً:

`DeviceCommand.execution_reference = WorkflowExecution.id`

یک Domain Reference است.

اما:

`correlation_id = abc123`

فقط برای دنبال کردن جریان end-to-end است.

بنابراین:

> **Correlation enables tracing; Domain Identity establishes identity and relationships.**

استفاده از `correlation_id` به‌عنوان جایگزین:

- occurrence_id
- workflow_execution_id
- command_id
- session_id
- elder_id

ممنوع است.

---

# 7. Idempotency

هر Event دارای `event_id` یکتا است.

Consumer باید بتواند دریافت تکراری همان Event را بدون اجرای دوباره اثر جانبی پردازش کند.

اصل:

> **At-least-once delivery must not mean repeated business action.**

مثلاً دریافت دوباره:

`ExecutionConfirmed`

نباید باعث ثبت دوباره CareCompletion شود.

`correlation_id` نیز Idempotency Key نیست.

چند Event مختلف می‌توانند یک Correlation ID داشته باشند.

---

# 8. Ordering

Event Domain تضمین Global Ordering برای کل Yara نمی‌دهد.

در صورت نیاز، ترتیب فقط در محدوده Aggregate یا Stream مربوطه حفظ یا قابل تشخیص است.

Business Logic نباید به ترتیب سراسری Eventها وابسته باشد.

---

# 9. Offline-First

Hub می‌تواند در حالت Offline Event تولید کند.

Event باید:

- ID پایدار داشته باشد.
- زمان وقوع واقعی را حفظ کند.
- Locally durable باشد.
- بعداً Sync شود.
- در Backend دوباره ایجاد نشود.
- در ارسال تکراری idempotently پردازش شود.

بنابراین:

`occurred_at`

با:

`recorded_at`

و زمان Sync یک مفهوم نیست.

Correlation نیز باید در صورت Offline execution قابل حفظ باشد تا جریان بعد از Sync همچنان traceable باقی بماند.

---

# 10. Event Versioning

هر Event Type دارای Version است.

مثلاً:

`DeviceOffline.v1`

تغییر Payload نباید Consumerهای موجود را بدون Compatibility Strategy بشکند.

در MVP Versioning ساده باقی می‌ماند.

Schema Registry یا Event Platform مستقل ساخته نمی‌شود.

---

# 11. Invariants

1. هر Event دارای `event_id` یکتا است.

2. Event ثبت‌شده Immutable است.

3. هر Event Producer مشخص دارد.

4. `occurred_at` زمان وقوع Fact است، نه زمان Sync.

5. Event تکراری با همان `event_id` نباید دوباره اعمال شود.

6. Event نباید Command باشد.

7. Producer نباید Consumerهای Event را بشناسد.

8. Payload فقط اطلاعات لازم Event را حمل می‌کند، نه Snapshot کامل Aggregate.

9. Event Type باید Version داشته باشد.

10. Event Domain business meaning جدید تولید نمی‌کند.

11. `correlation_id` جایگزین Domain Identity نیست.

12. `correlation_id` برای enforce کردن Domain Relationship یا Business Invariant استفاده نمی‌شود.

13. `causation_id` فقط رابطه علت مستقیم را برای tracing مشخص می‌کند.

14. `correlation_id` یا `causation_id` جایگزین `event_id` یا Idempotency Key نیستند.

---

# 12. Boundaries

## Event owns

- Event identity
- Event envelope
- Event metadata
- Correlation
- Causation
- Event version
- Immutable event record
- Publication contract

## Event does NOT own

- Business rules
- Domain identities
- Workflow orchestration
- Notification delivery
- Synchronization transport
- Audit policy
- Analytics
- Telemetry history
- Commands

---

# 13. Dependencies

| Domain | Relationship |
|---|---|
| Care | Publish / Consume |
| Workflow | Publish / Consume |
| Device | Publish / Consume where required |
| Communication | Publish |
| Scheduling | Publish |
| Notification | Consume |
| Monitoring | Consume where relevant |
| Audit | Consume |
| Synchronization | Transport Events بین Hub و Backend |

Event Domain به مدل داخلی هیچ‌کدام وابسته نیست.

---

# 14. Event vs Audit

Event می‌گوید:

> چه Fact دامنه‌ای رخ داد؟

Audit می‌گوید:

> چه Actorی چه عملی انجام داد و چه چیزی تغییر کرد؟

ممکن است یک Operation هم Event تولید کند و هم Audit Record.

اما این دو مفهوم یکی نیستند.

---

# 15. Event vs Synchronization

Event:

> چه اتفاقی افتاد؟

Synchronization:

> این اطلاعات چگونه بین Hub و Backend منتقل شود؟

Event Domain مالک:

- transport
- retry
- connectivity
- sync queue

نیست.

---

# 16. Architectural Decisions — Frozen

1. Yara از Domain Event برای ارتباط غیرمستقیم Domainها استفاده می‌کند.

2. Eventها Immutable هستند.

3. هر Event دارای Identity پایدار و Version است.

4. Correlation و Causation برای tracing جریان‌ها استفاده می‌شوند.

5. `correlation_id` جایگزین هیچ Domain Identity یا Domain Reference نیست.

6. `causation_id` رابطه علت مستقیم را نشان می‌دهد، نه ownership.

7. Idempotency بر اساس Event Identity/Processing Contract مدیریت می‌شود، نه Correlation ID.

8. Consumerها باید Event تکراری را idempotently پردازش کنند.

9. Global Event Ordering تضمین نمی‌شود.

10. Hub می‌تواند Offline Event تولید کند.

11. `occurred_at` از زمان ثبت و Sync مستقل است.

12. Event با Command، Audit یا SyncQueue یکی نیست.

13. Producer Consumerهای خود را نمی‌شناسد.

14. در MVP Kafka، Event Sourcing، Schema Registry یا Event Platform مستقل ساخته نمی‌شود.

15. Backend اولیه می‌تواند از PostgreSQL + Transactional Outbox استفاده کند.

16. مهاجرت آینده به Message Broker نباید Domain Contract را تغییر دهد.

---

# Final Principle

> **Domains own identity and meaning.  
> Events record facts.  
> Correlation connects the trace — not the data model.  
> Consumers decide how to react.  
> Synchronization moves those facts reliably.**