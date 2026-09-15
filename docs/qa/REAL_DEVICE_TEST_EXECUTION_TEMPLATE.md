# REAL_DEVICE_TEST_EXECUTION_TEMPLATE.md

# YARA Care OS — Real Device QA Execution Log

**Sprint:** Phase 3 — Sprint 2: Real Device Validation  
**Execution Date:** `YYYY-MM-DD`  
**QA Operator Name:** `HUMAN QA REQUIRED`  
**Overall Execution Result:** `PENDING / IN-PROGRESS / COMPLETED`  

---

## 1. Test Hardware & Environment Records

### Device A: Family Caregiver Mobile Device
- **Manufacturer & Model:** `HUMAN QA REQUIRED (e.g., Samsung Galaxy S23 / iPhone 14)`
- **Operating System & Version:** `HUMAN QA REQUIRED (e.g., Android 14 / One UI 6.1)`
- **Screen Size & Resolution:** `HUMAN QA REQUIRED (e.g., 6.1", 1080x2340)`
- **Family App Version / Build:** `0.1.0 (debug apk: apps/family/android/app/build/outputs/apk/debug/app-debug.apk)`
- **Configured Backend URL:** `http://192.168.1.101:8000/api/v1`
- **Network Connection:** `Wi-Fi / Cellular 4G / Intermittent`
- **Logged-in Caregiver Account:** `+989121111111`

### Device B: YARA Hub Dedicated Tablet
- **Manufacturer & Model:** `HUMAN QA REQUIRED (e.g., Lenovo Tab M10 / Samsung Galaxy Tab A8)`
- **Operating System & Version:** `HUMAN QA REQUIRED (e.g., Android 11 / API 30)`
- **Screen Size & Resolution:** `HUMAN QA REQUIRED (e.g., 10.1", 1920x1200)`
- **Hub APK Version / Build:** `2.0.0-foundation (debug apk: apps/hub/app/build/outputs/apk/debug/app-debug.apk)`
- **Configured Backend URL:** `http://192.168.1.101:8000/api/v1/`
- **Configured LiveKit URL:** `wss://yara-care-8qxaz9wd.livekit.cloud`
- **Assigned Elder Identity:** `Family Lab Elder`
- **Hardware Peripherals:** `Tablet Built-in Speaker, Microphone, Front Camera`

### Backend Workstation / Server Environment
- **Host IP & Port:** `192.168.1.101:8000`
- **Database Status:** `PostgreSQL 16 / Seeded with seed_family_lab`
- **Backend Test Status:** `419/419 passed (100% green)`

---

## 2. Test Execution Log Sheets

> **Instructions for Human QA Operator:**  
> - For each test case, mark **PASS**, **FAIL**, or **BLOCKED**.  
> - If an issue is observed, record the **Actual Result**, attach **Evidence** (screenshot, video, or logcat), and file a corresponding ticket in `REAL_DEVICE_BUG_REPORT_TEMPLATE.md`.

---

### Part 1: Family App Manual Test Cases

#### Category A: Authentication & Session
```text
Test ID: FAM-AUTH-01
Device: Device A (Caregiver Phone)
Build: Family App 0.1.0-debug
Environment: LAN Wi-Fi
Preconditions: App cleanly installed; backend running.
Steps:
  1. Open Family App.
  2. Input phone number: +989121111111
  3. Input password: familylab123
  4. Tap "ورود" (Login).
Expected Result: Navigates to Elder selection / Dashboard. JWT token stored securely.
Actual Result: [HUMAN QA TO FILL]
Status: [ PASS / FAIL / BLOCKED ]
Evidence: [ None / Screenshot filename ]
Notes:
```

```text
Test ID: FAM-AUTH-02
Device: Device A (Caregiver Phone)
Build: Family App 0.1.0-debug
Environment: LAN Wi-Fi
Preconditions: App on Login screen.
Steps:
  1. Enter phone: +989121111111
  2. Enter incorrect password: wrongpass123
  3. Tap Login.
Expected Result: Displays Persian error alert; remains on Login screen; no crash.
Actual Result: [HUMAN QA TO FILL]
Status: [ PASS / FAIL / BLOCKED ]
Evidence: [ None / Screenshot filename ]
Notes:
```

