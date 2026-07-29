# Yara — Communication Domain Contract

**Domain:** Communication  
**Classification:** Core Domain  
**Status:** Frozen  
**Version:** 1.1

---

## 1. Purpose

Communication Domain مسئول مدیریت ارتباط میان سالمند و افراد دیگر در اکوسیستم Yara است.

این Domain پاسخ می‌دهد:

> چه ارتباطی، بین چه طرف‌هایی، از چه کانالی، چه زمانی و با چه نتیجه‌ای اتفاق افتاد؟

Communication مالک فرآیند مراقبتی، Escalation یا معنای Care نیست.

اصل بنیادی:

> **Communication manages communication sessions; other domains decide why communication is needed.**

---

# 2. Ubiquitous Language

## Contact

فردی که برای ارتباط با Elder تعریف شده است.

Contact هویت مخاطب در تجربه سالمند است و می‌تواند شامل:

- display name
- photo reference
- phone
- communication identities
- preferred channel

باشد.

شماره تلفن هویت Contact نیست و الزاماً Unique نیست.

Media مانند عکس مخاطب باید از طریق Reference به Media Domain نگهداری شود.

---

## Priority Contact

Contactای که برای دسترسی سریع‌تر سالمند در Hub مشخص شده است.

مثلاً:

- دختر
- پسر
- پرستار

Priority Contact با `Emergency Recipient` یکی نیست.

`Priority Contact` متعلق به Communication است.

`Emergency Recipient` متعلق به Identity & Access است و مشخص می‌کند چه User/Membershipهایی مقصد هشدارهای اضطراری هستند.

یک شخص می‌تواند هر دو نقش را داشته باشد، اما این دو مفهوم Domain مستقل‌اند.

---

## Communication Channel

نوع ارتباط.

حداقل:

- VOICE
- VIDEO
- MESSAGE

فعال بودن برخی Channelها می‌تواند به Entitlement وابسته باشد.

---

## Communication Session

یک ارتباط مشخص میان Participantها.

Session مستقل از Workflow است و lifecycle ارتباط واقعی را نگه می‌دارد.

Lifecycle پایه:

`INITIATED → CONNECTING → CONNECTED → ENDED`

حالت‌های Terminal دیگر:

- MISSED
- DECLINED
- FAILED
- CANCELLED

---

## Session Participant

فرد مشارکت‌کننده در یک CommunicationSession.

حداقل Roleها:

- INITIATOR
- RECIPIENT

مدل Participant-based اجازه می‌دهد Communication به ساختارهای polymorphic مانند:

`initiator_type + initiator_id`

وابسته نشود و در آینده نیز بدون بازطراحی بنیادی چند Participant را پشتیبانی کند.

Group Call در MVP پیاده‌سازی نمی‌شود.

---

## Call Attempt

یک تلاش مشخص برای برقراری Session.

یک Session ممکن است چند Attempt داشته باشد:

`Attempt 1 → FAILED`

`Attempt 2 → FAILED`

`Attempt 3 → ANSWERED`

CallAttempt برای diagnostics، retry tracking و تحلیل کیفیت ارتباط نگهداری می‌شود.

---

## Session Outcome

نتیجه نهایی CommunicationSession.

حداقل:

- ANSWERED
- MISSED
- DECLINED
- FAILED
- CANCELLED

Duration حقیقت مستقل اصلی نیست و در صورت نیاز از:

`connected_at → ended_at`

محاسبه می‌شود.

---

# 3. Aggregates

## Contact — Aggregate Root

نماینده مخاطب Elder در Communication.

مسئول:

- display identity
- communication endpoints
- priority state
- communication preferences

است.

Contact دارای تاریخچه ارتباطی Hard Delete نمی‌شود و باید Archive/Deactivate شود.

---

## CommunicationSession — Aggregate Root

نماینده یک ارتباط مشخص.

حداقل شامل:

- channel
- status
- outcome
- initiated_at
- connected_at
- ended_at

و Participantها و Attemptهای مرتبط است.

---

## SessionParticipant

