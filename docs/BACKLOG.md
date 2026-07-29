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
- Subscription API
- Notification API
- Audit Log API

---

# Epic 3 — Android Hub

Sprint 2

Priority: P0

## Features

- Device Owner
- Kiosk Mode
- Auto Boot
- Offline Engine
- Room Database
- Medication Reminder
- BLE Manager
- Hub Status
- Sync Queue

Note:

The Hub project already exists.

This sprint focuses on integration and completion rather than building from scratch.

---

# Epic 4 — Firmware

Sprint 3

Priority: P0

## Features

- ESP32-C3 Firmware
- BLE
- Pairing
- Reed Switch Detection
- Battery Monitoring

---

# Epic 5 — Hub Integration

Sprint 4

Priority: P0

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
- Push Notifications
- Settings

The Caregiver App is a thin client.

Business logic belongs to the backend.

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

---

## Communication

- Voice Calls
- Video Calls
- Voice Messages

---

## Healthcare

- Doctor Portal
- Nurse Portal
- Health Reports

---

## Smart Home

- Camera
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