```text
Test ID: FAM-AUTH-03
Device: Device A (Caregiver Phone)
Build: Family App 0.1.0-debug
Environment: LAN Wi-Fi
Preconditions: User successfully authenticated and on Dashboard.
Steps:
  1. Swipe app away from recent apps (force-stop process).
  2. Relaunch app from app drawer.
Expected Result: App bypasses Login screen and immediately restores active session on Dashboard.
Actual Result: [HUMAN QA TO FILL]
Status: [ PASS / FAIL / BLOCKED ]
Evidence: [ None / Screenshot filename ]
Notes:
```

```text
Test ID: FAM-AUTH-04
Device: Device A (Caregiver Phone)
Build: Family App 0.1.0-debug
Environment: LAN Wi-Fi
Preconditions: User logged in.
Steps:
  1. Navigate to More/Settings tab.
  2. Tap "خروج از حساب کاربری" (Logout).
  3. Confirm logout.
Expected Result: Clears stored tokens; navigates to Login screen; Android hardware Back button does not return to authenticated screens.
Actual Result: [HUMAN QA TO FILL]
Status: [ PASS / FAIL / BLOCKED ]
Evidence: [ None / Screenshot filename ]
Notes:
```

```text
Test ID: FAM-AUTH-05
Device: Device A (Caregiver Phone)
Build: Family App 0.1.0-debug
Environment: LAN Wi-Fi
Preconditions: Active session running.
Steps:
  1. Allow access token to expire (or wait 60 minutes / simulate 401).
  2. Perform an action that requests data (e.g. pull-to-refresh on dashboard).
Expected Result: Client transparently calls /auth/token/refresh/; query succeeds without user logout.
Actual Result: [HUMAN QA TO FILL]
Status: [ PASS / FAIL / BLOCKED ]
Evidence: [ None / Logcat excerpt ]
Notes:
```

---

#### Category B: Elder Selection
```text
Test ID: FAM-ELD-01
Device: Device A
Build: Family App 0.1.0-debug
Preconditions: Logged in as +989121111111.
Steps: Observe home header upon login.
Expected Result: Automatically selects "Family Lab Elder" and displays elder name in Persian.
Actual Result: [HUMAN QA TO FILL]
Status: [ PASS / FAIL / BLOCKED ]
Notes:
```

---

#### Category C: Dashboard
```text
Test ID: FAM-DSH-01
Device: Device A
Build: Family App 0.1.0-debug
Preconditions: Elder selected, scheduled medication present.
Steps: Open Home tab.
Expected Result: Renders calmness status, upcoming dose cards, device connectivity status, and last update timestamp without flicker.
Actual Result: [HUMAN QA TO FILL]
Status: [ PASS / FAIL / BLOCKED ]
Notes:
```

```text
Test ID: FAM-DSH-02
Device: Device A
Build: Family App 0.1.0-debug
Preconditions: On Dashboard.
Steps: Perform pull-to-refresh gesture.
Expected Result: Spinner displays; refetches all queries; updates timestamp smoothly.
Actual Result: [HUMAN QA TO FILL]
Status: [ PASS / FAIL / BLOCKED ]
Notes:
```

```text
Test ID: FAM-DSH-03
Device: Device A
Build: Family App 0.1.0-debug
Preconditions: Occurrence skipped on Program screen.
Steps: Return to Home Dashboard.
Expected Result: Skipped occurrence does NOT show on today's list and does NOT trigger false urgent or attention tones.
Actual Result: [HUMAN QA TO FILL]
Status: [ PASS / FAIL / BLOCKED ]
Notes:
```

---

#### Category D: Two-Way Messaging Subsystem
```text
Test ID: FAM-MSG-01
Device: Device A
Build: Family App 0.1.0-debug
Steps:
  1. Open Messages tab.
  2. Type Persian text: "سلام مادر جان، قرصت رو خوردی؟"
  3. Tap Send.
Expected Result: Message renders optimistically at bottom as PENDING; updates to SENT within 2s.
Actual Result: [HUMAN QA TO FILL]
Status: [ PASS / FAIL / BLOCKED ]
Notes:
```

```text
Test ID: FAM-MSG-02
Device: Device A
Build: Family App 0.1.0-debug
Steps:
  1. Observe message bubble list with multiple historical messages.
  2. Send consecutive text messages.
Expected Result: Chronological ascending order (oldest top, newest bottom); messages NEVER jump to top on 3s background refetch.
Actual Result: [HUMAN QA TO FILL]
Status: [ PASS / FAIL / BLOCKED ]
Notes:
```