Entity متعلق به CommunicationSession.

Participant مشخص می‌کند چه طرف‌هایی در Session حضور دارند و Role هرکدام چیست.

---

## CallAttempt

Entity متعلق به CommunicationSession که هر تلاش واقعی برای برقراری تماس را ثبت می‌کند.

---

# 4. Session Flow

Flow پایه:

`Initiate Session`
↓
`Validate Communication Access`
↓
`Create Session`
↓
`Attempt Connection`
↓
`Connected / Failed / Declined / Missed`
↓
`Session Ended`

برای قابلیت plan-gated:

`Initiate VIDEO Session`
↓
`Licensing.HasEntitlement(VIDEO_CALL)`
↓
`Allowed`
↓
`CommunicationSession`

Communication نباید نام Plan را بررسی کند.

غلط:

`plan == PREMIUM`

درست:

`HasEntitlement(VIDEO_CALL)`

---

# 5. Public Interface

## Commands

- `CreateContact`
- `UpdateContact`
- `ArchiveContact`
- `SetPriorityContact`
- `RemovePriorityContact`
- `InitiateSession`
- `AcceptSession`
- `DeclineSession`
- `CancelSession`
- `EndSession`
- `RecordCallAttempt`
- `ReportAttemptResult`

## Queries

- `GetContact`
- `GetElderContacts`
- `GetPriorityContacts`
- `GetSession`
- `GetRecentSessions`
- `GetSessionParticipants`
- `GetCallAttempts`

---

# 6. Published Events

- `ContactCreated`
- `ContactUpdated`
- `ContactArchived`
- `CommunicationSessionInitiated`
- `CommunicationSessionConnected`
- `CommunicationSessionEnded`
- `CommunicationSessionMissed`
- `CommunicationSessionDeclined`
- `CommunicationSessionFailed`
- `CallAttemptStarted`
- `CallAttemptFailed`

Communication فقط facts ارتباطی را منتشر می‌کند.

مثلاً:

`CommunicationSessionMissed`

معتبر است.

اما:

`ElderNeedsHelp`

تفسیر متعلق به Communication نیست.

---

# 7. Workflow Integration

Communication می‌تواند Action درخواست‌شده توسط Workflow را اجرا کند.

مثلاً:

`Workflow`
↓
`INITIATE_CALL`
↓
`Communication`
↓
`CommunicationSession`
↓
`Session Result`
↓
`Event`

Communication مالک lifecycle واقعی Session باقی می‌ماند.

Workflow فقط تصمیم می‌گیرد که یک Communication Action باید انجام شود.

بنابراین رابطه رسمی:

> **Workflow → Communication: Action Contract**

Communication نباید WorkflowExecution را به مدل داخلی خود تبدیل کند.

در صورت نیاز، یک external execution reference / correlation برای trace جریان نگهداری می‌شود.

همچنین Communication مالک Retry یا Escalation Policy مراقبتی نیست.

مثلاً:

`No answer → call again after 5 minutes → notify caregiver`

یک Workflow است، نه رفتار داخلی Communication.

Communication فقط نتیجه هر Session/Attempt را گزارش می‌کند.

---

# 8. Licensing Integration

برخی Communication Capabilityها ممکن است plan-gated باشند.

مثلاً:

- VIDEO_CALL
- VOICE_CALL
- PREMIUM_COMMUNICATION_FEATURE

Communication قبل از شروع قابلیت نیازمند Entitlement، Licensing را بررسی می‌کند.

Licensing پاسخ می‌دهد:

> آیا این قابلیت مجاز است؟

Communication پاسخ می‌دهد:

> Session چگونه ایجاد و مدیریت شود؟

Communication نباید:

- Plan Name
- قیمت Plan
- Subscription logic
- Payment status

را تفسیر کند.

---

# 9. Authorization

Permissionهای Communication توسط Identity & Access ارزیابی می‌شوند.

مثلاً:

- VIEW_CONTACTS
- MANAGE_CONTACTS
- INITIATE_CALL

Communication نباید Role خاصی را Hard-code کند.

