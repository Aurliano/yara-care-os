# Yara Care — تکامل پروژه (Progress Flow)

**Version:** 1.2  
**Updated:** 02 Sep 2026

منبع وضعیت: کد فعلی (`apps/hub`, `apps/family`, `backend`, `firmware`)، ADR-012 تا ADR-015، `docs/ROADMAP.md`، و نتایج اجرای تست‌ها (۳۲۰ تست بک‌اند، ۱۱۱ تست هاب، ۸۵ تست فمیلی). درصدها تخمینی‌اند و برای هم‌راستایی تیم‌اند، نه معیار رسمی Done.

---

## 0. Snapshot (الان)

| لایه | وضعیت | یادداشت |
|------|--------|---------|
| Backend domains | ✅ کامل و پایدار | ۱۰ دامنه اصلی + زیرسیستم پیام‌رسانی دوطرفه و رسانه؛ معماری ارائه‌دهنده ارتباطات LiveKit (ADR-013)؛ هشدار درون‌برنامه‌ای (ADR-015)؛ ۳۳۲ تست سبز |
| Hub Android | 🟢 ~85% | فونداسیون (Sprint II-A)، یادآور آفلاین (Sprint II-B / ADR-012)، سینک و پرویژنینگ (II-D/E)، تماس تصویری/صوتی LiveKit v1 و پیام‌رسانی دوطرفه؛ BLE موکول به فاز سخت‌افزار؛ حالت کیوسک موکول به آمادگی تولید؛ ۱۱۱ تست سبز |
| Firmware | 📋 0% | ساختار دایرکتوری‌ها (`firmware/pillbox`, `firmware/sensors`) ایجاد شده، کدنویسی در فاز سخت‌افزار آغاز می‌شود |
| Hub ↔ Pill Box | 📋 0% | وابسته به فریمور ESP32-C3 + درایور BLE در Hub (فاز یکپارچه‌سازی سخت‌افزار) |
| Family (Caregiver) App | 🟢 ~85% | احراز هویت، داشبورد مراقب، برنامه دارویی و مراقبتی، وضعیت دستگاه‌ها، هشدارهای درون‌برنامه‌ای (ADR-015)، تماس تصویری/صوتی LiveKit Native WebRTC و پیام‌رسانی دوطرفه فعال؛ ۸۵ تست سبز |
| Pilot | 📋 | پس از تکمیل فازهای نرم‌افزاری (پلن/پرداخت، رادیو، پوش)، فریمور، اتصال سخت‌افزار و پایداری نهایی |

**تطبیق با نقشه راه محصول:** تماس ویدیویی/صوتی و پیام‌رسانی دوطرفه به عنوان بخشی از MVP پیاده‌سازی شده‌اند. کار نرم‌افزاری باقیمانده شامل فاز ۲ (پلن‌ها و پرداخت)، فاز ۳ (رادیو) و فاز ۴ (پوش‌نوتیفیکیشن) است و پس از آن یکپارچه‌سازی سخت‌افزاری و سپس آمادگی تولید (حالت کیوسک) انجام خواهد شد.

---

## 1. High-Level Journey

