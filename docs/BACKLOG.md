# BACKLOG.md

Version: 2.0
Status: Approved
Product: Yara Care Ecosystem

---

# Purpose

This document defines the official MVP backlog.

Only items listed in this document are considered part of the MVP.

Features outside this backlog must not be implemented without explicit approval.

---

# Priority Levels

P0 → Critical

Required for MVP.

---

P1 → High

Important.

Can be implemented immediately after MVP.

---

P2 → Medium

Future improvements.

---

P3 → Future

Long-term vision.

---

# Epic 1 — Platform Foundation

Sprint 0–1

Priority: P0

## Features

- Product Documentation
- Architecture
- ADRs
- Repository Structure
- CI/CD
- API Standards
- Database Design
- Authentication Foundation

---

# Epic 2 — Backend Platform

Sprint 1

Priority: P0

## Features

- Authentication API
- Elder API
- Caregiver API
- Membership API
- Hub API
- Medication API
- In-App Caregiver Alerts API (ADR-015)
- Audit Log API
- Communication Sessions API (ADR-011, ADR-013 LiveKit token minting & call lifecycle)
- Two-Way Messaging Subsystem API (Messages & Attachments: Text, Voice Message, Image, Video)

Note:
Subscription model and Billing/Payment Gateway are scheduled for Phase 2 (Licensing & Billing).

---

# Epic 3 — Android Hub

Sprint 2

Priority: P0

## Features

- Auto Boot
- Offline Engine
- Room Database
- Medication Reminder (ADR-012)
- BLE Manager (Stub / interface ready; full hardware in Hardware Integration Phase)
- Hub Status
- Sync Queue
- LiveKit Audio/Video Calling (ADR-011/013, LiveKit SDK, incoming/outgoing screens, ringing)
- Two-Way Messaging Subsystem (Room DB sync, audio playback/recording, attachments)

Note:
The Hub project already exists.
Device Owner / Kiosk Mode (LockTask) is explicitly postponed to Production Readiness / Deployment Hardening to avoid blocking development and interactive testing.

---

# Epic 4 — Firmware

Sprint 3

Priority: P0 (Hardware Integration Phase)

## Features

- ESP32-C3 Firmware
- BLE
- Pairing
- Reed Switch Detection
- Battery Monitoring

---

# Epic 5 — Hub Integration

Sprint 4

Priority: P0 (Hardware Integration Phase)

## Features

- Hub ↔ Pill Box Communication
- Medication Confirmation
- BLE Recovery
- Battery Synchronization
- Device Health

---

# Epic 6 — Caregiver App

Sprint 5

Priority: P0

## Features

- Login
- Pair Hub
- Dashboard
- Medication Status
- Hub Status
- Contacts
- In-App Caregiver Alert Inbox (ADR-015)
- LiveKit Audio/Video Calling (LiveKit WebRTC, ringing, call screens)
- Two-Way Messaging Subsystem (Messages screen, voice message recording, attachments)
- Settings

Note:
Push Notifications (FCM/APNs) are scheduled for Software Phase 4. ADR-015 In-App Alert Inbox is the active MVP notification mechanism.
The Caregiver App is a thin client. Business logic belongs to the backend.

---

# Epic 7 — Care Platform

Sprint 6

Priority: P1

## Features

- Medication Management
- Appointments
- Reminder Management
- Timeline
- Activity History
- Subscription Management

---

# Epic 8 — Smart Sensors

Sprint 7

Priority: P1

## Features

- Power Failure Detection
- Gas Leak Detection
- Alert Escalation
- SMS Notification (Backend)

---

# Epic 9 — Pilot Release

Sprint 8

Priority: P0

## Features

- Bug Fixes
- Performance
- Security Review
- UX Improvements
- Internal Pilot
- Release Candidate

---

# Future Backlog

Priority: P3

## AI

- AI Care Assistant
- Predictive Analytics
- Local LLM

## Smart Home & Sensors

- Ambient Camera Streaming (Passive 24/7 room monitoring / CCTV)
- Motion Sensors
- Wearables
- Medical Devices

---

## Marketplace

- Device Store
- AI Services
- Healthcare Services
- Rental Management

---

# Definition of Ready

A feature may enter development only if:

- Product goal is clear.
- UI flow is defined.
- API contract exists (if applicable).
- Acceptance criteria are written.
- Dependencies are identified.

---

# Definition of Done

A feature is complete only if:

- Code is implemented.
- Reviewed.
- Tested.
- Integrated.
- Documented when necessary.
- No known blocking issues remain.

---

# Backlog Rules

- Finish the MVP before adding new features.
- Never implement P2 or P3 items while P0 items remain incomplete.
- Avoid feature creep.
- Keep the backlog aligned with PROJECT_CONTEXT.md and ARCHITECTURE.md.
- Optimize for delivering a reliable product, not the largest feature list.

---

# Technical Debt Register

## TD-MSG-001 — Unified Sync Domain Migration for Messaging
- **Component:** Hub Messaging Polling vs Unified Sync Architecture (`Session`, `Delta`, `Checkpoint`)
- **Current State:** Phase 1 asynchronous messaging uses an adaptive checkpointed polling bridge (`syncElderMessages` with `since` delta and exponential backoff) in `HomeViewModel`. Outbox dispatch is opportunistic immediate-dispatch with durable fallback to `UploadSessionRunner`.
- **Target Architecture:** Migrate incoming messaging events from the polling bridge into the unified Synchronization Domain Session/Checkpoint model or unified server-sent event stream (`MessageCreated` / `MessageDelivered`).
- **Priority:** P1 (Post-MVP / Next Phase)
- **Status:** Documented & Tracked