غلط:

`if user.role == PRIMARY_CAREGIVER`

درست:

`Can(user, INITIATE_CALL, elder)`

---

# 10. Invariants

1. هر CommunicationSession حداقل Initiator و Recipient معتبر دارد.

2. Participant Role در Context همان Session معنا دارد.

3. Session پایان‌یافته دوباره Active نمی‌شود.

4. `connected_at` فقط برای Session واقعاً Connected ثبت می‌شود.

5. `ended_at` نباید قبل از `connected_at` باشد.

6. Outcome باید با lifecycle Session سازگار باشد.

7. Contact دارای تاریخچه Communication نباید Hard Delete شود.

8. Communication مالک Escalation Policy نیست.

9. Communication business meaning مربوط به Care تولید نمی‌کند.

10. قابلیت plan-gated بدون Entitlement معتبر نباید شروع شود.

11. Communication نباید Plan Name را برای تصمیم‌گیری تجاری بررسی کند.

12. Workflow Action نباید lifecycle داخلی CommunicationSession را دور بزند.

---

# 11. Boundaries

## Communication owns

- Contact
- Priority Contact
- Communication Channel
- Communication Session
- Session Participant
- Call Attempt
- Session lifecycle
- Session outcome
- Communication facts

## Communication does NOT own

- Emergency Recipient
- CareActivity
- Medication
- Workflow orchestration
- Escalation policy
- Reminder
- Notification routing
- Subscription
- Plan
- Payment
- User authorization policy
- Media storage
- Device hardware state

---

# 12. Dependencies

| Domain | Relationship |
|---|---|
| Identity & Access | Participant reference + Authorization |
| Licensing | Entitlement validation برای قابلیت‌های plan-gated |
| Workflow | Action Contract |
| Event | انتشار Communication facts |
| Media | Reference برای Contact photo / media |
| Synchronization | انتقال state/events در صورت نیاز |

Communication به مدل داخلی Workflow یا Licensing وابسته نیست.

---

# 13. Priority Contact vs Emergency Recipient

این دو مفهوم رسماً از یکدیگر جدا هستند.

### Priority Contact

متعلق به Communication.

هدف:

> چه کسی باید برای سالمند در Hub سریع و ساده قابل تماس باشد؟

### Emergency Recipient

متعلق به Identity & Access.

هدف:

> چه User/Membershipهایی مجاز و انتخاب‌شده‌اند که هشدارهای مهم Elder را دریافت کنند؟

بنابراین:

`Priority Contact ≠ Emergency Recipient`

حتی اگر در برخی Use Caseها هر دو به یک شخص اشاره کنند.

---

# 14. Architectural Decisions — Frozen

1. Contact هویت مخاطب در تجربه Communication است، نه صرفاً شماره تلفن.

2. Contact photo از طریق Media Reference مدیریت می‌شود.

3. CommunicationSession مدل Participant-based دارد.

4. Initiator/Recipient با polymorphic type/id روی Session مدل نمی‌شوند.

5. CallAttempt حفظ می‌شود.

6. Session outcome از lifecycle ارتباط واقعی جدا و صریح است.

7. Communication Workflow Engine نیست.

8. Workflow می‌تواند از طریق Action Contract درخواست Communication ایجاد کند.

9. Communication مالک Session lifecycle باقی می‌ماند.

10. Retry/Escalation مراقبتی متعلق به Workflow است.

11. Communication برای قابلیت‌های plan-gated به Licensing وابسته است.

12. Domainها Entitlement را بررسی می‌کنند، نه Plan Name را.

13. Authorization متعلق به Identity & Access است.

14. Priority Contact و Emergency Recipient دو مفهوم مستقل هستند.

15. Contact دارای تاریخچه Hard Delete نمی‌شود.

16. Group Call و Communication Workflow پیچیده در MVP ساخته نمی‌شوند.

---

# Final Principle

> **Workflow decides when communication is needed.  
> Licensing decides whether the capability is available.  
> Identity decides who may use it.  
> Communication owns the actual session and its outcome.**