```mermaid
flowchart TD
    subgraph Legend
        direction TB
        L1["🟢 Completed / Near Done"]
        L2["🟡 In Progress"]
        L3["🔵 Planned / Not Started"]
    end

    subgraph Sprints["Sprint Progression"]
        direction TB
        S0["Sprint 0<br/>Platform Foundation<br/>✅ 100%"]
        S1["Sprint 1<br/>Backend Platform<br/>✅ 100% (320 tests)"]
        S2["Sprint 2<br/>Android Hub Runtime<br/>🟢 ~85% (111 tests)"]
        S3["Sprint 3<br/>Firmware MVP<br/>🔵 0% (Scaffolded)"]
        S4["Sprint 4<br/>Hub ↔ Pill Box<br/>🔵 0%"]
        S5["Sprint 5<br/>Caregiver App MVP<br/>🟢 ~85% (85 tests)"]
        S6["Sprint 6<br/>Care Platform<br/>🔵 Planned"]
        S7["Sprint 7<br/>Smart Sensors<br/>🔵 Planned"]
        S8["Sprint 8<br/>Pilot Release<br/>🔵 Planned"]
    end

    S0 --> S1 --> S2
    S1 --> S3
    S2 --> S4
    S3 --> S4
    S1 --> S5
    S2 -.->|Real-time WebRTC / LiveKit| S5
    S4 -.->|Hardware Med Confirm| S5
    S5 --> S6 --> S7 --> S8

    style S0 fill:#10b981,color:white
    style S1 fill:#10b981,color:white
    style S2 fill:#10b981,color:white
    style S3 fill:#3b82f6,color:white
    style S4 fill:#3b82f6,color:white
    style S5 fill:#10b981,color:white
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
        
        subgraph Firmware["Firmware (ESP32-C3)"]
            direction LR
            F1["BLE Service 📋"]
            F2["Reed Switch Detection 📋"]
            F3["Battery Monitoring 📋"]
            F4["Power Optimization 📋"]
            F5["Pairing Process 📋"]
            F1 --- F2 --- F3 --- F4 --- F5
        end

        subgraph Hub["Android Hub (11 Modules)"]
            direction LR
            H1["Kiosk / Device Owner 📋"]
            H2["Room Database v5 ✅"]
            H3["Sync Infrastructure ✅"]
            H4["Offline Reminders MVP ✅"]
            H5["BLE / Device Runtime 📋"]
            H6["Communication LiveKit ✅"]
            H7["Runtime Kernel ✅"]
            H8["Boot Recovery ✅"]
            H2 --- H3 --- H4 --- H6 --- H7 --- H8
        end

        subgraph Backend["Backend Django (11 Domains)"]
            direction LR
            B1["Identity & Access ✅"]
            B2["Licensing ✅"]
            B3["Scheduling ✅"]
            B4["Workflow ✅"]
            B5["Care ✅"]
            B6["Device ✅"]
            B7["Communication (LiveKit/Skyroom) ✅"]
            B8["Notification (In-app Inbox) 🔧"]
            B9["Synchronization ✅"]
            B10["Event ✅"]
            B11["Integration ✅"]
            B12["Hardening ✅"]
            B1 --> B2 --> B3 --> B4 --> B5 --> B6 --> B7 --> B8 --> B9 --> B10 --> B11 --> B12
        end

        subgraph CareApp["Family App Expo (React Native)"]
            direction LR
            C1["Authentication ✅"]
            C2["Devices / Pairing UI ✅"]
            C3["Dashboard ✅"]
            C4["Program / Medication ✅"]
            C5["Hub / Device Status ✅"]
            C6["In-app Alerts (ADR-015) ✅"]
            C7["LiveKit Video & Audio Calls ✅"]
            C8["Settings / Family ✅"]
            C9["Push Notifications (FCM) 📋"]
            C1 --> C3 --> C4 --> C5 --> C6 --> C7 --> C8
        end
    end

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
    style H6 fill:#10b981,color:white
    style H7 fill:#10b981,color:white
    style H8 fill:#10b981,color:white

    style F1 fill:#3b82f6,color:white
    style F2 fill:#3b82f6,color:white
    style F3 fill:#3b82f6,color:white
    style F4 fill:#3b82f6,color:white
    style F5 fill:#3b82f6,color:white

    style C1 fill:#10b981,color:white
    style C2 fill:#10b981,color:white
    style C3 fill:#10b981,color:white
    style C4 fill:#10b981,color:white
    style C5 fill:#10b981,color:white
    style C6 fill:#10b981,color:white
    style C7 fill:#10b981,color:white
    style C8 fill:#10b981,color:white
    style C9 fill:#3b82f6,color:white
```

