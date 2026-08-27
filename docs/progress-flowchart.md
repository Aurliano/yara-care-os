# Yara Care — تکامل پروژه (Progress Flow)

**Version:** 1.1  
**Updated:** 25 Aug 2026

منبع وضعیت: کد فعلی (`apps/hub`, `apps/family`, `backend`)، ADR-012 / ADR-015، `docs/ROADMAP.md`، و لاگ‌های integration. درصدها تخمینی‌اند و برای هم‌راستایی تیم‌اند، نه معیار رسمی Done.

---

## 0. Snapshot (الان)

| لایه | وضعیت | یادداشت |
|------|--------|---------|
| Backend domains | ✅ تقریباً کامل | 11 دامنه پیاده‌سازی‌شده؛ Notification هنوز Draft؛ Hardening انجام شده |
| Hub Sprint II-A / II-B | 🟡 ~75–80% | Reminder MVP slice (ADR-012)؛ BLE و Device Owner هنوز نیست |
| Firmware | 📋 0% | درخت firmware در ریپو وجود ندارد |
| Hub ↔ Pill Box | 📋 0% | وابسته به Firmware + BLE Runtime |
| Family (Caregiver) App | 🟡 ~70% | Auth، Dashboard، Program، Devices، Alerts، Settings فعال؛ Push هنوز نه |
| Pilot | 📋 | بعد از یکپارچگی سخت‌افزار و پایداری |

**تناقض مهم با ROADMAP:** ترتیب رسمی Sprintها خطی است، ولی در عمل Family App جلوتر از Firmware شروع شده. این flowchart واقعیت موازی را نشان می‌دهد؛ وابستگی‌های معماری (مثلاً Pill Box قبل از تأیید سخت‌افزاری) همچنان برقرارند.

---

## 1. High-Level Journey

```mermaid
flowchart TD
    subgraph Legend
        direction TB
        L1["🟢 Completed"]
        L2["🟡 In Progress"]
        L3["🔵 Planned / Not Started"]
    end

    subgraph Sprints["Sprint Progression"]
        direction TB
        S0["Sprint 0<br/>Platform Foundation<br/>✅ 100%"]
        S1["Sprint 1<br/>Backend Platform<br/>✅ 100%"]
        S2["Sprint 2<br/>Android Hub Runtime<br/>🟡 ~75–80%"]
        S3["Sprint 3<br/>Firmware MVP<br/>🔵 0%"]
        S4["Sprint 4<br/>Hub ↔ Pill Box<br/>🔵 0%"]
        S5["Sprint 5<br/>Caregiver App MVP<br/>🟡 ~70%"]
        S6["Sprint 6<br/>Care Platform<br/>🔵 Planned"]
        S7["Sprint 7<br/>Smart Sensors<br/>🔵 Planned"]
        S8["Sprint 8<br/>Pilot Release<br/>🔵 Planned"]
    end

    S0 --> S1 --> S2
    S1 --> S3
    S2 --> S4
    S3 --> S4
    S1 --> S5
    S2 -.->|thin client needs Hub APIs| S5
    S4 -.->|full med confirm| S5
    S5 --> S6 --> S7 --> S8

    style S0 fill:#10b981,color:white
    style S1 fill:#10b981,color:white
    style S2 fill:#f59e0b,color:white
    style S3 fill:#3b82f6,color:white
    style S4 fill:#3b82f6,color:white
    style S5 fill:#f59e0b,color:white
    style S6 fill:#3b82f6,color:white
    style S7 fill:#3b82f6,color:white
    style S8 fill:#3b82f6,color:white
```

---

## 2. Layer-by-Layer Progress