```text
Test ID: FAM-MSG-03
Device: Device A + Device B
Build: Family App 0.1.0-debug + Hub 2.0.0-debug
Steps:
  1. Send message from Family App.
  2. Hub downloads message.
  3. Elder opens message on Hub.
Expected Result: Family App bubble status transitions: PENDING -> SENT -> DELIVERED (✓✓ تحویل به هاب) -> READ (✓✓ خوانده شده).
Actual Result: [HUMAN QA TO FILL]
Status: [ PASS / FAIL / BLOCKED ]
Notes:
```

```text
Test ID: FAM-MSG-04
Device: Device A
Build: Family App 0.1.0-debug
Steps:
  1. Turn Phone Airplane Mode ON.
  2. Type and send a message.
  3. Observe FAILED status.
  4. Turn Airplane Mode OFF.
  5. Tap "تلاش دوباره" (Retry) on bubble.
Expected Result: Message shows "⚠ ارسال ناموفق (تلاش دوباره)". Tapping retry re-sends and successfully transitions to SENT.
Actual Result: [HUMAN QA TO FILL]
Status: [ PASS / FAIL / BLOCKED ]
Notes:
```

```text
Test ID: FAM-MSG-05
Device: Device A
Build: Family App 0.1.0-debug
Steps:
  1. Tap microphone button.
  2. Grant microphone permission if prompted.
  3. Record 5 seconds of audio.
  4. Tap Stop & Send.
Expected Result: Uploads voice note; bubble displays duration "۵ ثانیه" with play button.
Actual Result: [HUMAN QA TO FILL]
Status: [ PASS / FAIL / BLOCKED ]
Notes:
```

```text
Test ID: FAM-MSG-06
Device: Device A
Build: Family App 0.1.0-debug
Steps: Tap Play button on incoming voice message from Hub.
Expected Result: Audio plays through speaker/earpiece; progress indicator updates; stops at finish.
Actual Result: [HUMAN QA TO FILL]
Status: [ PASS / FAIL / BLOCKED ]
Notes:
```

```text
Test ID: FAM-MSG-07
Device: Device A
Build: Family App 0.1.0-debug
Steps: Tap photo attachment; select image from phone gallery; send.
Expected Result: Uploads image; renders image preview thumbnail in chat bubble.
Actual Result: [HUMAN QA TO FILL]
Status: [ PASS / FAIL / BLOCKED ]
Notes:
```

---

#### Category E: Medication & Scheduling
```text
Test ID: FAM-MED-01
Device: Device A
Build: Family App 0.1.0-debug
Steps: Navigate to Program tab.
Expected Result: Displays active medication list with Persian titles, clock times, and dosages.
Actual Result: [HUMAN QA TO FILL]
Status: [ PASS / FAIL / BLOCKED ]
Notes:
```

```text
Test ID: FAM-MED-02
Device: Device A + Device B
Build: Family App 0.1.0-debug + Hub 2.0.0-debug
Steps:
  1. Select an occurrence on Program screen.
  2. Select Reschedule Once.
  3. Input time: 20:30.
  4. Tap Confirm.
Expected Result: Replacement time computed in Asia/Tehran timezone (+03:30). Dose reflects exactly 20:30 on Hub tablet schedule.
Actual Result: [HUMAN QA TO FILL]
Status: [ PASS / FAIL / BLOCKED ]
Notes:
```

---

#### Category F: Calling (LiveKit)
```text
Test ID: FAM-CAL-01
Device: Device A + Device B
Steps:
  1. Tap Call tab on Family App.
  2. Select Hub contact and tap Video Call.
  3. Elder on Hub taps Answer.
Expected Result: Both devices connect to LiveKit room; bidirectional audio and video are active, synchronized, and low-latency (<500ms).
Actual Result: [HUMAN QA TO FILL]
Status: [ PASS / FAIL / BLOCKED ]
Notes:
```

```text
Test ID: FAM-CAL-02
Device: Device A
Steps: During active video call, tap Mute Mic, Camera Flip, and Camera Off.
Expected Result: Controls respond immediately; Hub receives corresponding mute/track events without crash.
Actual Result: [HUMAN QA TO FILL]
Status: [ PASS / FAIL / BLOCKED ]
Notes:
```

