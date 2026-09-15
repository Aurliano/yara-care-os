# REAL_DEVICE_TEST_PLAN.md

# YARA Care OS — Phase 3 / Sprint 2: Real Device Validation

**Version:** 1.0  
**Status:** Approved for QA Execution  
**Author:** QA Preparation Engineer & Technical Validation Lead  
**Last Updated:** 2026-09-09  

---

## 1. Scope & Objective

This document defines the physical real-device validation test plan for **YARA Care OS Phase 3 — Sprint 2**.

### 1.1 Non-Negotiable Operational Boundaries
- **No Feature Development:** This sprint strictly prepares and executes real-device validation of the existing MVP.
- **Physical Device Exclusivity:** Automated tests and Android emulators do **NOT** constitute physical real-device validation. Every test case in this plan must be physically executed by a human QA operator on actual hardware.
- **Phase 2 Boundary:** Licensing & Billing architecture is closed. Family App must never call `/payments/verify/`.
- **Kiosk Mode Boundary:** Device Owner / LockTask mode is deferred to Production Readiness; Hub is validated as a full-screen dedicated foreground application.
- **Notification Boundary:** Push Notifications (FCM/APNs) are deferred to Phase 4. Active notification is verified via Hub ringer/audio alarms, in-app alerts (ADR-015), and foreground pollers.

---

## 2. Test Environments & Topology

```text
┌──────────────────────────────────────┐          ┌──────────────────────────────────────┐
│       DEVICE A: Physical Phone       │          │       DEVICE B: Physical Tablet      │
│         (Family Caregiver App)       │          │           (YARA Elder Hub)           │
│   IP: 192.168.1.X / Cellular 4G/LTE  │          │      IP: 192.168.1.Y (Wi-Fi Only)    │
└──────────────────┬───────────────────┘          └──────────────────┬───────────────────┘
                   │                                                 │
                   │    HTTP REST / Bearer JWT (Port 8000)           │  HTTP REST / Sync Sessions / Checkpoints
                   │    Two-Way Messaging / LiveKit Tokens           │  Monotonic Checkpoints (Port 8000)
                   ▼                                                 ▼
        ┌───────────────────────────────────────────────────────────────────┐
        │                     LOCAL LAB / STAGING BACKEND                   │
        │             Host: 192.168.1.101:8000 (Django / PostgreSQL)        │
        │                  Pre-seeded via: seed_family_lab                  │
        └─────────────────────────────────┬─────────────────────────────────┘
                                          │  Direct Media Tracks
                                          │  WebRTC (Audio/Video)
                                          ▼
                        ┌───────────────────────────────────┐
                        │      LIVEKIT CLOUD WEBRTC         │
                        │ wss://yara-care-8qxaz9wd.livekit  │
                        └───────────────────────────────────┘
```

### 2.1 Network Configurations Under Test
1. **LAN Wi-Fi (Normal):** Both devices connected to local Wi-Fi with route to `http://192.168.1.101:8000/api/v1/`.
2. **Heterogeneous Network:** Family App on Cellular Data (4G/5G) via public IP/ngrok or staging domain, Hub on Home Wi-Fi.
3. **Degraded / High Latency:** Simulated 500ms+ latency and 5% packet loss (simulating rural Iranian telecom conditions).
4. **Air-Gapped / Zero Connectivity:** Device Wi-Fi and Cellular toggled OFF (Flight Mode) during Hub execution to validate offline-first invariants.

---

## 3. Physical Device Target Specifications

### Target A: Caregiver Mobile Device (Family App)
- **Role:** Family Caregiver thin client.
- **Physical Hardware:** `HUMAN QA REQUIRED` (Record: Make, Model, OS version).
- **Minimum OS:** Android 10+ (API 29+) or iOS 15+.
- **Installed Artifact:** `apps/family/android/app/build/outputs/apk/debug/app-debug.apk` (Package: `ir.sayda.yara.family`).
- **Environment Variable:** `EXPO_PUBLIC_API_BASE_URL=http://192.168.1.101:8000/api/v1`.
- **Pre-Configured Credentials:**
  - Phone: `+989121111111`
  - Password: `familylab123`
  - Elder ID: `Family Lab Elder`

