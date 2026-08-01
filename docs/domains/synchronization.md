
# Yara — Synchronization Domain Contract

**Domain:** Synchronization 
**Classification:** Supporting Domain  
**Status:** Frozen  
**Version:**  V2.0

## 1. Purpose
Synchronization Domain مسئول تضمین Reliable State Replication بین Backend و Hub است.
Synchronization هیچ Business Logic تولید یا تفسیر نمی‌کند.
Synchronization فقط وضعیتی را همگام می‌کند که توسط Owner همان Aggregate منتشر شده است.
## 2. Domain Philosophy
Synchronization is not Messaging.
Synchronization is not Transport.
Synchronization is not Event Store.
Synchronization is not Workflow.
Synchronization is not Device Control.
Synchronization owns replication only.
## 3. Responsibilities
Synchronization مسئول:
Synchronization Sessions
Replica States
Replica Health
Checkpoints
Delta Replication
Snapshot Replication
Conflict Detection
Synchronization Progress
Synchronization Statistics
Idempotent Replication
## 4. Out of Scope
Synchronization مسئول نیست:
Care Logic
Scheduling
Workflow
Notification
Device Commands
BLE
MQTT
HTTP
WebSocket
Event Publishing
Event Storage
Authentication
Authorization
## 5. Ubiquitous Language
Term	Meaning
Replica	Backend یا Hub
Replica State	وضعیت همگام‌سازی یک Replica
Synchronization Session	یک عملیات کامل Sync
Checkpoint	آخرین نسخه موفق اعمال‌شده روی Replica
Delta	تغییر منتشرشده توسط Domain Owner
Snapshot	تصویر کامل Aggregate منتشرشده توسط Domain Owner
Conflict	تغییر همزمان دو Replica
Tombstone	حذف منطقی
Upload	Hub → Backend
Download	Backend → Hub

## 6. Aggregate Roots
SynchronizationSession
نماینده یک عملیات کامل Synchronization.
ReplicaState
مالک وضعیت فعلی Replica است.
ReplicaState شامل:
Current Checkpoint
Replica Health
Replica Status
Last Successful Synchronization
Replica Statistics
Checkpoint دیگر Aggregate مستقل نیست.
## 7. Entities
SynchronizationOperation
هر Upload یا Download انجام‌شده.
SynchronizationConflict
Conflict کشف‌شده.
ReplicaVersion
نسخه Aggregate روی Replica.
## 8. Value Objects
AggregateReference
SynchronizationToken
SynchronizationWindow
SynchronizationStatistics
ConflictResolutionRequest
## 9. Fundamental Principle
Synchronization هرگز داده Business Domainها را مستقیماً نمی‌خواند.
Synchronization هرگز Query روی Aggregateهای سایر Domainها اجرا نمی‌کند.
Synchronization فقط Payloadهایی را دریافت می‌کند که توسط Domain Owner منتشر شده‌اند.
Business Domains همیشه Push می‌کنند.
Synchronization هرگز Pull نمی‌کند.
## 10. Synchronization Lifecycle
Idle

↓

SynchronizationRequested

↓

SessionStarted

↓

PayloadReceived

↓

Validation

↓

ChangesApplied

↓

CheckpointAdvanced

↓

SessionCompleted
Failure:
SessionStarted

↓

TransferFailed

↓

RetryScheduled

↓

SynchronizationResumed
## 11. Synchronization Unit
Synchronization همیشه روی Aggregate انجام می‌شود.
هرگز روی:
Table
Row
Field
نمونه Aggregateها:
CareActivity
WorkflowExecution
Device
CommunicationSession
Synchronization خود این Aggregateها را نمی‌شناسد؛ فقط Payload مربوط به آن‌ها را دریافت می‌کند.
## 12. Publish Model
هر Business Domain موظف است هنگام تغییر Aggregate یکی از موارد زیر را منتشر کند:
Aggregate Delta
Aggregate Snapshot
Synchronization مسئول تولید Delta نیست.
Synchronization مسئول استخراج Snapshot نیست.
Synchronization فقط آن‌ها را Replicate می‌کند.
## 13. Synchronization Strategies
Delta Synchronization
روش پیش‌فرض.
Snapshot Synchronization
فقط برای:
First Synchronization
Replica Recovery
Replica Reset
Corrupted Replica
## 14. Checkpoints
هر Replica دقیقاً یک Checkpoint جاری دارد.
Checkpoint داخل ReplicaState نگهداری می‌شود.
Checkpoint:
فقط به جلو حرکت می‌کند.
هرگز Rollback نمی‌شود.
فقط پس از Apply موفق تغییر می‌کند.
## 15. Aggregate Version
تمام Aggregateهایی که قابلیت Synchronization دارند باید دارای Version یکنواخت (Monotonic Version) باشند.
Synchronization نسخه تولید نمی‌کند.
Synchronization نسخه را افزایش نمی‌دهد.
Owner هر Aggregate مسئول تولید و افزایش Version است.
نوع Version (Integer، RowVersion، Revision و...) به Owner همان Domain تعلق دارد.
## 16. Conflict Detection
Conflict زمانی رخ می‌دهد که:
هر دو Replica تغییر مستقل ثبت کرده باشند.
Versionها با هم ناسازگار باشند.
هیچ Checkpoint مشترک معتبر وجود نداشته باشد.
Conflict از دید Backend یا Hub تعریف نمی‌شود.
Conflict کاملاً متقارن است.
## 17. Conflict Resolution
Synchronization فقط:
Conflict را ثبت می‌کند.
Conflict را منتشر می‌کند.
نتیجه Resolution را اعمال می‌کند.
Synchronization هرگز Merge انجام نمی‌دهد.
اگر Resolution نیازمند Business Knowledge باشد:
ConflictDetected