### تغییرات و ارتقاهای کلیدی
- **مهاجرت ارتباطات به LiveKit v1:** پیاده‌سازی ارائه‌دهنده LiveKit در بک‌اند (ADR-013)، صدور توکن‌های امن JWT، پیاده‌سازی WebRTC نیتیو در Family App (`@livekit/react-native`) و ران‌تایم اختصاصی LivekitCallEngine به همراه صفحه تماس و زنگ ریل‌تایم روی Hub.
- **پیام‌رسانی دوطرفه کامل (Two-Way Messaging):** پیاده‌سازی کامل ارسال و دریافت پیام‌های متنی، پیام صوتی (Voice Message)، عکس و ویدیو در بک‌اند (`Message`, `MessageAttachment`)، هاب (`MessagingRepositoryImpl`) و اپلیکیشن فمیلی با وضعیت‌های تحویل و خوانده‌شدن.
- **تست‌ها و ثبات:** ۳۳۲ تست بک‌اند (۱۰۰٪ پاس)، ۱۱۱ تست هاب (۱۰۰٪ پاس)، ۸۵ تست فمیلی اپ (۱۰۰٪ پاس).
- **جداسازی معماری تماس از پیام صوتی:** تماس صوتی/تصویری هم‌زمان (Synchronous LiveKit Call) از پیام صوتی ناهمگام (Asynchronous Voice Message) کاملاً در داده‌ها و ماشین وضعیت جداست (`Voice Message != Voice Call`).
- **وضعیت فریمور و کیوسک:** فریمور در انتظار فاز یکپارچه‌سازی سخت‌افزار است؛ حالت کیوسک هاب به فاز آمادگی تولید موکول شده است.

---

## 3. Backend Domain Deep-Dive

```mermaid
flowchart TD
    subgraph BackendDomains["Backend — 11 Implemented Domains (320 tests)"]
        IA["Identity & Access ✅"]
        LIC["Licensing ✅"]
        SCH["Scheduling ✅"]
        WFL["Workflow ✅"]
        CARE["Care ✅"]
        DEV["Device ✅"]
        COM["Communication ✅<br/>LiveKit v1 Primary + Skyroom Fallback (ADR-013)"]
        NOT["Notification 🔧<br/>Draft — In-App Alert Inbox (ADR-015)"]
        EVT["Event ✅"]
        SYNC["Synchronization ✅"]
        INT["Integration ✅<br/>Hub Provisioning + Sync Facade + Alert Handlers"]
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

**نکته زیرساختی ارتباطات (ADR-013):**  
بک‌اند ارائه‌دهنده را انتزاعی کرده است (`CommunicationProvider`). در حال حاضر `LivekitCommunicationProvider` به عنوان ارائه‌دهنده پیش‌فرض توکن‌های امن JWT صادر می‌کند و اتاق‌های پایدار بر اساس شناسه سالمند مدیریت می‌شوند؛ نیازی به وابستگی مستقیم کلاینت‌ها به APIهای شرکت واسط نیست.

---

## 4. Hub Architecture & Current State (Sprint 2 + LiveKit)

```mermaid
flowchart TB
    subgraph HubLayers["Hub Layer Stack (11 Gradle Modules)"]
        direction TB
        DB[(Room Database<br/>v5 — Schema Exported)]
        SYNC["Synchronization Runtime ✅<br/>Delta up/down, Checkpoint, Outbox"]
        KERNEL["Runtime Kernel ✅<br/>Lifecycle + Recover"]
        SCHED["Scheduling Replica Runtime ✅<br/>Occurrence + Alarms"]
        WFRUN["Workflow Replica Runtime ✅<br/>SHOW_REMINDER path MVP"]
        DISPATCH["Action Dispatcher<br/>SHOW_REMINDER ✅<br/>INITIATE_CALL ✅<br/>OPEN_COMPARTMENT 📋 deferred"]
        DEVRT["Device Runtime 📋<br/>BLE stub — Sprint II-C / 4"]
        COMRT["Communication Runtime ✅<br/>LiveKit v1 WebRTC + Real-Time Ringing"]
        INTEG["Integration Runtime ✅<br/>WorkManager Orchestration"]
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
    style DISPATCH fill:#dcfce7,stroke:#10b981
    style DEVRT fill:#bbdefb,stroke:#3b82f6
    style COMRT fill:#dcfce7,stroke:#10b981
    style INTEG fill:#dcfce7,stroke:#10b981
    style BOOT fill:#dcfce7,stroke:#10b981
    style UI fill:#dcfce7,stroke:#10b981
    style PILL fill:#bbdefb,stroke:#3b82f6
```

### Hub Module Breakdown (واقعی — ۱۱ ماژول گرادل)

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
    style RUNTIME fill:#10b981,stroke:#059669
    style DATA fill:#10b981,stroke:#059669
    style UI_MOD fill:#10b981,stroke:#059669
    style HOME fill:#10b981,stroke:#059669
    style REM fill:#10b981,stroke:#059669
    style COM_FEAT fill:#10b981,stroke:#059669
```