```text
Test ID: FAM-CAL-03
Device: Device A
Steps: Tap End Call (red button).
Expected Result: LiveKit room disconnects cleanly; releases camera/mic hardware locks; returns to Call tab.
Actual Result: [HUMAN QA TO FILL]
Status: [ PASS / FAIL / BLOCKED ]
Notes:
```

---

#### Category G: Subscription / Checkout
```text
Test ID: FAM-SUB-01
Device: Device A
Steps: Navigate to More -> Subscription.
Expected Result: Displays current Plan (PREMIUM), active status, and Persian expiration date.
Actual Result: [HUMAN QA TO FILL]
Status: [ PASS / FAIL / BLOCKED ]
Notes:
```

```text
Test ID: FAM-SUB-02
Device: Device A
Steps:
  1. Select Renew / Change Plan.
  2. Tap Review Order.
  3. Proceed to Payment.
  4. Cancel on browser gateway and return to app.
Expected Result: App resumes cleanly; license remains unchanged; app NEVER calls /payments/verify/.
Actual Result: [HUMAN QA TO FILL]
Status: [ PASS / FAIL / BLOCKED ]
Notes:
```

---

### Part 2: Android Hub Manual Test Cases

#### Category A: Boot & Reliability
```text
Test ID: HUB-BOT-01
Device: Device B (Tablet)
Build: Hub 2.0.0-debug
Steps: Power on tablet from off state; open YARA Hub app.
Expected Result: Injections and Room DB load within 3 seconds; ambient Home screen renders with Persian clock and elder greeting.
Actual Result: [HUMAN QA TO FILL]
Status: [ PASS / FAIL / BLOCKED ]
Notes:
```

```text
Test ID: HUB-BOT-02
Device: Device B (Tablet)
Steps: Force close app via Settings or adb shell am force-stop ir.sayda.yara.hub; relaunch.
Expected Result: App launches immediately into previous state; no database locked or Room corruption errors.
Actual Result: [HUMAN QA TO FILL]
Status: [ PASS / FAIL / BLOCKED ]
Notes:
```

---

#### Category B: Dashboard & Touch Usability
```text
Test ID: HUB-DSH-01
Device: Device B
Steps: Inspect Home screen layout and typography.
Expected Result: Clear RTL layout; large Persian typography (Vazirmatn); minimum 48dp touch targets; zero confusing sub-menus.
Actual Result: [HUMAN QA TO FILL]
Status: [ PASS / FAIL / BLOCKED ]
Notes:
```

---

#### Category C: Medication & Reminder Engine (Offline Invariant)
```text
Test ID: HUB-REM-01
Device: Device B
Steps: Wait for scheduled medication clock time (e.g. 14:00).
Expected Result: Full-screen reminder dialog takes foreground; gentle audio chime plays; displays medication image and Persian name.
Actual Result: [HUMAN QA TO FILL]
Status: [ PASS / FAIL / BLOCKED ]
Notes:
```

```text
Test ID: HUB-REM-02
Device: Device B
Steps: Tap large green button "دارو را خوردم" (Taken).
Expected Result: Chime stops; records MEDICATION_TAKEN; dialog closes; card retained for 15 minutes with green checkmark.
Actual Result: [HUMAN QA TO FILL]
Status: [ PASS / FAIL / BLOCKED ]
Notes:
```

```text
Test ID: HUB-REM-03
Device: Device B
Steps: Tap yellow button "۱۰ دقیقه دیگر یادآوری کن" (Postpone 10 min).
Expected Result: Dialog dismisses; local alarm reschedules exactly 10 minutes later; re-fires at designated time.
Actual Result: [HUMAN QA TO FILL]
Status: [ PASS / FAIL / BLOCKED ]
Notes:
```

```text
Test ID: HUB-REM-04
Device: Device B
Steps:
  1. Complete or postpone a reminder.
  2. Return to Home screen.
  3. Rotate tablet or put app in background and resume.
Expected Result: Does NOT re-trigger the completed reminder (Sprint 1 navigation leak fix verified).
Actual Result: [HUMAN QA TO FILL]
Status: [ PASS / FAIL / BLOCKED ]
Notes:
```