```mermaid
flowchart LR
    subgraph Stack["Yara Stack — Completion Matrix"]
        direction TB
        subgraph Firmware["Firmware"]
            F1["ESP32-C3 BLE"]
            F2["Reed Switch Detection"]
            F3["Battery Monitoring"]
            F4["Power Optimization"]
            F5["Pairing Process"]
        end

        subgraph Hub["Android Hub"]
            H1["Kiosk / Device Owner"]
            H2["Room Database (v5)"]
            H3["Sync Infrastructure"]
            H4["Offline Reminders MVP"]
            H5["BLE / Device Runtime"]
            H6["Communication Runtime"]
            H7["Runtime Kernel"]
            H8["Boot Recovery"]
        end

        subgraph Backend["Backend (Django)"]
            B1["Identity & Access"]
            B2["Licensing"]
            B3["Scheduling"]
            B4["Workflow"]
            B5["Care"]
            B6["Device"]
            B7["Communication"]
            B8["Notification draft"]
            B9["Synchronization"]
            B10["Event"]
            B11["Integration"]
            B12["Hardening"]
        end

        subgraph CareApp["Family App Expo"]
            C1["Authentication"]
            C2["Devices / Pairing UI"]
            C3["Dashboard"]
            C4["Program / Medication"]
            C5["Hub / Device Status"]
            C6["In-app Alerts"]
            C7["Contacts / Calls"]
            C8["Settings / Family"]
            C9["Push Notifications"]
        end
    end

    B1-->|✅| B2-->|✅| B3-->|✅| B4-->|✅| B5-->|✅| B6-->|✅| B7-->|✅| B8-->|🔧| B9-->|✅| B10-->|✅| B11-->|✅| B12-->|✅|

    H2-->|✅| H3-->|✅| H4-->|✅| H7-->|✅| H8-->|✅|
    H6-->|🔧|
    H1-->|📋|
    H5-->|📋|

    F1-->|📋| F2-->|📋| F3-->|📋| F4-->|📋| F5-->|📋|

    C1-->|✅| C2-->|🔧| C3-->|✅| C4-->|✅| C5-->|✅| C6-->|✅| C7-->|🔧| C8-->|✅| C9-->|📋|

    style B1 fill:#10b981,color:white
    style B2 fill:#10b981,color:white
    style B3 fill:#10b981,color:white
    style B4 fill:#10b981,color:white
    style B5 fill:#10b981,color:white
    style B6 fill:#10b981,color:white
    style B7 fill:#10b981,color:white
    style B8 fill:#f59e0b,color:white
    style B9 fill:#10b981,color:white
    style B10 fill:#10b981,color:white
    style B11 fill:#10b981,color:white
    style B12 fill:#10b981,color:white

    style H1 fill:#3b82f6,color:white
    style H2 fill:#10b981,color:white
    style H3 fill:#10b981,color:white
    style H4 fill:#10b981,color:white
    style H5 fill:#3b82f6,color:white
    style H6 fill:#f59e0b,color:white
    style H7 fill:#10b981,color:white
    style H8 fill:#10b981,color:white

    style F1 fill:#3b82f6,color:white
    style F2 fill:#3b82f6,color:white
    style F3 fill:#3b82f6,color:white
    style F4 fill:#3b82f6,color:white
    style F5 fill:#3b82f6,color:white

    style C1 fill:#10b981,color:white
    style C2 fill:#f59e0b,color:white
    style C3 fill:#10b981,color:white
    style C4 fill:#10b981,color:white
    style C5 fill:#10b981,color:white
    style C6 fill:#10b981,color:white
    style C7 fill:#f59e0b,color:white
    style C8 fill:#10b981,color:white
    style C9 fill:#3b82f6,color:white
```

### اصلاحات نسبت به v1.0

- Family App دیگر «شروع‌نشده» نیست؛ بخش عمده Sprint 5 پیاده شده (`apps/family`).
- BLE Runtime روی Hub در حال انجام نیست — stub است و `OPEN_COMPARTMENT` صریحاً به Sprint II-C موکول شده.
- Kiosk / Device Owner در کد Hub پیدا نشد (فقط در اسناد)؛ دیگر ✅ نیست.
- Notification دامنه Draft است (ADR-015): inbox درون‌برنامه‌ای هست؛ SMS/Push هنوز نه.
- Push جدا از Alerts نشان داده شده.

