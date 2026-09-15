# REAL_DEVICE_BUG_REPORT_TEMPLATE.md

# YARA Care OS — Standardized Real-Device Bug Report Template

**Sprint:** Phase 3 — Sprint 2: Real Device Validation  
**Target:** Physical Device Testing (Family App / Hub / Integration)  

---

## 1. Severity Definitions

| Severity Level | Impact Definition | Examples |
| :--- | :--- | :--- |
| **P0 — BLOCKER** | System completely unusable, data corruption, physical safety risk, or core MVP invariant violated. | App crashes on launch; Hub cannot boot; scheduled medication reminder fails to fire offline; incorrect subscription billing; security/auth bypass. |
| **P1 — CRITICAL** | Major MVP workflow fundamentally broken with no viable workaround. | Messaging fails to send or receive; audio/video calling unusable; medication cannot be confirmed; offline sync permanently fails to drain. |
| **P2 — MAJOR** | Important feature functions with significant defects, intermittent failures, or poor recovery. | Occasional audio glitch during call; retry button requires multiple taps; pull-to-refresh lags significantly; non-blocking layout overflow. |
| **P3 — MINOR** | Cosmetic, wording, or minor visual inconsistency that does not impair function. | Typo in Persian translation; slight icon misalignment; minor contrast mismatch in secondary text. |

---

## 2. QA Boundary & Reporting Philosophy

> [!IMPORTANT]
> **Human QA Boundary Rule:**  
> The QA Operator's primary responsibility is to report **WHAT** happened, **WHEN** it happened, and on **WHICH DEVICE**, accompanied by objective evidence.  
> The QA Operator is **NOT** required or expected to diagnose the root cause, inspect backend source code, or propose software architecture fixes. The engineering team will triage and resolve the root cause.

---

## 3. Standardized Bug Report Form

```text
================================================================================
YARA CARE OS BUG REPORT
================================================================================

BUG-ID: BUG-P3S2-00X (e.g. BUG-P3S2-001)

Title: [Concise summary describing the observed defect, e.g. "Voice message playback freezes on physical tablet"]

Severity: [ P0 - BLOCKER | P1 - CRITICAL | P2 - MAJOR | P3 - MINOR ]

Component: [ Family App | Android Hub | Backend | Integration / Network ]

Device: [ Device A (Caregiver Phone) | Device B (Hub Tablet) | Cross-Device ]
  - Make & Model: [e.g. Samsung Galaxy Tab A8 10.5" / iPhone 13]
  - OS & Version: [e.g. Android 13 / One UI 5.0]
  - Screen Resolution: [e.g. 1920x1200]

Build Identifier:
  - App Version: [e.g. Family App 0.1.0-debug / Hub 2.0.0-debug]
  - Git Commit / Hash: [e.g. master @ HEAD]

Environment:
  - Backend URL: [e.g. http://192.168.1.101:8000/api/v1/]
  - LiveKit URL: [e.g. wss://yara-care-8qxaz9wd.livekit.cloud]
  - Test Account: [e.g. +989121111111]
  - Elder Profile: [e.g. Family Lab Elder]

Network Condition:
  - [ ] Online (High-Speed Local Wi-Fi)
  - [ ] Cellular Data (4G/LTE)
  - [ ] Offline (Airplane Mode / Wi-Fi Disabled)
  - [ ] Intermittent / High-Latency (500ms+ lag)

Preconditions:
  1. [List any required prior state, e.g. "User is logged in on Family App; Hub has 1 pending dose at 14:00"]
  2. [...]

Steps to Reproduce:
  1. [Exact physical user action, e.g. "Tap on 'پیام‌ها' (Messages) in bottom bar"]
  2. [Next action, e.g. "Record 10 seconds of voice audio and tap Send"]
  3. [Next action, e.g. "Observe Hub tablet screen for incoming notification"]
  4. [...]

Expected Result:
  [What should have occurred according to the specification and test plan]
  (e.g., "Hub receives voice message within 3 seconds, plays notification chime, and shows unread badge.")

Actual Result:
  [What actually occurred on the physical hardware]
  (e.g., "Hub does not display notification; unread badge does not appear until app is manually killed and restarted.")

Frequency of Occurrence:
  - [ ] Always (100% of attempts)
  - [ ] Often (~75% of attempts)
  - [ ] Intermittent (~25-50% of attempts)
  - [ ] Once (Isolated occurrence)

Reproducibility:
  - Total Attempts: [e.g. 5]
  - Total Reproductions: [e.g. 5]

Evidence Attached:
  - [ ] Screenshot (Name/Path: docs/qa/evidence/...)
  - [ ] Screen Recording / Video (Name/Path: docs/qa/evidence/...)
  - [ ] Photo of Physical Device Screen (Name/Path: docs/qa/evidence/...)
  - [ ] Logcat Dump (Name/Path: docs/qa/evidence/...)
  - [ ] Timestamp of event: [e.g. 2026-09-09 14:32:15 Tehran Time]

Suspected Layer (QA Best Guess - Optional):
  - [ ] UI / Display Layout
  - [ ] Client Application Logic
  - [ ] Sync Runtime / Local DB
  - [ ] Backend API / Database
  - [ ] Network / LiveKit Transport
  - [ ] Physical Hardware / OS Limitation
  - [ ] Unknown

Additional Observations & Notes:
  [Any extra context, device temperature, battery state, or peripheral connections]

================================================================================
```

---

## 4. Example Filled Bug Report (Reference)

```text
================================================================================
YARA CARE OS BUG REPORT (SAMPLE)
================================================================================

BUG-ID: BUG-P3S2-SAMPLE-01

Title: Hub audio chime plays through earpiece instead of loud speaker during offline reminder

Severity: P1 - CRITICAL

Component: Android Hub

Device: Device B (Hub Tablet)
  - Make & Model: Lenovo Tab M10 FHD Plus
  - OS & Version: Android 10 (API 29)
  - Screen Resolution: 1920x1200

Build Identifier:
  - App Version: Hub 2.0.0-foundation (app-debug.apk)
  - Git Commit / Hash: master

Environment:
  - Backend URL: http://192.168.1.101:8000/api/v1/
  - LiveKit URL: wss://yara-care-8qxaz9wd.livekit.cloud
  - Test Account: +989121111111
  - Elder Profile: Family Lab Elder

Network Condition:
  - [x] Offline (Airplane Mode / Wi-Fi Disabled)

Preconditions:
  1. Tablet has Wi-Fi turned off.
  2. Scheduled dose exists at 15:00.

Steps to Reproduce:
  1. Wait for clock to reach 15:00.
  2. Observe reminder audio output when dialog appears.

Expected Result:
  Audio chime plays at high volume through tablet dual stereo speakers to alert the elder in the room.

Actual Result:
  Audio chime is very faint and routes only through the top call speaker/earpiece channel, making it inaudible from across the room.

Frequency of Occurrence:
  - [x] Always (100% of attempts)

Reproducibility:
  - Total Attempts: 3
  - Total Reproductions: 3

Evidence Attached:
  - [x] Video recording: docs/qa/evidence/VID_20260909_150012.mp4
  - [x] Logcat dump: docs/qa/evidence/logcat_audio_route.txt
  - [x] Timestamp: 2026-09-09 15:00:05 +03:30

Suspected Layer:
  - [x] Client Application Logic / AudioTrack routing

Additional Observations & Notes:
  Tablet media volume was set to 100%, but stream type seems to be STREAM_VOICE_CALL instead of STREAM_ALARM or STREAM_MUSIC.
================================================================================
```