### وضعیت برش‌های Sprint 2 و ارتباطات

| Slice | وضعیت | مستندات و شواهد |
|-------|--------|-----------------|
| II-A Foundation & Runtime | ✅ کامل | معماری ۱۱ ماژوله، Room v5، تزریق وابستگی Hilt، Integration + Boot Recovery |
| II-B Reminder Runtime | ✅ MVP کامل (ADR-012) | اجرای آفلاین `SHOW_REMINDER`، تعویق محلی (Postpone)، ثبت Evidence در Outbox، ارسال به بک‌اند |
| II-D / II-E Sync & Provisioning | ✅ کامل | سینک دلتای افزایشی، سیستم Staging دانلود، گیت احراز هویت و Provisioning |
| Communication LiveKit Runtime | ✅ کامل | موتور تماس LiveKit v1، مدیریت تماس دریافتی/ارسالی، رابط کاربری سالمند-محور `CallScreen` و `TalkingScreen` |
| II-C Device / BLE | 📋 شروع‌نشده | هندلر `DeferredDeviceActionHandler` به عنوان Stub؛ بدون کد Bluetooth |
| Kiosk / Device Owner | 📋 در برنامه | در معماری تعیین شده، اما هنوز در کد اندروید فعال نشده است |

---

## 5. Medication Reminder Flow — وضعیت فعلی و هدف

```mermaid
flowchart LR
    subgraph Current["Current — Hub Reminder MVP (ADR-012) ✅"]
        direction TB
        OCC["OccurrenceDue (Local Alarm)"]
        WF_RUN["Workflow Replica Runtime"]
        SHOW["SHOW_REMINDER Action"]
        UI["Elder Reminder Screen"]
        EVIDENCE["User Manual Confirm"]
        LOCAL_CONFIRM["ExecutionConfirmed (Hub-local)"]
        OUTBOX["Outbox PendingEvidence Queue"]
        SYNC_UP["Sync Runtime Upload"]
        BACKEND["Backend Care Domain Interpretation"]

        OCC --> WF_RUN
        WF_RUN --> SHOW
        SHOW --> UI
        UI --> EVIDENCE
        EVIDENCE --> LOCAL_CONFIRM
        LOCAL_CONFIRM --> OUTBOX
        OUTBOX --> SYNC_UP
        SYNC_UP --> BACKEND
    end

    subgraph Target["Target — Sprint 4 Full Hardware Integration 📋"]
        direction TB
        OCC2["OccurrenceDue"]
        WF2["Workflow Replica Runtime"]
        OPEN["OPEN_COMPARTMENT BLE Action"]
        PILLBOX["ESP32 Pill Box CompartmentClosed Event"]
        BLE_DEV["Hub BLE Device Runtime"]
        EVIDENCE2["CompartmentClosed Hardware Evidence"]
        COMPARE["Confirmation Policy Engine"]
        CONFIRM2["ExecutionConfirmed Aggregate"]
        SYNC2["Sync to Cloud Backend"]
        CARE_INTERP["Care → MedicationTaken Record"]

        OCC2 --> WF2
        WF2 --> OPEN
        OPEN --> BLE_DEV
        BLE_DEV --> PILLBOX
        PILLBOX --> EVIDENCE2
        EVIDENCE2 --> COMPARE
        UI2["Manual Confirm Backup"] --> COMPARE
        COMPARE --> CONFIRM2
        CONFIRM2 --> SYNC2
        SYNC2 --> CARE_INTERP
    end

    subgraph Prereq["Sprint 3 — Firmware Prerequisite 📋"]
        direction TB
        ESP["ESP32-C3 Firmware"]
        BLE_PAIR["BLE Pairing Protocol"]
        REED["Reed Switch Sensor Logic"]
        BATT["Battery ADC Monitoring"]

        ESP --> BLE_PAIR
        ESP --> REED
        ESP --> BATT
    end

    style Current fill:#dcfce7,stroke:#10b981
    style Target fill:#fef3c7,stroke:#f59e0b
    style Prereq fill:#bbdefb,stroke:#3b82f6
```

---