---

## 3. Backend Domain Deep-Dive

```mermaid
flowchart TD
    subgraph BackendDomains["Backend — implemented domains"]
        IA["Identity & Access ✅"]
        LIC["Licensing ✅"]
        SCH["Scheduling ✅"]
        WFL["Workflow ✅"]
        CARE["Care ✅"]
        DEV["Device ✅"]
        COM["Communication ✅<br/>provider-dependent at runtime"]
        NOT["Notification 🔧<br/>Draft — in-app alerts only"]
        EVT["Event ✅"]
        SYNC["Synchronization ✅"]
        INT["Integration ✅<br/>Hub provision + sync facade"]
        HARD["Hardening ✅"]
    end

    IA --> LIC --> SCH --> WFL --> CARE --> DEV --> COM --> NOT --> EVT --> SYNC --> INT --> HARD

    style IA fill:#d1fae5,stroke:#10b981
    style LIC fill:#d1fae5,stroke:#10b981
    style SCH fill:#d1fae5,stroke:#10b981
    style WFL fill:#d1fae5,stroke:#10b981
    style CARE fill:#d1fae5,stroke:#10b981
    style DEV fill:#d1fae5,stroke:#10b981
    style COM fill:#d1fae5,stroke:#10b981
    style NOT fill:#fef3c7,stroke:#f59e0b
    style EVT fill:#d1fae5,stroke:#10b981
    style SYNC fill:#d1fae5,stroke:#10b981
    style INT fill:#d1fae5,stroke:#10b981
    style HARD fill:#d1fae5,stroke:#10b981
```

**نکته عملیاتی:** `POST /api/v1/communication/call/start/` در صورت نبود/خطای Skyroom با **502** برمی‌گردد. دامنه پیاده شده است؛ تماس واقعی به `SKYROOM_API_KEY` و سرویس خارجی وابسته است.

---

## 4. Hub Architecture & Current State (🟡 Sprint 2)

```mermaid
flowchart TB
    subgraph HubLayers["Hub Layer Stack"]
        direction TB
        DB[(Room Database<br/>v5 — schema exported)]
        SYNC["Synchronization Runtime ✅<br/>Delta up/down, checkpoint, outbox"]
        KERNEL["Runtime Kernel ✅<br/>Lifecycle + recover"]
        SCHED["Scheduling Replica Runtime ✅<br/>Occurrence + alarms"]
        WFRUN["Workflow Replica Runtime ✅<br/>SHOW_REMINDER path MVP"]
        DISPATCH["Action Dispatcher<br/>SHOW_REMINDER ✅<br/>INITIATE_CALL ✅<br/>OPEN_COMPARTMENT 📋 deferred"]
        DEVRT["Device Runtime 📋<br/>BLE stub — Sprint II-C / 4"]
        COMRT["Communication Runtime 🔧<br/>Skyroom join/leave; needs provider"]
        INTEG["Integration Runtime ✅<br/>WorkManager orchestration"]
        BOOT["Boot Receiver ✅<br/>Reschedule after reboot"]
    end

    BOOT --> INTEG
    INTEG --> KERNEL
    KERNEL --> SYNC
    KERNEL --> SCHED
    KERNEL --> WFRUN
    SCHED -->|OccurrenceDue| WFRUN
    WFRUN -->|Action| DISPATCH
    DISPATCH -->|SHOW_REMINDER| UI[Reminder UI ✅]
    DISPATCH -->|OPEN_COMPARTMENT| DEVRT
    DISPATCH -->|INITIATE_CALL| COMRT
    DEVRT -.->|future BLE| PILL["ESP32 Pill Box 📋"]
    SYNC --> DB
    WFRUN --> DB
    SCHED --> DB

    style DB fill:#dcfce7,stroke:#10b981
    style SYNC fill:#dcfce7,stroke:#10b981
    style KERNEL fill:#dcfce7,stroke:#10b981
    style SCHED fill:#dcfce7,stroke:#10b981
    style WFRUN fill:#dcfce7,stroke:#10b981
    style DISPATCH fill:#fef3c7,stroke:#f59e0b
    style DEVRT fill:#bbdefb,stroke:#3b82f6
    style COMRT fill:#fef3c7,stroke:#f59e0b
    style INTEG fill:#dcfce7,stroke:#10b981
    style BOOT fill:#dcfce7,stroke:#10b981
    style UI fill:#dcfce7,stroke:#10b981
    style PILL fill:#bbdefb,stroke:#3b82f6
```

