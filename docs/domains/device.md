# Yara — Device Domain Contract

**Domain:** Device  
**Classification:** Core Domain  
**Status:** Frozen  
**Version:** 1.1

> این نسخه تمام تصمیمات Frozen نسخه 1.0 را حفظ می‌کند و قرارداد ارتباط `DeviceCommand` با Workflow را دقیق‌تر می‌کند.

---

## 1. Purpose

Device Domain مسئول مدل‌سازی و مدیریت سخت‌افزارهای فیزیکی اکوسیستم Yara است.

این Domain پاسخ می‌دهد:

> چه سخت‌افزاری داریم، چه قابلیت‌هایی دارد، به چه کسی تخصیص داده شده، چگونه با سایر تجهیزات ارتباط منطقی دارد و چه عملیاتی می‌تواند انجام دهد؟

اصل بنیادی:

> **Device owns hardware identity, capability, state and execution — not business meaning.**

Device می‌تواند گزارش کند:

`CompartmentClosed`

اما:

`MedicationTaken`

متعلق به Care است.

---

# 2. Core Model

Aggregateهای اصلی:

- `Device`
- `DeviceModel`
- `DeviceAssignment`
- `Pairing`
- `DeviceCommand`

Entityهای مهم:

- `Compartment`
- `CompartmentAssignment`
- `DeviceCapabilityOverride`

ساختار کلی:

`DeviceModel`
↓
`Device`
├── Profile
├── Current State
├── Capability Overrides
└── Compartments

و مستقل از آن:

`DeviceAssignment`

`Pairing`

`DeviceCommand`

---

# 3. Device Model & Capability

`DeviceModel` منبع حقیقت Capabilityهای سخت‌افزاری است.

مثلاً:

`Galaxy Tab S2`
- DISPLAY
- SPEAKER
- MICROPHONE
- CAMERA
- BLE
- BATTERY

Device خاص فقط:

- Configuration
- Current Capability State
- Audited Override

را نگه می‌دارد.

`DeviceCapabilityOverride` باید:

- Explicit
- Reasoned
- Audit-able
- Actor-aware

باشد و نمی‌تواند Capability جدیدی خارج از DeviceModel ایجاد کند.

---

# 4. Device Assignment

رابطه Device و Elder از طریق `DeviceAssignment` مدل می‌شود.

Lifecycle نمونه:

`Inventory → Assigned → Returned → Refurbished → Reassigned`

Assignment Type حداقل:

- OWNED
- RENTED
- LOANER

Device مالک دائمی Elder نیست و این مدل باید فروش، اجاره، تعویض و دستگاه جایگزین را پشتیبانی کند.

---

# 5. Pairing

`Pairing` رابطه Lifecycleدار Hub و Peripheral Device است.

Lifecycle پایه:

`PAIRING → ACTIVE → DISCONNECTED → REVOKED`

Pairing با وضعیت لحظه‌ای BLE یکی نیست.

---

# 6. DeviceCommand

`DeviceCommand` یک Aggregate مستقل و قابل ردیابی است.

Lifecycle پایه:

`QUEUED → DELIVERED → EXECUTING → SUCCEEDED`

Terminal Stateهای دیگر:

- FAILED
- EXPIRED
- CANCELLED

Device مالک:

- Command Identity
- Intent
- Target Device
- Parameters
- Lifecycle
- Expiration
- Result
- Failure Reason
- Idempotency Identity

است.

Synchronization مالک:

- Transport
- Retry delivery
- Connectivity handling
- Message transfer
- ACK transport

است.

بنابراین:

> **DeviceCommand ≠ SyncQueue**

---

# 7. Workflow Execution Reference

وقتی DeviceCommand در نتیجه یک Workflow Action ایجاد می‌شود، باید Execution مبدأ قابل ردیابی باشد.

Contract رسمی:

`WorkflowExecution`
↓
`Action: OPEN_COMPARTMENT`
↓
`DeviceCommand`
↓
`execution_reference = WorkflowExecution.id`

اما `execution_reference` در Device یک:

> **Opaque External Reference**

است.

Device فقط می‌داند:

> این Command از یک Execution خارجی با این Identity منشأ گرفته است.

Device:

- WorkflowExecution را Load نمی‌کند.
- Workflow State را تفسیر نمی‌کند.
- Workflow invariant را enforce نمی‌کند.
- برای اجرای Command به Workflow Database وابسته نیست.

---

## Cross-Domain FK Rule

بین:

`DeviceCommand.execution_reference`

و:

`WorkflowExecution.id`

**Foreign Key دیتابیسی Cross-Domain ایجاد نمی‌شود.**

بنابراین:

`DeviceCommand`
`execution_reference = "wf_exec_123"`

مجاز است، بدون اینکه Device schema به جدول Workflow وابسته شود.

Integrity داخل هر Domain حفظ می‌شود و ارتباط بین Domainها از طریق Contract و Event/Reference مدیریت می‌شود.

---

## Optional Origin

همه DeviceCommandها الزاماً از Workflow ایجاد نمی‌شوند.

مثلاً:

- Support diagnostic command
- Manual administrative command
- OTA-related operation
- Local Hub operation

بنابراین `execution_reference` فقط زمانی وجود دارد که Command واقعاً توسط WorkflowExecution ایجاد شده باشد.

در صورت نیاز به Generalization در آینده می‌توان Origin Metadata را توسعه داد، اما در MVP polymorphic origin framework ساخته نمی‌شود.

---

# 8. Idempotency

هر DeviceCommand دارای Identity پایدار است.

Hub باید اجرای تکراری همان Command را تشخیص دهد.

مثلاً:

`OPEN_COMPARTMENT`
↓
Executed
↓
ACK lost
↓
Command delivered again
↓
DO NOT execute physical action again