## 6. Synchronization Pipeline — Data Flow

```mermaid
flowchart LR
    subgraph SyncFlow["Backend ↔ Hub Synchronization Pipeline"]
        BACKEND["Backend PostgreSQL + Event Store"]
        DELTA_SVC["Delta & Snapshot Services"]
        HUB_FACADE["Integration Hub Sync API<br/>/api/v1/hub/sync/"]
        SYNC_API["Synchronization API<br/>/api/v1/synchronization/"]
        HUB_SYNC["Hub Sync Runtime Client"]
        HUB_DB["Hub Room DB<br/>Replicas + Outbox"]
    end

    BACKEND --> DELTA_SVC
    DELTA_SVC --> HUB_FACADE
    DELTA_SVC --> SYNC_API
    HUB_FACADE <-->|HTTPS + JWT<br/>Bulk Delta / Snapshot / Outbox| HUB_SYNC
    SYNC_API <-->|Sessions, Checkpoints,<br/>Pending Operations| HUB_SYNC
    HUB_SYNC --> HUB_DB
    HUB_DB -->|Outbox upload| HUB_FACADE

    style BACKEND fill:#dbeafe,stroke:#3b82f6
    style DELTA_SVC fill:#dcfce7,stroke:#10b981
    style HUB_FACADE fill:#dcfce7,stroke:#10b981
    style SYNC_API fill:#dcfce7,stroke:#10b981
    style HUB_SYNC fill:#dcfce7,stroke:#10b981
    style HUB_DB fill:#dcfce7,stroke:#10b981
```

---

## 7. Test Matrix & Code Health

```mermaid
flowchart LR
    subgraph TestSummary["Yara Total Test Suite — 516 Tests Passing (100%)"]
        BE["Backend Pytest<br/>320 tests ✅"]
        HUB["Android Hub JUnit<br/>111 tests ✅"]
        FAM["Family App Jest<br/>85 tests ✅"]
    end

    BE --- HUB --- FAM

    style BE fill:#dcfce7,stroke:#10b981
    style HUB fill:#dcfce7,stroke:#10b981
    style FAM fill:#dcfce7,stroke:#10b981
```

### تفکیک تست‌های بک‌اند (۳۲۰ تست در ۱۱ دامنه و معماری)

| دامنه / حوزه | تعداد تست‌ها | وضعیت | تمرکز تست‌ها |
|---|---|---|---|
| Architecture Contracts | ۴۰ | ✅ | تست‌های عدم وجود Foreign Key نامجاز و جداسازی وابستگی‌ها |
| Workflow | ۳۳ | ✅ | ماشین وضعیت، اجرای آفلاین، سیاست‌های تعویق و عدم مصرف |
| Integration | ۳۰ | ✅ | پرویژنینگ هاب، احراز هویت، سناریوهای E2E و نگاشت Alert |
| Scheduling | ۳۰ | ✅ | تعریف زمان‌بندی، تولید رخداد و قوانین تقویمی |
| Communication | ۲۸ | ✅ | نشست تماس، مدیریت شرکت‌کنندگان و امنیت عدم انتشار توکن |
| Infrastructure Providers | ۲۷ | ✅ | تست‌های LiveKit Provider (۱۱ تست)، Skyroom Provider (۱۵ تست)، Fake Provider |
| Device | ۲۷ | ✅ | ثبت دستگاه، انتساب محفظه و ارسال فرمان |
| Care | ۲۰ | ✅ | برنامه‌های مراقبتی، داروها و تفسیر رویدادهای مراقبتی |
| Identity & Access | ۱۹ | ✅ | احراز هویت، مدیریت سالمند، عضویت مراقبان و کنترل دسترسی |
| Synchronization | ۱۸ | ✅ | نشست سینک، ایجاد چک‌پوینت و عملیات دسته‌ای |
| Event Store | ۱۶ | ✅ | ثبات رویدادهای دامنه و ردگیری تغییرات |
| Licensing | ۱۶ | ✅ | پلن‌ها، اشتراک‌ها و محدودیت‌های دسترسی |
| Notification (Draft) | ۵ | 🔧 | صندوق هشدارهای درون‌برنامه‌ای و مدیریت Alertها |
| Common & Root Health | ۵ | ✅ | پاسخ‌های استاندارد خطا و سلامت کلی سرویس |
| **مجموع تست‌های بک‌اند** | **۳۲۰** | **✅ ۱۰۰٪** | **بدون هیچ‌گونه تست ناموفق** |