### Hub Module Breakdown (واقعی)

```mermaid
flowchart LR
    subgraph Modules["Hub Gradle Modules"]
        APP[":app"]
        CORE[":core"]
        DATA[":data"]
        NETWORK[":network"]
        DATABASE[":database"]
        SYNC_MOD[":sync"]
        RUNTIME[":runtime"]
        UI_MOD[":ui"]
        HOME[":feature-home"]
        REM[":feature-reminder"]
        COM_FEAT[":feature-communication"]
    end

    APP --> CORE
    APP --> HOME
    APP --> REM
    APP --> COM_FEAT
    CORE --> DATABASE
    CORE --> NETWORK
    RUNTIME --> SYNC_MOD
    RUNTIME --> DATA
    DATABASE --> DATA
    NETWORK --> DATA
    HOME --> UI_MOD
    REM --> UI_MOD
    COM_FEAT --> UI_MOD

    style APP fill:#a78bfa,stroke:#7c3aed
    style CORE fill:#a78bfa,stroke:#7c3aed
    style DATABASE fill:#10b981,stroke:#059669
    style NETWORK fill:#10b981,stroke:#059669
    style SYNC_MOD fill:#10b981,stroke:#059669
    style RUNTIME fill:#f59e0b,stroke:#d97706
    style DATA fill:#10b981,stroke:#059669
    style UI_MOD fill:#10b981,stroke:#059669
    style HOME fill:#10b981,stroke:#059669
    style REM fill:#10b981,stroke:#059669
    style COM_FEAT fill:#f59e0b,stroke:#d97706
```

### Sprint 2 slice status

| Slice | Status | Evidence |
|-------|--------|----------|
| II-A Foundation & Runtime | ✅ تقریباً کامل | Multi-module, Room, sync, DI, Integration + Boot |
| II-B Reminder Runtime | ✅ MVP slice (ADR-012) | Offline SHOW_REMINDER، confirm → outbox؛ polish / escalate / postpone-upload موکول |
| II-C Device / BLE | 📋 شروع نشده | `DeferredDeviceActionHandler` → «Deferred to Sprint II-C»؛ بدون کد Bluetooth |

---

## 5. Medication Reminder Flow — Current → Target