↓

Business Domain

↓

ResolveConflict

↓

Synchronization applies result
Merge همیشه توسط Owner همان Aggregate انجام می‌شود.
## 18. Offline-first Rules
Hub باید بتواند:
Offline کار کند.
عملیات را ذخیره کند.
پس از اتصال Replicate کند.
Backend هرگز Online بودن Hub را فرض نمی‌کند.
## 19. Idempotency
تمام عملیات Replication باید Idempotent باشند.
اعمال مجدد یک Delta نباید باعث:
Duplicate Aggregate
Duplicate State
Duplicate Snapshot
Duplicate Operation
شود.
## 20. Tombstones
Synchronization فقط Tombstone را Replicate می‌کند.
پاک‌سازی دائمی خارج از مسئولیت این Domain است.
## 21. Public Commands
StartSynchronization

ResumeSynchronization

CancelSynchronization

SubmitAggregateDelta

SubmitAggregateSnapshot

ApplyDelta

ApplySnapshot

ResolveConflict

AdvanceCheckpoint

ResetReplica

MarkReplicaHealthy

MarkReplicaOutdated
Submit* توسط Business Domainها فراخوانی می‌شود.
Apply* فقط داخل Synchronization استفاده می‌شود.
## 22. Public Queries
GetSynchronizationSession

GetReplicaState

GetCheckpoint

GetPendingOperations

GetSynchronizationStatistics

GetConflicts

GetSynchronizationHistory
## 23. Published Events
SynchronizationStarted

SynchronizationCompleted

SynchronizationCancelled

SynchronizationFailed

ReplicaUpdated

CheckpointAdvanced

ConflictDetected

ConflictResolved

DeltaApplied

SnapshotApplied
Synchronization هیچ Business Event منتشر نمی‌کند.
## 24. Cross-Domain Dependencies
Synchronization هیچ Domain دیگری را Query نمی‌کند.
Synchronization هیچ FK به Domainهای Business ندارد.
Business Domainها از طریق SubmitAggregateDelta و SubmitAggregateSnapshot تغییرات خود را در اختیار Synchronization قرار می‌دهند.
Synchronization فقط Payload را پردازش می‌کند.
## 25. Ownership Rules
Business Domains:
مالک Aggregate
مالک Version
مالک Delta
مالک Snapshot
مالک Merge
Synchronization:
مالک Replication
مالک Replica State
مالک Session
مالک Conflict Tracking
مالک Checkpoint
مالک Idempotency
## 26. Invariants
هر SynchronizationSession دارای شناسه یکتا است.
هر Replica دقیقاً یک ReplicaState دارد.
هر Replica دقیقاً یک Checkpoint جاری دارد.
Checkpoint فقط به جلو حرکت می‌کند.
Synchronization هیچ Aggregateی را مستقیماً Query نمی‌کند.
Delta فقط توسط Domain Owner تولید می‌شود.
Snapshot فقط توسط Domain Owner تولید می‌شود.
Version فقط توسط Domain Owner افزایش می‌یابد.
Merge فقط توسط Domain Owner انجام می‌شود.
Synchronization فقط نتیجه Merge را اعمال می‌کند.
تمام عملیات قابل Resume هستند.
تمام عملیات Idempotent هستند.
## 27. Error Model
ReplicaUnavailable

CheckpointMismatch

InvalidDelta

SnapshotCorrupted

VersionMismatch

SynchronizationConflict

ReplicaOutdated

SynchronizationCancelled

SynchronizationTimeout
## 28. Architectural Decisions
Offline-first
Eventually Consistent
Aggregate-based Replication
Push-based Synchronization
No Cross-Domain Reads
No Business Interpretation
Idempotent Replication
Deterministic Conflict Tracking
Transport Agnostic
Protocol Agnostic
## 29. Future Extension Points
Incremental Snapshot
Compression
Encryption
Multi-Hub Support
Selective Synchronization
Background Prioritization
Differential Snapshot
بدون تغییر Contract فعلی.
## 30. Final Principle
Business Domains own business state.

Business Domains publish synchronization payloads.

Synchronization never discovers business state by itself.

Synchronization guarantees reliable, idempotent, offline-first replication while preserving complete domain ownership.