### Target B: YARA Hub Dedicated Tablet
- **Role:** Dedicated elderly companion appliance, local execution engine, and offline reminder coordinator.
- **Physical Hardware:** `HUMAN QA REQUIRED` (Record: Make, Model, Screen size, Resolution).
- **Minimum OS:** Android 7.0+ (API 24+) tablet (Recommended: 8" or 10" display).
- **Installed Artifact:** `apps/hub/app/build/outputs/apk/debug/app-debug.apk` (Package: `ir.sayda.yara.hub`).
- **Build Configuration:** Configured via `apps/hub/local.properties`:
  - `hub.backend.url=http://192.168.1.101:8000/api/v1/`
  - `hub.provision.phone=+989121111111`
  - `hub.provision.password=familylab123`
  - `hub.livekit.url=wss://yara-care-8qxaz9wd.livekit.cloud`

---

## 4. Test Preconditions & Lab Setup

1. **Backend Database Seeding:**
   Run from repository root:
   ```bash
   python manage.py seed_family_lab
   ```
   This guarantees:
   - Primary Caregiver created: `+989121111111` (`familylab123`).
   - Elder created: `Family Lab Elder` with active `PREMIUM` subscription.
   - Hub device provisioned and mapped to `Family Lab Elder`.
   - Priority Contact created: `دختر` mapped to caregiver.
   - Medication reminder workflow active.