```mermaid
flowchart LR
    subgraph Current["Current — Hub Reminder MVP ADR-012"]
        direction TB
        OCC["OccurrenceDue"]
        WF_RUN["Workflow Replica Runtime"]
        SHOW["SHOW_REMINDER"]
        UI["Reminder Screen"]
        EVIDENCE["User Confirmation"]
        LOCAL_CONFIRM["ExecutionConfirmed Hub-local"]
        OUTBOX["Outbox PendingEvidence"]
        SYNC_UP["Sync Runtime"]
        BACKEND["Backend Care interpretation"]

        OCC --> WF_RUN
        WF_RUN --> SHOW
        SHOW --> UI
        UI --> EVIDENCE
        EVIDENCE --> LOCAL_CONFIRM
        LOCAL_CONFIRM --> OUTBOX
        OUTBOX --> SYNC_UP
        SYNC_UP --> BACKEND
    end

    subgraph Target["Target — Sprint 4 Full Integration"]
        direction TB
        OCC2["OccurrenceDue"]
        WF2["Workflow Replica Runtime"]
        OPEN["OPEN_COMPARTMENT BLE"]
        PILLBOX["Pill Box CompartmentClosed"]
        BLE_DEV["Device Runtime"]
        EVIDENCE2["CompartmentClosed Evidence"]
        COMPARE["Confirmation Policy"]
        CONFIRM2["ExecutionConfirmed"]
        SYNC2["Sync to Backend"]
        CARE_INTERP["Care → MedicationTaken"]

        OCC2 --> WF2
        WF2 --> OPEN
        OPEN --> BLE_DEV
        BLE_DEV --> PILLBOX
        PILLBOX --> EVIDENCE2
        EVIDENCE2 --> COMPARE
        UI2["Manual Confirm"] --> COMPARE
        COMPARE --> CONFIRM2
        CONFIRM2 --> SYNC2
        SYNC2 --> CARE_INTERP
    end

    subgraph Future["Sprint 3 — Firmware first prerequisite"]
        direction TB
        ESP["ESP32-C3 Firmware"]
        BLE_PAIR["BLE Pairing"]
        REED["Reed Switch"]
        BATT["Battery Monitoring"]

        ESP --> BLE_PAIR
        ESP --> REED
        ESP --> BATT
    end

    style Current fill:#dcfce7,stroke:#10b981
    style Target fill:#fef3c7,stroke:#f59e0b
    style Future fill:#bbdefb,stroke:#3b82f6
```

**باقی‌مانده‌های ADR-012:** polish UI، escalate/skip روی Reminder، upload postpone، کاهش اتکا به bootstrap محلی.

---

## 6. Synchronization Pipeline — Data Flow

```mermaid
flowchart LR
    subgraph SyncFlow["Backend ↔ Hub Synchronization"]
        BACKEND["Backend PostgreSQL + Event"]
        DELTA_SVC["Delta / Snapshot services"]
        HUB_FACADE["Integration Hub Sync API<br/>/api/v1/hub/sync/"]
        SYNC_API["Synchronization API<br/>/api/v1/synchronization/"]
        HUB_SYNC["Hub Sync Runtime"]
        HUB_DB["Hub Room DB<br/>Replica + Outbox"]
    end

    BACKEND --> DELTA_SVC
    DELTA_SVC --> HUB_FACADE
    DELTA_SVC --> SYNC_API
    HUB_FACADE <-->|HTTPS + JWT<br/>provisioned Hub| HUB_SYNC
    SYNC_API <-->|sessions, pending-ops,<br/>checkpoints| HUB_SYNC
    HUB_SYNC --> HUB_DB
    HUB_DB -->|Outbox upload| HUB_FACADE

    style BACKEND fill:#dbeafe,stroke:#3b82f6
    style DELTA_SVC fill:#dcfce7,stroke:#10b981
    style HUB_FACADE fill:#dcfce7,stroke:#10b981
    style SYNC_API fill:#dcfce7,stroke:#10b981
    style HUB_SYNC fill:#dcfce7,stroke:#10b981
    style HUB_DB fill:#dcfce7,stroke:#10b981
```

مسیر قدیمی `/api/v1/sync/` در کد فعلی استفاده نمی‌شود.

---

## 7. Backend Test Status

```mermaid
flowchart LR
    subgraph TestSummary["Backend Testing — ~309 collected pytest items"]
        UNIT["Domain / service tests"]
        API["API / DRF tests"]
        ARCH["Architecture FK contracts"]
        INTEGRATION["Integration flows"]
    end

    UNIT --> API --> ARCH --> INTEGRATION

    style UNIT fill:#dcfce7,stroke:#10b981
    style API fill:#dcfce7,stroke:#10b981
    style ARCH fill:#dcfce7,stroke:#10b981
    style INTEGRATION fill:#dcfce7,stroke:#10b981
```

