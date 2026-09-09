# ROADMAP.md

Version: 5.0
Status: Approved
Product: Yara Care Ecosystem

---

# Purpose

This roadmap defines the strategic development plan for the Yara Care Ecosystem.

Its purpose is to:

- Deliver a stable MVP as quickly as possible.
- Build a scalable architecture from day one.
- Reduce technical risk early.
- Ensure every sprint produces measurable product value.

The roadmap reflects the current architecture, technology stack, and product vision defined in:

- PROJECT_CONTEXT.md
- ARCHITECTURE.md
- BACKLOG.md

---

# Development Principles

Every sprint should:

- Deliver a usable outcome.
- Reduce project risk.
- Keep the system deployable.
- Avoid unnecessary complexity.
- Preserve clean architecture.

Priority order:

1. Reliability
2. Product Value
3. Maintainability
4. Performance
5. New Features

---

# Sprint 0 — Product Foundation ✅ Completed

Goal

Establish a solid foundation before implementation begins.

Objectives

- Finalize Product Vision
- Finalize Architecture
- Define ADRs
- Define Technology Stack
- Repository Structure
- CI/CD
- Coding Standards
- Documentation
- Database Modeling
- API Standards

Deliverables

- PROJECT_CONTEXT.md
- ARCHITECTURE.md
- BACKLOG.md
- ROADMAP.md
- AGENTS.md
- Initial ADR documents
- Git Repository
- CI Pipeline

Exit Criteria

- Documentation approved.
- Repository ready.
- Architecture frozen.
- Development standards established.

---

# Sprint 1 — Platform Foundation  ✅ Completed

Goal

Build the backend foundation that every client depends on.

Objectives

- Django Project
- DRF Setup
- PostgreSQL
- Authentication
- User Management
- Elder Management
- Membership Model
- Subscription Model
- Initial REST APIs

Deliverables

- Authentication APIs
- Elder APIs
- Membership APIs
- Hub APIs
- Database Schema
- API Documentation

Exit Criteria

- Backend is operational.
- Authentication works.
- API contracts are stable.

---

# Sprint 2 — Android Hub Runtime ✅ Substantially Complete (~85%)
Goal

Transform the Android prototype into the production Hub runtime that implements the frozen Backend architecture while remaining fully offline-first.

### Sprint II-A — Foundation & Runtime ✅ Completed
- Platform Foundation: 11-module Gradle architecture, Hilt DI, ViewModel, Navigation, Configuration
- Persistence: Room Database v5, replica storage, outbox storage, monotonic checkpoints
- Networking: Retrofit, JWT authentication, replica identifiers (`X-Replica-ID`, `X-Device-ID`, `X-Correlation-ID`)
- Synchronization: Sync Session client, incremental delta download/upload, staging database, selective refresh
- Runtime: Integration Runtime, WorkManager jobs, Boot receiver recovery, alarm recovery

### Sprint II-B — Reminder Runtime ✅ Completed (ADR-012)
- Scheduling Runtime: ScheduleDefinition replicas, local occurrence generation, alarm coordinator
- Workflow Runtime: WorkflowExecution replicas, Action Dispatcher, reminder lifecycle, local postpone
- Reminder UI: Today screen from replicas, reminder screen, elder confirmation UI, 15-minute card retention
- Offline Confirmation: Pending evidence queue, outbox upload, idempotent replay

### Communication Runtime (LiveKit WebRTC) ✅ Completed (ADR-013)
- LiveKit WebRTC engine (`LivekitCallEngine`), token consumption, call state machine
- Real-time elder calling UI: Incoming call ringer, outgoing call, talking screen, mute/speaker/camera controls

### Two-Way Messaging Subsystem ✅ Completed
- Hub Messaging Repository (`MessagingRepositoryImpl`) & Room Message storage (`MessageDao`)
- Text, Voice Message, Image, and Video messaging support with delivery/read receipts

### Sprint II-C — Device BLE Runtime 🔜 Planned (Deferred to Hardware Phase)
- BLE GATT client runtime, pairing handshake, compartment sensor integration (`DeferredDeviceActionHandler` currently active)

### Kiosk Mode / Device Owner ⏸️ Postponed (Moved to Production Readiness)
- Android LockTask mode and Device Owner provisioning temporarily postponed to Production Readiness so as not to impede ongoing development, debugging, and testing.

---

# Sprint 3 — Firmware MVP

Goal

Develop the Smart Pill Box firmware.

Objectives

- ESP32-C3 Firmware
- BLE Communication
- Pairing
- Reed Switch Detection
- Battery Monitoring
- Power Optimization

Deliverables

- Firmware
- BLE Protocol
- Pairing Process

Exit Criteria

- Pill Box pairs successfully.
- Door events are detected.
- Battery status is reported.

---

# Sprint 4 — Hub ↔ Pill Box Integration

Goal

Integrate Hub and hardware into a single working system.

Objectives

- BLE Integration
- Medication Confirmation
- Retry Logic
- Battery Synchronization
- Device Health Monitoring

Deliverables

- Complete BLE workflow
- Medication confirmation pipeline
- Stable reconnection logic

Exit Criteria

- Hub and Pill Box operate reliably together.

---

# Sprint 5 — Caregiver App (Family App) MVP ✅ Substantially Complete (~85%)

Goal

Deliver the first caregiver-facing application with full monitoring, communication, and messaging capabilities.

Objectives

- Authentication & Account Management ✅
- Pair with Elder & Multi-caregiver Memberships ✅
- Dashboard & Daily Care Status ✅
- Medication Management (Create, Edit, Schedule) ✅
- Hub & Peripheral Device Status ✅
- Real-Time LiveKit Video & Audio Calling ✅
- Two-Way Messaging (Text, Voice Message, Image, Video) ✅
- In-App Caregiver Alerts (ADR-015) ✅
- Push Notifications (FCM / APNs) 🔜 Planned (Software Phase 4)