---

## 8. Sprint Dependency Graph (واقعی + معماری)

```mermaid
flowchart TD
    S0_START["Sprint 0 ✅"]
    S1_DELIVER["Sprint 1 Backend ✅ (320 tests)"]
    S2_HUB_A["Sprint 2-A Hub Foundation ✅"]
    S2_HUB_B["Sprint 2-B Reminder MVP ✅ (ADR-012)"]
    S2_HUB_LIVEKIT["Hub LiveKit Video/Audio ✅"]
    S2_HUB_C["Sprint 2-C / 4 BLE Device 📋"]
    S3_FW["Sprint 3 Firmware 📋 (Scaffolded)"]
    S4_INTEGRATE["Sprint 4 Hub-PillBox 📋"]
    S5_APP["Sprint 5 Family App 🟢 ~85% (85 tests)"]
    S6_PLATFORM["Sprint 6 Care Platform 📋"]
    S7_SENSORS["Sprint 7 Smart Sensors 📋"]
    S8_PILOT["Sprint 8 Pilot 📋"]

    S0_START --> S1_DELIVER
    S1_DELIVER --> S2_HUB_A
    S1_DELIVER --> S3_FW
    S1_DELIVER --> S5_APP
    S2_HUB_A --> S2_HUB_B
    S2_HUB_B --> S2_HUB_LIVEKIT
    S2_HUB_B --> S2_HUB_C
    S2_HUB_C --> S4_INTEGRATE
    S3_FW --> S4_INTEGRATE
    S2_HUB_LIVEKIT <-->|WebRTC Video/Audio| S5_APP
    S4_INTEGRATE -.-> S5_APP
    S5_APP --> S6_PLATFORM
    S6_PLATFORM --> S7_SENSORS
    S7_SENSORS --> S8_PILOT

    style S0_START fill:#10b981,color:white
    style S1_DELIVER fill:#10b981,color:white
    style S2_HUB_A fill:#10b981,color:white
    style S2_HUB_B fill:#10b981,color:white
    style S2_HUB_LIVEKIT fill:#10b981,color:white
    style S2_HUB_C fill:#3b82f6,color:white
    style S3_FW fill:#3b82f6,color:white
    style S4_INTEGRATE fill:#3b82f6,color:white
    style S5_APP fill:#10b981,color:white
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

## 10. Next Milestones (برنامه عملیاتی و واقع‌بینانه — سپتامبر ۲۰۲۶)

```mermaid
gantt
    title Yara Project — برنامه کوتاه‌مدت و مسیر بحرانی
    dateFormat  YYYY-MM-DD
    section Backend
    Domains + Hardening + LiveKit      :done,    be1, 2026-06-01, 2026-08-28
    Notification Draft Inbox (ADR-015) :done,    be2, 2026-08-01, 2026-08-30
    Phase 2: Licensing + Plans + Billing :active, be3, 2026-09-05, 14d
    section Hub
    II-A Foundation + Room v5          :done,    h1,  2026-06-01, 2026-07-20
    II-B Reminder MVP (ADR-012)        :done,    h2,  2026-07-15, 2026-08-20
    LiveKit Video Call + Ringing       :done,    h3,  2026-08-20, 2026-09-02
    Two-Way Messaging Subsystem        :done,    h4,  2026-09-01, 2026-09-05
    Phase 3: Radio on Elder Hub        :         h5,  2026-09-20, 10d
    section Family App
    Core screens + Care Management     :done,    fa1, 2026-07-01, 2026-08-20
    LiveKit Native Video / Audio Calls :done,    fa2, 2026-08-20, 2026-09-02
    Two-Way Messaging Screen           :done,    fa3, 2026-09-01, 2026-09-05
    Phase 4: Push Notifications        :         fa4, 2026-09-25, 14d
    section Hardware Integration
    ESP32-C3 Firmware (Smart Pill Box) :crit,    hw1, 2026-10-05, 21d
    Hub BLE Driver (Sprint II-C/4)     :crit,    hw2, 2026-10-15, 21d
    Smart Wearable Integration         :         hw3, 2026-11-01, 14d
    section Production Readiness
    Hub Kiosk / LockTask Mode          :         pr1, 2026-11-15, 10d
    Pilot Candidate Ready              :         pr2, 2026-11-25, 14d