### Test breakdown by area (approx. `def test_` counts)

| Area | Tests | Status |
|------|-------|--------|
| Architecture | ~40 | ✅ |
| Workflow | ~33 | ✅ |
| Scheduling | ~30 | ✅ |
| Integration | ~30 | ✅ |
| Communication | ~28 | ✅ |
| Device | ~27 | ✅ |
| Care | ~20 | ✅ |
| Identity & Access | ~19 | ✅ |
| Synchronization | ~18 | ✅ |
| Event | ~16 | ✅ |
| Licensing | ~16 | ✅ |
| Infrastructure | ~16 | ✅ |
| Notification | ~5 | 🔧 draft slice |
| Common / root | ~5 | ✅ |

`docs/CHANGELOG.md` هنوز «236 tests» دارد — عدد قدیمی است؛ این flowchart با `pytest --collect-only` هم‌خوان است (~309).

---

## 8. Sprint Dependency Graph (واقعی + معماری)

```mermaid
flowchart TD
    S0_START["Sprint 0 ✅"]
    S1_DELIVER["Sprint 1 Backend ✅"]
    S2_HUB_A["Sprint 2-A Hub Foundation ✅"]
    S2_HUB_B["Sprint 2-B Reminder MVP ✅ slice"]
    S2_HUB_C["Sprint 2-C / 4 BLE Device 📋"]
    S3_FW["Sprint 3 Firmware 📋"]
    S4_INTEGRATE["Sprint 4 Hub-PillBox 📋"]
    S5_APP["Sprint 5 Family App 🟡 ~70%"]
    S6_PLATFORM["Sprint 6 Care Platform 📋"]
    S7_SENSORS["Sprint 7 Smart Sensors 📋"]
    S8_PILOT["Sprint 8 Pilot 📋"]

    S0_START --> S1_DELIVER
    S1_DELIVER --> S2_HUB_A
    S1_DELIVER --> S3_FW
    S1_DELIVER --> S5_APP
    S2_HUB_A --> S2_HUB_B
    S2_HUB_B --> S2_HUB_C
    S2_HUB_C --> S4_INTEGRATE
    S3_FW --> S4_INTEGRATE
    S2_HUB_B -.-> S5_APP
    S4_INTEGRATE -.-> S5_APP
    S5_APP --> S6_PLATFORM
    S6_PLATFORM --> S7_SENSORS
    S7_SENSORS --> S8_PILOT

    style S0_START fill:#10b981,color:white
    style S1_DELIVER fill:#10b981,color:white
    style S2_HUB_A fill:#10b981,color:white
    style S2_HUB_B fill:#10b981,color:white
    style S2_HUB_C fill:#3b82f6,color:white
    style S3_FW fill:#3b82f6,color:white
    style S4_INTEGRATE fill:#3b82f6,color:white
    style S5_APP fill:#f59e0b,color:white
    style S6_PLATFORM fill:#3b82f6,color:white
    style S7_SENSORS fill:#3b82f6,color:white
    style S8_PILOT fill:#3b82f6,color:white
```

---

## 9. Domain Ownership Matrix