Deliverables

- Expo / React Native App (Android & iOS)
- Native WebRTC calling engine via LiveKit
- Two-way messaging with audio/video/image attachments
- In-app alert inbox

Exit Criteria

- Caregivers can monitor an elder remotely.
- LiveKit calls connect reliably between Family App and Hub.
- Two-way messages sync across devices.
- In-app alerts notify caregivers of late/missed doses.

---

# Current Expected Product Roadmap

The software capabilities are prioritized ahead of physical hardware to establish a rock-solid cloud and client foundation:

```text
Phase 2: Licensing + Plans + Billing + Payment
                   │
                   ▼
Phase 3: Radio inside Elder Hub
                   │
                   ▼
Phase 4: Push Notifications (FCM / APNs)
                   │
                   ▼
Hardware Integration: Smart Pill Box & Wearable
                   │
                   ▼
Production Readiness: Kiosk Mode, E2E Reliability, Pilot Deployment
```

## Software Completion Roadmap

### Phase 2 — Licensing-based Plans + Billing + Payment 🔄 (In Progress)
- **Goal:** Commercialize the platform and bind subscription lifecycles to elder profiles.
- **Progress:**
  - Stage 0 — complete (ADR-016 & Frozen Domain Contracts)
  - Stage 1 — complete (`Subscription` aggregate in Licensing domain)
  - Stage 2 — complete (`domains.billing` supporting domain foundation: `Invoice`, `PlanPrice`, `PaymentAttempt`)
  - Stage 3 — complete (`infrastructure.payment` provider abstraction & ZarinPal adapter)
  - Stage 4 — complete (`application.payments` coordinator, REST API, & `PaymentSucceeded` domain event outbox)
  - Stage 5 — pending (Family App Subscription & checkout flow)

### Phase 3 — Radio inside Elder Hub 🔜
- **Goal:** Deliver a calm, companion entertainment feature for the elder directly on the Hub.
- **Objectives:**
  - Streaming audio player engine in Hub runtime.
  - Elder-friendly Radio UI on Hub Home screen.
  - Station management and fallback streams.

### Phase 4 — Push Notifications 🔜
- **Goal:** Provide reliable background alerting and remote call ringing.
- **Objectives:**
  - Notification provider integration (FCM for Android, APNs for iOS) in `backend/infrastructure/notification/`.
  - Device token registration in Identity / Notification domain.
  - Background call ringing and urgent missed-dose push delivery.

---

# Hardware Integration Phase

### 1. Smart Pill Box (Firmware & Hub BLE Integration)
- **Sprint 3 — Firmware MVP (ESP32-C3):**
  - ESP32-C3 firmware implementation (`firmware/pillbox`).
  - BLE GATT service, Reed switch open/close detection, battery ADC monitoring, low-power sleep.
- **Sprint 4 — Hub ↔ Pill Box Integration:**
  - Implement Hub BLE Central driver in `apps/hub/runtime` (replace `DeferredDeviceActionHandler`).
  - Hardware confirmation pipeline: `OPEN_COMPARTMENT` $\rightarrow$ BLE command $\rightarrow$ Door Closed $\rightarrow$ Hardware Evidence $\rightarrow$ Care `MedicationTaken`.

### 2. Smart Wearable Integration
- BLE pairing and connection management.
- Emergency SOS button trigger $\rightarrow$ initiates priority call via Communication domain.
- Vital alert delivery $\rightarrow$ caregiver notification for critical anomalies.

---

# Production Readiness & Deployment Hardening

Prior to pilot release:

- **Hub Kiosk Mode / Android LockTask:** Enable Device Owner provisioning and pin app to prevent accidental elder exit.
- **Real-Time Reliability:** LiveKit reconnection resilience and network handover testing.
- **Background Behavior:** Android Doze mode and WorkManager recovery hardening.
- **Offline/Online Recovery:** Stress-testing multi-day offline queue drain and monotonic checkpoint advance.
- **Comprehensive E2E Testing & Bug Fixing.**
- **Pilot Deployment Preparation.**

---

# Future Roadmap

## AI Platform

- AI Care Assistant
- Predictive Analytics
- Personalized Care Suggestions
- Local LLM Support

---

## Communication (Future Additions)

- Group Calling (Multi-caregiver conference)
- Family Timeline / Story Sharing
- Transcription & Call Summaries

---

## Healthcare

- Doctor Portal
- Nurse Portal
- Health Reports & Trends
- Prescription Management Expansion

---

## Smart Home

- Environmental Sensors (Gas leak, power failure)
- Smart Camera
- Motion Detection

---

## Marketplace

- Device Marketplace
- Healthcare Services
- AI Extensions
- Subscription Marketplace
- Rental Management

---

# Success Metrics

The MVP is considered successful when:

- Medication reminders operate reliably.
- Hub remains functional without internet.
- Caregivers receive timely notifications.
- BLE communication is stable.
- Installation is simple.
- The architecture supports future expansion.

---

# Roadmap Rules

- Complete one sprint before starting the next.
- Do not skip architectural dependencies.
- Do not introduce future features into MVP sprints.
- Reassess priorities only after sprint completion.
- Keep documentation synchronized with implementation.

---

# Long-Term Vision

Yara is not intended to become just another healthcare application.

The long-term vision is to build a complete elderly care ecosystem where:

- One Elder
- One Hub
- One Subscription
- Multiple Caregivers
- Multiple Smart Devices
- One Unified Platform

Yara should evolve into the trusted operating system for independent elderly living, combining AI, IoT, cloud services, and human-centered design under a single, reliable ecosystem.