2. **Backend Server Execution:**
   Start server listening on all network interfaces:
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```
   Ensure workstation firewall allows inbound TCP on port 8000 from local subnet `192.168.1.0/24`.

3. **Device Installation:**
   - Connect Family Device via USB:
     ```bash
     adb -s <DEVICE_A_ID> install -r apps/family/android/app/build/outputs/apk/debug/app-debug.apk
     ```
   - Connect Hub Tablet via USB:
     ```bash
     adb -s <DEVICE_B_ID> install -r apps/hub/app/build/outputs/apk/debug/app-debug.apk
     ```

---

## 5. Family App Test Matrix (Physical Device)

### Category A: Authentication & Session Handling
| Test ID | Test Scenario | Steps | Expected Result | Execution |
| :--- | :--- | :--- | :--- | :--- |
| **FAM-AUTH-01** | Valid Caregiver Login | 1. Launch app.<br>2. Enter `+989121111111` and `familylab123`.<br>3. Press Login. | Authenticates successfully, stores JWT in secure storage, navigates to Elder selection / Dashboard. | `HUMAN QA REQUIRED` |
| **FAM-AUTH-02** | Invalid Password Rejection | 1. Enter `+989121111111` and `wrongpassword`.<br>2. Press Login. | Displays Persian error message ("نام کاربری یا رمز عبور اشتباه است"), remains on login screen. | `HUMAN QA REQUIRED` |
| **FAM-AUTH-03** | Session Persistence across Process Kill | 1. Log in successfully.<br>2. Swipe app away from recent apps (force stop).<br>3. Relaunch app. | Bypasses login screen directly into active session without asking for credentials. | `HUMAN QA REQUIRED` |
| **FAM-AUTH-04** | Explicit Logout | 1. Navigate to More/Settings tab.<br>2. Tap Logout.<br>3. Confirm modal. | Tokens cleared from secure storage, returns to Login screen. Back navigation cannot return to authenticated screens. | `HUMAN QA REQUIRED` |
| **FAM-AUTH-05** | Token Expiry & Automatic Refresh | 1. With active session, trigger backend refresh token expiry or advance device clock.<br>2. Perform API request. | Transparently calls `/auth/token/refresh/` using refresh token; request succeeds without user logout. | `HUMAN QA REQUIRED` |

### Category B: Elder Selection & Access Control
| Test ID | Test Scenario | Steps | Expected Result | Execution |
| :--- | :--- | :--- | :--- | :--- |
| **FAM-ELD-01** | Auto-selection of Elder | Log in with user having single elder membership. | Automatically selects `Family Lab Elder` and loads dashboard. | `HUMAN QA REQUIRED` |
| **FAM-ELD-02** | Multi-Elder Switcher | 1. Seed second elder on account.<br>2. Open elder selector in top bar.<br>3. Select second elder. | Dashboard, medication, and messaging immediately switch context and refetch data for the selected elder. | `HUMAN QA REQUIRED` |
| **FAM-ELD-03** | Permission Enforcement | Log in as caregiver with `VIEWER` role (read-only). | Medication edit buttons and message composer input are hidden or disabled; viewer cannot modify prescriptions. | `HUMAN QA REQUIRED` |

### Category C: Dashboard Integrity
| Test ID | Test Scenario | Steps | Expected Result | Execution |
| :--- | :--- | :--- | :--- | :--- |
| **FAM-DSH-01** | Initial Dashboard Load | Launch app with active elder. | Displays elder name, calmness indicator tone (`calm`), today's upcoming medication cards, and hub connectivity. | `HUMAN QA REQUIRED` |
| **FAM-DSH-02** | Pull-to-Refresh | Swipe down on dashboard screen. | Spinner activates, refetches elder status, occurrences, and devices; updates timestamp without layout jitter. | `HUMAN QA REQUIRED` |
| **FAM-DSH-03** | Skipped/Cancelled Occurrence Filtering | 1. Skip a scheduled dose on backend/program.<br>2. View Dashboard. | Skipped dose does **NOT** appear in Today's list and does **NOT** trigger false `urgent` or `attention` tone. | `HUMAN QA REQUIRED` |
| **FAM-DSH-04** | Attention Tone on Due Dose | Schedule dose due in current hour without completion. | Dashboard status tone transitions to `attention` and shows Due badge. | `HUMAN QA REQUIRED` |

### Category D: Two-Way Messaging Subsystem
| Test ID | Test Scenario | Steps | Expected Result | Execution |
| :--- | :--- | :--- | :--- | :--- |
| **FAM-MSG-01** | Send Text Message | 1. Open Messages tab.<br>2. Type "سلام، قرصت رو خوردی؟".<br>3. Tap Send. | Message appears immediately with `PENDING` (در حال ارسال), then transitions to `SENT` (✓ ارسال شد) within 2s. | `HUMAN QA REQUIRED` |
| **FAM-MSG-02** | Message Chronological Ordering | 1. Observe message list with multiple entries.<br>2. Send consecutive messages. | Oldest messages are at the top, newest messages at the bottom. Messages never jump position during background poll. | `HUMAN QA REQUIRED` |
| **FAM-MSG-03** | Delivery & Read Receipts | 1. Send message from Family App.<br>2. Hub connects and downloads message.<br>3. Elder opens message on Hub. | Status changes to `DELIVERED` (✓✓ تحویل به هاب), then to `READ` (✓✓ خوانده شده) in blue text on Family App. | `HUMAN QA REQUIRED` |
| **FAM-MSG-04** | Failed Send & Retry Affordance | 1. Toggle Airplane Mode ON.<br>2. Type message and tap Send.<br>3. Wait 5s.<br>4. Toggle Airplane Mode OFF.<br>5. Tap retry button. | Shows `⚠ ارسال ناموفق (تلاش دوباره)`. Tapping retry immediately re-attempts transmission and updates status to `SENT`. | `HUMAN QA REQUIRED` |
| **FAM-MSG-05** | Send Voice Note | 1. Tap microphone icon.<br>2. Speak for 5 seconds.<br>3. Tap Stop & Send. | Uploads audio recording (`.m4a`), renders voice bubble with play button and duration (۵ ثانیه). | `HUMAN QA REQUIRED` |
| **FAM-MSG-06** | Voice Note Playback | Tap Play button on incoming voice message. | Audio plays clearly through device earpiece/speaker, progress animates, stops at end. | `HUMAN QA REQUIRED` |
| **FAM-MSG-07** | Send Photo Attachment | 1. Tap photo attachment icon.<br>2. Select image from device gallery.<br>3. Send. | Uploads media attachment, displays image thumbnail preview in chat bubble. | `HUMAN QA REQUIRED` |
| **FAM-MSG-08** | Virtual Keyboard Behavior | Tap text input field in Messages. | Keyboard opens smoothly; scroll view automatically scrolls to bottom without covering input field. | `HUMAN QA REQUIRED` |

### Category E: Medication & Scheduling Subsystem
| Test ID | Test Scenario | Steps | Expected Result | Execution |
| :--- | :--- | :--- | :--- | :--- |
| **FAM-MED-01** | View Medication Regimen | Navigate to Program/Medication tab. | Lists active prescriptions with Persian titles, dosages, scheduled clock times, and instructions. | `HUMAN QA REQUIRED` |
| **FAM-MED-02** | One-Time Reschedule (Tehran Timezone Safety) | 1. Select upcoming occurrence.<br>2. Choose Reschedule Once.<br>3. Enter 21:30.<br>4. Confirm. | Sends replacement time in `Asia/Tehran` offset (`+03:30`). Verification on Hub reflects exactly 21:30 Tehran time regardless of phone's local time zone. | `HUMAN QA REQUIRED` |
| **FAM-MED-03** | Skip Single Occurrence | 1. Select occurrence.<br>2. Choose Skip Once.<br>3. Confirm. | Occurrence marked `SKIPPED`. Card displays skipped status on Program tab and is removed from Dashboard. | `HUMAN QA REQUIRED` |
| **FAM-MED-04** | End Care Activity | 1. Select activity.<br>2. Tap End Program.<br>3. Confirm dialog. | Activity status transitions to `ENDED`; future occurrences are purged from schedule. | `HUMAN QA REQUIRED` |

### Category F: Real-Time Audio/Video Calling (LiveKit)
| Test ID | Test Scenario | Steps | Expected Result | Execution |
| :--- | :--- | :--- | :--- | :--- |
| **FAM-CAL-01** | Outgoing Video Call Initiation | 1. Navigate to Call tab.<br>2. Select Hub contact.<br>3. Tap Video Call. | Requests camera/mic permissions if not granted; connects to LiveKit room; displays local preview and "در حال برقراری تماس...". | `HUMAN QA REQUIRED` |
| **FAM-CAL-02** | Two-Way Media Stream | Hub accepts the call. | Remote video stream from Hub tablet renders smoothly; bidirectional two-way audio is clear without echo or distortion. | `HUMAN QA REQUIRED` |
| **FAM-CAL-03** | Call Controls (Mute/Camera Flip) | 1. Tap Mute Microphone.<br>2. Tap Flip Camera.<br>3. Tap Camera OFF. | Audio mutes on Hub; camera switches to rear lens; video stream pauses appropriately. | `HUMAN QA REQUIRED` |
| **FAM-CAL-04** | End Call by Caregiver | Tap End Call button (red). | Call terminates, LiveKit room disconnects, audio stops, UI returns cleanly to Call tab. | `HUMAN QA REQUIRED` |
| **FAM-CAL-05** | Remote Termination by Hub | Hub ends the call while active. | Family App detects remote disconnect within 2 seconds, displays call ended banner, returns to Call tab. | `HUMAN QA REQUIRED` |

### Category G: Subscription & Payment Checkout
| Test ID | Test Scenario | Steps | Expected Result | Execution |
| :--- | :--- | :--- | :--- | :--- |
| **FAM-SUB-01** | View Active Subscription | Navigate to More -> Subscription. | Displays current plan code (`PREMIUM`), active status, expiration date in Persian solar calendar. | `HUMAN QA REQUIRED` |
| **FAM-SUB-02** | Two-Step Checkout Initiation | 1. Select Renewal or Plan upgrade.<br>2. Tap Review Order. | Calls `/payments/checkout/` on backend; receives server-authoritative price and invoice details; does NOT calculate price locally. | `HUMAN QA REQUIRED` |
| **FAM-SUB-03** | Gateway Launch & Cancellation | 1. Tap Proceed to Payment.<br>2. Web browser launches ZarinPal gateway.<br>3. Cancel payment and return to app. | Family App resumes gracefully without crash. License remains unchanged; no false success reported. App never calls `/payments/verify/`. | `HUMAN QA REQUIRED` |
| **FAM-SUB-04** | Successful Payment Return | 1. Complete test payment on gateway.<br>2. Return to app via deep link. | Family App resumes, queries `/licensing/elders/{id}/license/`, updates expiration date and active badge. | `HUMAN QA REQUIRED` |

### Category H: App Lifecycle & Background Resilience
| Test ID | Test Scenario | Steps | Expected Result | Execution |
| :--- | :--- | :--- | :--- | :--- |
| **FAM-LIF-01** | Background & Foreground Resume | 1. Place app in background during active screen.<br>2. Wait 30 seconds.<br>3. Bring app to foreground. | Resumes state without blank screen; react-query silently revalidates stale data. | `HUMAN QA REQUIRED` |
| **FAM-LIF-02** | Screen Lock/Unlock | Lock device screen while on Dashboard, then unlock. | App renders immediately without crash or navigation reset. | `HUMAN QA REQUIRED` |
| **FAM-LIF-03** | Network Drop & Reconnection | 1. Turn Wi-Fi OFF.<br>2. Observe network banner.<br>3. Turn Wi-Fi ON. | Shows offline notice; upon reconnection, banner disappears and active queries automatically refresh. | `HUMAN QA REQUIRED` |

---

## 6. Android Hub Test Matrix (Physical Tablet)

### Category A: Hub Boot & Initialization
| Test ID | Test Scenario | Steps | Expected Result | Execution |
| :--- | :--- | :--- | :--- | :--- |
| **HUB-BOT-01** | Cold Boot Launch | 1. Power on physical tablet from powered-off state.<br>2. Launch YARA Hub app. | Starts smoothly, Hilt injections complete, loads persisted Room database, renders Home screen within 3s. | `HUMAN QA REQUIRED` |
| **HUB-BOT-02** | Crash Recovery & State Restoration | 1. Force stop Hub app via Android Settings or `adb shell am force-stop ir.sayda.yara.hub`.<br>2. Re-open app. | Restores previous session and active reminders without database corruption. | `HUMAN QA REQUIRED` |
| **HUB-BOT-03** | Offline Cold Boot | 1. Disable Wi-Fi on tablet.<br>2. Reboot tablet.<br>3. Launch app. | Hub loads local SQLite replica data, displays elder name and scheduled reminders without internet connection. | `HUMAN QA REQUIRED` |

### Category B: Hub Dashboard & Interaction
| Test ID | Test Scenario | Steps | Expected Result | Execution |
| :--- | :--- | :--- | :--- | :--- |
| **HUB-DSH-01** | Elder Ambient Home Screen | Observe Hub resting screen. | Displays large high-contrast clock, Persian date, elder greeting ("سلام مادر"), and today's schedule summary. | `HUMAN QA REQUIRED` |
| **HUB-DSH-02** | Touch Target Responsiveness | Tap medication cards and contact buttons on screen. | Large touch targets (≥48dp) respond immediately with subtle feedback; no cognitive overload or complex sub-menus. | `HUMAN QA REQUIRED` |
| **HUB-DSH-03** | Settings Protection | Attempt to access Settings. | Settings requires long-press (5s) or developer PIN, preventing accidental elder modification. | `HUMAN QA REQUIRED` |

### Category C: Local Medication & Reminder Engine (Offline Invariant)
| Test ID | Test Scenario | Steps | Expected Result | Execution |
| :--- | :--- | :--- | :--- | :--- |
| **HUB-REM-01** | Scheduled Reminder Firing | Schedule dose for 14:00; wait for clock to reach 14:00. | Full-screen reminder dialog takes foreground: plays audible chime, displays medication photo and Persian instructions. | `HUMAN QA REQUIRED` |
| **HUB-REM-02** | Elder Dose Confirmation | Tap large green button "دارو را خوردم" (Medication Taken). | Chime stops; execution state records `MEDICATION_TAKEN`; dialog closes; card retained for 15 minutes with checkmark. | `HUMAN QA REQUIRED` |
| **HUB-REM-03** | Reminder Postpone (Snooze) | Tap yellow button "۱۰ دقیقه دیگر یادآوری کن" (Postpone 10 min). | Dialog dismisses; local alarm reschedules exactly 10 minutes later; re-fires at designated postponed time. | `HUMAN QA REQUIRED` |
| **HUB-REM-04** | Stale Navigation Leak Prevention (Sprint 1 Verification) | 1. Complete or postpone a reminder.<br>2. Return to Home screen.<br>3. Rotate screen or toggle app background/foreground. | Does **NOT** re-open the completed/postponed reminder dialog (`consumeOpenRequest` and `launchSingleTop` verified). | `HUMAN QA REQUIRED` |
| **HUB-REM-05** | Air-Gapped Offline Reminder Execution | 1. Disconnect Hub Wi-Fi completely.<br>2. Wait for scheduled dose time. | Reminder fires on time offline with full audio/visual prompts; elder confirms dose; evidence queued in local outbox. | `HUMAN QA REQUIRED` |

### Category D: Hub Two-Way Messaging Subsystem
| Test ID | Test Scenario | Steps | Expected Result | Execution |
| :--- | :--- | :--- | :--- | :--- |
| **HUB-MSG-01** | Receive Incoming Text Message | Send message from Family App while Hub is online. | Hub receives message via poller within 3s; displays incoming notification and unread badge on Messages icon. | `HUMAN QA REQUIRED` |
| **HUB-MSG-02** | Auto-Read & Unread Badge Clear | Tap message to view full screen. | Unread badge clears; Hub dispatches read receipt to backend; Family App immediately updates status to `READ`. | `HUMAN QA REQUIRED` |
| **HUB-MSG-03** | Play Voice Note on Hub | Tap voice note received from caregiver. | Voice plays clearly through tablet speakers at comfortable volume; displays audio wave/progress indicator. | `HUMAN QA REQUIRED` |
| **HUB-MSG-04** | Photo & Video Viewing | Open photo or video message on Hub. | Media displays full-screen with high contrast and simple "بازگشت" (Back) button. | `HUMAN QA REQUIRED` |

### Category E: Hub LiveKit Audio/Video Calling
| Test ID | Test Scenario | Steps | Expected Result | Execution |
| :--- | :--- | :--- | :--- | :--- |
| **HUB-CAL-01** | Incoming Call Ringer | Initiate video call from Family App to Hub. | Hub screen wakes/switches to Incoming Call view: plays gentle Iranian ringer, displays caller name ("دختر") and photo. | `HUMAN QA REQUIRED` |
| **HUB-CAL-02** | Answer Call | Elder taps large green "پاسخ" (Answer) button. | Ringer stops; LiveKit room connects; full-screen video renders caregiver; Hub microphone streams elder's voice. | `HUMAN QA REQUIRED` |
| **HUB-CAL-03** | Reject Call | Elder taps red "رد تماس" (Decline) button. | Ringer stops; call declines cleanly; Family App displays call declined; Hub returns to ambient home screen. | `HUMAN QA REQUIRED` |
| **HUB-CAL-04** | Outgoing Emergency Call | Elder taps contact icon on Hub home screen. | Hub initiates call to priority caregiver; caregiver phone rings; connects audio/video upon caregiver answer. | `HUMAN QA REQUIRED` |

### Category F: Sync Runtime & Offline Recovery
| Test ID | Test Scenario | Steps | Expected Result | Execution |
| :--- | :--- | :--- | :--- | :--- |
| **HUB-SNC-01** | Monotonic Checkpoint Sync | Hub syncs with backend while online. | Checkpoint advances monotonically in SQLite; no duplicate delta records ingested. | `HUMAN QA REQUIRED` |
| **HUB-SNC-02** | Multi-Dose Offline Queue & Reconnection Drain | 1. Disconnect Hub Wi-Fi for 4 hours.<br>2. Acknowledge 2 scheduled doses offline.<br>3. Reconnect Wi-Fi. | Hub Sync Runtime establishes session, drains outbox evidence to backend; backend registers completions; Family App updates. | `HUMAN QA REQUIRED` |
| **HUB-SNC-03** | Server-Side Schedule Update Sync | 1. Caregiver adds new medication in Family App.<br>2. Hub performs sync cycle. | Hub downloads new `ScheduleDefinition` and `WorkflowExecution` replicas; schedules local AlarmManager without app restart. | `HUMAN QA REQUIRED` |

---

## 7. Cross-Device End-to-End Scenarios

```text
┌─────────────┐               ┌─────────────┐               ┌─────────────┐
│ FAMILY APP  │               │   BACKEND   │               │  YARA HUB   │
└──────┬──────┘               └──────┬──────┘               └──────┬──────┘
       │                             │                             │
       │ E2E-01: Two-Way Message     │                             │
       │────────────────────────────►│                             │
       │                             │── Delivery Polling/Sync ───►│
       │                             │                             │ (Displays Notification)
       │                             │◄── Read Receipt Dispatch ───│ (Elder Opens Message)
       │◄── Status Update: READ ─────│                             │
       │                             │                             │
       │ E2E-02: Medication Lifecycle│                             │
       │ (Caregiver creates dose)    │                             │
       │────────────────────────────►│                             │
       │                             │── Sync Delta Replicas ─────►│
       │                             │                             │ (Schedules Local Alarm)
       │                             │                             │ [Alarm Fires Offline]
       │                             │                             │ (Elder Takes Dose)
       │                             │◄── Sync Outbox Evidence ────│
       │◄── Dashboard Tone: CALM ────│                             │
       │                             │                             │
       │ E2E-04: Video Call          │                             │
       │ (Caregiver taps Call)       │                             │
       │─── Start Session / Token ──►│── Incoming Session Push ───►│ (Ringing)
       │◄── LiveKit Room Credentials─│                             │
       │                             │◄── Accept Session ──────────│ (Elder Answers)
       │======================= WebRTC Media Stream ===============│
       │ (Caregiver ends call)       │                             │
       │─── End Session ────────────►│── End Session Broadcast ───►│ (Returns to Ambient Home)
       └─────────────────────────────┴─────────────────────────────┘