```

### اولویت‌های کلیدی جاری (ترتیب نرم‌افزاری و سخت‌افزاری)
1. **فاز ۲ نرم‌افزاری — پلن‌ها، اشتراک و درگاه پرداخت (Licensing & Billing):** تکمیل مدل `Subscription`، ماژول صدور فاکتور و اتصال به درگاه پرداخت در لایه Infrastructure.
2. **فاز ۳ نرم‌افزاری — رادیو در هاب سالمند (Radio inside Elder Hub):** افزودن پخش‌کننده استریم صوتی سبک و رابط کاربری آرامش‌بخش رادیو روی صفحه خانگی هاب.
3. **فاز ۴ نرم‌افزاری — پوش نوتیفیکیشن (Push Notifications - FCM/APNs):** پیاده‌سازی ارائه‌دهنده پوش برای زنگ تماس و هشدارهای فوری در پس‌زمینه.
4. **فاز یکپارچه‌سازی سخت‌افزار (Hardware Integration):**
   - توسعه فریمور جعبه داروی هوشمند (ESP32-C3) با سنسور رید سوئیچ و مانیتورینگ باتری.
   - پیاده‌سازی درایور کلاینت BLE در هاب (جایگزینی `DeferredDeviceActionHandler`).
   - یکپارچه‌سازی دستبند هوشمند (Smart Wearable) برای هشدار سقوط و دکمه اضطراری SOS.
5. **فاز آمادگی تولید (Production Readiness):** فعال‌سازی حالت کیوسک هاب (LockTask / Device Owner)، آزمون پایداری سراسری E2E، و تست پرواز پایلوت.

---

## 11. جدول تطبیق واقعیت‌های فنی پروژه

| موضوع | وضعیت در گزارش قبلی (v1.1) | واقعیت فعلی و به‌روزرسانی (v1.2) |
|---|---|---|
| تماس تصویری / صوتی | 🔧 وابسته به Skyroom با خطای ۵۰۲ | 🟢 مهاجرت کامل به LiveKit v1 (ADR-013)؛ WebRTC نیتیو در Family App و هاب با زنگ ریل‌تایم |
| پیام‌رسانی دوطرفه و پیام صوتی | نامشخص / غیرفعال با پیام موقت | 🟢 پیاده‌سازی کامل پیام‌رسانی دوطرفه (متن، پیام صوتی، عکس، ویدیو) با وضعیت تحویل/خوانده در بک‌اند، هاب و فمیلی اپ |
| تعداد تست‌های بک‌اند | ۳۰۹ مورد تقریبی | ✅ ۳۳۲ تست رسمی با pytest (۱۰۰٪ پاس) در ۱۱ دامنه، معماری و زیرساخت |
| تست‌های Family App | نامشخص در گزارش قبلی | ✅ ۸۵ تست Jest در ۱۳ مجموعه آزمون (۱۰۰٪ پاس) |
| تست‌های Android Hub | نامشخص در گزارش قبلی | ✅ ۱۱۱ تست یونیت ماژولار (۱۰۰٪ پاس) در ۱۱ ماژول گرادل |
| فریمور سخت‌افزار | درخت فریمور وجود ندارد | 📋 ساختار دایرکتوری ایجاد شده، کدنویسی در فاز سخت‌افزار آغاز می‌شود |
| حالت کیوسک هاب (Kiosk) | به عنوان پیش‌نیاز MVP فرض می‌شد | ⏸️ موکول به فاز آمادگی تولید (Production Readiness) جهت تسریع تست و دیباگ |
| هشدارهای مراقب | فقط در سطح تئوری | 🔧 فعال در سطح صندوق هشدارهای درون‌برنامه‌ای (ADR-015) متصل به Workflow و Care |
| سینک هاب | مسیر قدیمی `/api/v1/sync/` | ✅ خط لوله دوگانه `/api/v1/hub/sync/` (نما) و `/api/v1/synchronization/` (چک‌پوینت) |