```mermaid
flowchart LR
    subgraph Matrix["Domain Ownership — Who Owns What"]
        IA["Identity & Access"]
        CARE_DOMAIN["Care"]
        LIC["Licensing"]
        SCH["Scheduling"]
        WFL["Workflow"]
        DEV["Device"]
        COM["Communication"]
        NOT["Notification"]
        SYNC["Synchronization"]
        EVT["Event"]
    end

    subgraph Ownership["Ownership Relationships"]
        IA -->|User, Elder, Membership| CARE_DOMAIN
        IA -->|Authorization| ALL["All Other Domains"]
        LIC -->|Plans, Subscriptions| IA
        CARE_DOMAIN -->|CareActivity| SCH
        CARE_DOMAIN -->|CareActivity| WFL
        CARE_DOMAIN -->|Compartment Assignment| DEV
        CARE_DOMAIN -->|Care Completion| EVT
        SCH -->|Occurrences| WFL
        WFL -->|Evidence| CARE_DOMAIN
        WFL -->|Actions| DEV
        WFL -->|Actions| COM
        WFL -->|NOTIFY_CAREGIVER| NOT
        DEV -->|Hardware Facts| EVT
        COM -->|Session Facts| EVT
        SYNC -->|Replica State| ALL
    end

    style IA fill:#dbeafe,stroke:#3b82f6
    style CARE_DOMAIN fill:#dcfce7,stroke:#10b981
    style LIC fill:#dcfce7,stroke:#10b981
    style SCH fill:#dcfce7,stroke:#10b981
    style WFL fill:#dcfce7,stroke:#10b981
    style DEV fill:#dcfce7,stroke:#10b981
    style COM fill:#dcfce7,stroke:#10b981
    style NOT fill:#fef3c7,stroke:#f59e0b
    style SYNC fill:#dcfce7,stroke:#10b981
    style EVT fill:#ecfccb,stroke:#84cc16
    style ALL fill:#f1f5f9,stroke:#94a3b8
```

---

## 10. Next Milestones (واقع‌بینانه — Aug 2026)

```mermaid
gantt
    title Yara Project — Near-term focus
    dateFormat  YYYY-MM-DD
    section Backend
    Domains + Hardening           :done,    be1, 2026-06-01, 2026-08-01
    Notification draft + alerts   :done,    be2, 2026-07-15, 2026-08-20
    Skyroom ops reliability       :active,  be3, 2026-08-19, 14d
    section Hub
    II-A Foundation               :done,    h1,  2026-06-01, 2026-07-20
    II-B Reminder MVP             :done,    h2,  2026-07-15, 2026-08-20
    Communication runtime polish  :active,  h3,  2026-08-15, 21d
    BLE Device Runtime II-C       :         h4,  2026-09-01, 21d
    section Firmware
    ESP32-C3 MVP                  :         fw1, 2026-09-01, 21d
    section Family App
    Core screens MVP              :done,    fa1, 2026-07-01, 2026-08-20
    Calls + provider hardening    :active,  fa2, 2026-08-15, 21d
    Push notifications            :         fa3, 2026-09-15, 14d
    section Integration
    Hub ↔ Pill Box                :         int1, 2026-09-22, 21d
    Pilot prep                    :         int2, 2026-10-15, 21d
```

### اولویت‌های کوتاه‌مدت پیشنهادی

1. پایدار کردن تماس (Skyroom env + 502 handling) روی Backend / Hub / Family  
2. بستن باقی‌مانده‌های ADR-012 روی Reminder  
3. شروع Sprint 3 Firmware (مسیر بحرانی برای تأیید دارو با سخت‌افزار)  
4. BLE Runtime روی Hub بعد از پروتکل Firmware  
5. Push فقط بعد از انتخاب vendor و freeze دامنه Notification  

---

## 11. Gaps deliberately called out

| موضوع | وضعیت قبلی در v1.0 | واقعیت |
|--------|---------------------|--------|
| Caregiver App | Sprint 5 = 0% | اپ `apps/family` با صفحات اصلی فعال است |
| Hub BLE | In progress | Stub؛ بدون Bluetooth API |
| Kiosk / Device Owner | ✅ | در کد نیست |
| Notification | ✅ کامل | Draft؛ فقط inbox |
| Backend tests | 236 | ~309 collected |
| Sync path | `/api/v1/sync/` | `/api/v1/hub/sync/` + `/api/v1/synchronization/` |
| Firmware Gantt | Active Aug 2026 | هنوز شروع نشده |
| Communication | فقط planned روی clients | Runtime روی Hub و Family هست؛ وابسته به provider |