```

### Scenario E2E-01: End-to-End Messaging Lifecycle
1. Caregiver types "داروی ظهر فراموش نشود" in Family App and taps Send.
2. Family App optimistically shows message as `PENDING`, updates to `SENT`.
3. Backend ingests message into PostgreSQL.
4. Hub receives message via background sync/poller within 3 seconds.
5. Hub sounds gentle notification chime and shows unread badge.
6. Elder taps message card on Hub tablet to read text.
7. Hub dispatches read acknowledgment to backend.
8. Family App background query refetches; bubble displays `✓✓ خوانده شده` in blue.

### Scenario E2E-02: End-to-End Medication Creation & Fulfillment
1. Caregiver creates "آسپرین ۸۰ میلی‌گرم" daily at 18:00 in Family App.
2. Backend creates `CareActivity`, `Prescription`, and `ScheduleDefinition`.
3. Hub executes sync cycle; persists replicas into Room DB; registers Android `AlarmManager`.
4. At 18:00, Hub triggers full-screen reminder dialog with audio chime.
5. Elder taps "دارو را خوردم".
6. Hub logs `CareCompletion` evidence into Room outbox.
7. Hub syncs outbox with backend.
8. Caregiver opens Family App Dashboard; today's dose shows green checkmark with exact confirmation time.

### Scenario E2E-03: Offline Recovery & Monotonic Sync
1. Turn Hub Wi-Fi OFF (simulating power/internet outage).
2. Dose triggers locally on Hub at scheduled time.
3. Elder confirms dose on Hub while offline.
4. Wait 15 minutes; turn Hub Wi-Fi back ON.
5. Hub WorkManager triggers sync session; uploads pending outbox evidence.
6. Backend evaluates evidence, records `MEDICATION_TAKEN`, and resolves pending alerts.
7. Family App reloads dashboard; status changes from `DUE` to `COMPLETED` without caregiver manual intervention.

### Scenario E2E-04: Real-Time Interactive Video Call
1. Caregiver taps Hub contact on Family App and starts Video Call.
2. Backend generates `CommunicationSession` and mints LiveKit join tokens.
3. Hub tablet rings with audio chime and caller photo.
4. Elder taps large green Answer button.
5. LiveKit connects on both sides; two-way audio and video stream smoothly.
6. After 30 seconds of conversation, caregiver taps red End Call button.
7. Both apps terminate session; Hub returns cleanly to resting ambient home screen.

### Scenario E2E-05: Subscription Checkout & License Refresh
1. Caregiver navigates to Subscription tab in Family App.
2. Selects Plan and initiates checkout.
3. Web view / browser opens payment gateway.
4. Caregiver completes mock/sandbox transaction.
5. Backend verifies callback, activates license, and records `PaymentSucceeded`.
6. Caregiver returns to Family App; app re-queries license; displays active subscription.

---

## 8. Failure & Recovery Matrix

| Failure Condition | Injected Point | Expected System Behavior | Recovery Verification |
| :--- | :--- | :--- | :--- |
| **Backend API Outage** | Kill backend process during client operation. | Clients display calm non-technical error ("عدم برقراری ارتباط با سرور"); no unhandled crash or white screen. | Once backend restarts, pull-to-refresh resumes normal operation. |
| **Internet Loss on Hub** | Disable Hub Wi-Fi during normal operation. | Hub continues running; scheduled alarms fire locally on time; elder can confirm doses offline. | When Wi-Fi is restored, pending outbox items sync automatically. |
| **Tablet Sudden Reboot** | Hard reboot tablet during pending reminder. | Boot receiver restarts Hub app; Room DB recovers state; missed or upcoming alarms are rescheduled. | No duplicated occurrences; pending evidence remains intact in SQLite. |
| **Family App Process Killed** | Force kill Family App while sending message. | Message is saved in local query cache as `PENDING` or `FAILED`; no message loss. | Upon app relaunch, message is listed with retry button affordance. |
| **Payment Gateway Cancelled** | Caregiver presses "انصراف" on ZarinPal gateway. | Returns to Family App; order remains pending or cancelled; no false subscription activation occurs. | App resumes cleanly; license remains unmutated; user can re-attempt. |
| **LiveKit Network Drop** | Disconnect Wi-Fi mid-call. | Media stream freezes; app displays reconnecting banner; if unrecoverable within 15s, ends call gracefully. | Releases hardware camera/microphone locks; returns to Home screen. |
| **Duplicate Sync Request** | Replay sync session payload twice. | Backend enforces idempotency keys and aggregate versions; ignores duplicate deltas. | Zero duplicate care completions or duplicate database records created. |

---

## 9. Acceptance Criteria for Physical Validation

The Phase 3 / Sprint 2 physical validation is accepted when:
1. **Zero P0 / Blocker Bugs:** No application crash, unhandled exception, database corruption, or missed offline reminder.
2. **Zero P1 / Critical Bugs:** Core flows (Messaging, Medication confirmation, Video calling, Sync recovery) succeed on physical hardware.
3. **Timezone Invariant Preserved:** All medication events occur in exact `Asia/Tehran` local time regardless of physical device locale settings.
4. **Offline Resilience Proven:** Scheduled reminder triggers and is confirmed on Hub without active Wi-Fi connection.
5. **Real Evidence Captured:** Completed test execution logs, screenshots/recordings of failures, and device metadata recorded in `REAL_DEVICE_TEST_EXECUTION_TEMPLATE.md`.