اصل:

> **Delivery retry ≠ Command execution retry.**

`execution_reference` نیز جایگزین `command_id` یا `idempotency_key` نیست.

ممکن است یک WorkflowExecution در طول lifecycle خود چند DeviceCommand متفاوت ایجاد کند.

---

# 9. Device Events

Device فقط Fact سخت‌افزاری یا نتیجه عملیات خود را منتشر می‌کند.

نمونه:

- `DeviceOnline`
- `DeviceOffline`
- `DevicePaired`
- `CompartmentOpened`
- `CompartmentClosed`
- `DeviceCommandCompleted`
- `DeviceCommandFailed`

Device نباید Eventهایی مانند:

`MedicationTaken`

منتشر کند.

---

# 10. Current State vs Monitoring

Device مالک Current Operational State است.

مثلاً:

- battery = 67%
- network = online
- pillbox = connected

Monitoring مالک تاریخچه Telemetry است.

Device نباید به time-series store تبدیل شود.

---

# 11. Offline-First

Hub باید بدون Backend بتواند در محدوده داده و Policy محلی معتبر:

- تجهیزات محلی را مدیریت کند.
- Device State را دریافت کند.
- Commandهای محلی معتبر را اجرا کند.
- Hardware Fact تولید کند.
- نتیجه را برای Sync بعدی نگه دارد.

Synchronization مسئول انتقال قابل‌اعتماد بین Hub و Backend است.

---

# 12. Invariants

1. هر Device دقیقاً یک DeviceModel معتبر دارد.

2. هر Compartment دقیقاً متعلق به یک Device میزبان است.

3. DeviceProfile قابلیت سخت‌افزاری جدید ایجاد نمی‌کند.

4. DeviceCapabilityOverride فقط روی Capability موجود Model اعمال می‌شود.

5. Pairing باید با Capabilityهای Deviceها سازگار باشد.

6. یک Compartment در یک زمان حداکثر یک Assignment فعال دارد.

7. تاریخچه Assignment، Pairing و Command حذف نمی‌شود.

8. Device غیرفعال/Revoked Command عملیاتی جدید دریافت نمی‌کند.

9. هر DeviceCommand Identity پایدار دارد.

10. اجرای تکراری همان Command نباید اثر فیزیکی ناخواسته تکراری ایجاد کند.

11. `execution_reference` فقط Reference مبدأ است و مالکیت WorkflowExecution را به Device منتقل نمی‌کند.

12. وجود `execution_reference` نباید برای اجرای DeviceCommand نیازمند Query به Workflow باشد.

13. `execution_reference` جایگزین Command Identity یا Idempotency Identity نیست.

---

# 13. Boundaries

## Device owns

- Device Identity
- Device Model
- Capability
- Device Assignment
- Pairing
- Compartment
- Current Device State
- DeviceCommand semantics
- DeviceCommand lifecycle
- Raw hardware facts

## Device does NOT own

- Care meaning
- WorkflowExecution
- Workflow orchestration
- ConfirmationPolicy
- Medication
- Reminder
- Escalation
- Notification delivery
- Licensing rules
- Historical telemetry
- Sync transport

---

# 14. Dependencies

| Domain | Relationship |
|---|---|
| Identity & Access | Authorization + Actor/Elder reference |
| Licensing | Entitlement validation |
| Workflow | Action Contract + opaque execution reference |
| Event | Publish hardware/command facts |
| Monitoring | Telemetry Contract |
| Firmware & OTA | Firmware operations |
| Synchronization | Delivery / Retry / ACK |

Device به مدل داخلی Workflow وابسته نیست.

---

# 15. Workflow ↔ Device Contract

رابطه نهایی:

`WorkflowExecution`
↓
`Action`
↓
`DeviceCommand`
↓
`Device executes`
↓
`Device Fact / Command Result`
↓
`Workflow`

Workflow مالک دلیل اجرای Action است.

Device مالک اجرای عملیات سخت‌افزاری است.

برای tracing:

`DeviceCommand.execution_reference = WorkflowExecution.id`

ولی این Reference:

- Opaque است.
- Cross-Domain FK ندارد.
- Dependency تراکنشی ایجاد نمی‌کند.
- برای Authorization یا اجرای Command استفاده نمی‌شود.

---

# 16. Architectural Decisions — Frozen

1. DeviceCommand Aggregate مستقل است.

2. DeviceCommand با SyncQueue یکی نیست.

3. Device مالک Command semantics و lifecycle است.

4. Synchronization مالک Transport، Delivery، Retry و ACK است.

5. DeviceCommand باید idempotent باشد.

6. Command ناشی از Workflow می‌تواند `execution_reference` داشته باشد.

7. `execution_reference` در این حالت به `WorkflowExecution.id` اشاره می‌کند.

8. Device این شناسه را Opaque External Reference می‌بیند.

9. Cross-Domain FK بین Device و Workflow ایجاد نمی‌شود.

10. Device برای اجرای Command به Workflow Database وابسته نیست.

11. یک WorkflowExecution می‌تواند چند DeviceCommand ایجاد کند؛ بنابراین execution reference جایگزین command identity نیست.

12. DeviceCommandهایی که منشأ Workflow ندارند مجبور به داشتن execution reference نیستند.

13. Generic polymorphic Origin Model در MVP ساخته نمی‌شود.

14. Device فقط hardware facts را گزارش می‌کند و business meaning تولید نمی‌کند.

15. معماری Device Offline-First باقی می‌ماند.

---

# Final Principle

> **Workflow decides why an action is needed.  
> DeviceCommand records what the device must do.  
> Device owns physical execution.  
> Synchronization guarantees movement.  
> The execution reference provides traceability — not ownership.**