```text
Test ID: HUB-REM-05 (CRITICAL OFFLINE INVARIANT)
Device: Device B
Steps:
  1. Turn tablet Wi-Fi OFF (Flight Mode).
  2. Wait for scheduled medication time.
  3. Confirm dose when reminder fires.
Expected Result: Reminder fires completely offline without internet; audio chime plays; confirmation is saved into local SQLite outbox.
Actual Result: [HUMAN QA TO FILL]
Status: [ PASS / FAIL / BLOCKED ]
Notes:
```

---

#### Category D: Hub Messaging
```text
Test ID: HUB-MSG-01
Device: Device B
Steps: Send message from Family App while Hub is on Home screen.
Expected Result: Hub receives message within 3s; gentle chime sounds; unread badge appears on Messages icon.
Actual Result: [HUMAN QA TO FILL]
Status: [ PASS / FAIL / BLOCKED ]
Notes:
```

```text
Test ID: HUB-MSG-02
Device: Device B
Steps: Tap incoming message to view full screen.
Expected Result: Opens message card; unread badge clears immediately; read receipt sent to backend.
Actual Result: [HUMAN QA TO FILL]
Status: [ PASS / FAIL / BLOCKED ]
Notes:
```

---

#### Category E: Hub Video/Audio Calling
```text
Test ID: HUB-CAL-01
Device: Device B
Steps: Initiate video call from Family App to Hub.
Expected Result: Hub tablet screen displays incoming call view; rings with gentle Iranian ringer; shows caller photo and name ("دختر").
Actual Result: [HUMAN QA TO FILL]
Status: [ PASS / FAIL / BLOCKED ]
Notes:
```

```text
Test ID: HUB-CAL-02
Device: Device B
Steps: Tap large green "پاسخ" (Answer) button.
Expected Result: Ringer stops; LiveKit room connects; full-screen video renders caregiver; two-way audio stream connects.
Actual Result: [HUMAN QA TO FILL]
Status: [ PASS / FAIL / BLOCKED ]
Notes:
```

```text
Test ID: HUB-CAL-03
Device: Device B
Steps: Tap red "رد تماس" (Decline) button during incoming call.
Expected Result: Ringer stops immediately; returns cleanly to ambient Home screen; Family App shows call declined.
Actual Result: [HUMAN QA TO FILL]
Status: [ PASS / FAIL / BLOCKED ]
Notes:
```

---

#### Category F: Hub Sync & Offline Recovery
```text
Test ID: HUB-SNC-01
Device: Device B
Steps: Inspect SQLite database via adb or observe sync logs during normal operation.
Expected Result: Monotonic checkpoints advance cleanly; no duplicate entries in database.
Actual Result: [HUMAN QA TO FILL]
Status: [ PASS / FAIL / BLOCKED ]
Notes:
```

```text
Test ID: HUB-SNC-02 (CRITICAL SYNC DRAIN)
Device: Device B + Device A
Steps:
  1. Turn tablet Wi-Fi OFF for 2 hours.
  2. Confirm 2 medication reminders offline.
  3. Turn tablet Wi-Fi back ON.
  4. Wait 30 seconds.
  5. Check Family App Dashboard.
Expected Result: Hub sync session drains outbox evidence to backend; backend records completions; Family App updates doses to COMPLETED.
Actual Result: [HUMAN QA TO FILL]
Status: [ PASS / FAIL / BLOCKED ]
Notes:
```

---

## 3. Execution Summary Statistics (To be filled upon completion)

| Category | Total Tests | Passed | Failed | Blocked |
| :--- | :--- | :--- | :--- | :--- |
| **Family App Auth & Session** | 5 | - | - | - |
| **Family App Elder & Nav** | 3 | - | - | - |
| **Family App Dashboard** | 4 | - | - | - |
| **Family App Messaging** | 8 | - | - | - |
| **Family App Medication** | 4 | - | - | - |
| **Family App Calling** | 5 | - | - | - |
| **Family App Subscription** | 4 | - | - | - |
| **Family App Lifecycle** | 3 | - | - | - |
| **Hub Boot & Reliability** | 3 | - | - | - |
| **Hub Dashboard & Usability** | 3 | - | - | - |
| **Hub Reminders (Offline)** | 5 | - | - | - |
| **Hub Messaging** | 4 | - | - | - |
| **Hub Calling** | 4 | - | - | - |
| **Hub Sync & Recovery** | 3 | - | - | - |
| **TOTAL** | **58** | **-** | **-** | **-** |

**QA Sign-off Signature:** `______________________`  
**Date:** `YYYY-MM-DD`  
