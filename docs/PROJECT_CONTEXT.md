# PROJECT_CONTEXT.md

Version: 2.1
Status: Approved
Product: Yara Care Ecosystem
Company: SAYDA Technology
Last Updated: 2026-09-09

---

# Purpose

This document is the single source of truth for the Yara project.

Every architectural decision, implementation detail, roadmap item, backlog task and AI-generated code must align with this document.

If another document conflicts with PROJECT_CONTEXT.md, this document always takes precedence.

---

# What is Yara?

Yara is an AI-powered elderly care ecosystem.

It combines hardware, software and cloud services into one integrated platform that enables families to care for elderly loved ones remotely.

Yara is built around one simple goal:

> Help elderly people live independently while giving their families peace of mind.

---

# Product Vision

Yara is NOT:

- a medication reminder
- a tablet application
- another Android app
- a hospital management system
- a social network

Yara IS:

- an elderly care platform
- a connected hardware ecosystem
- a trusted daily companion
- a remote caregiving solution
- a long-term healthcare platform

---

# Product Philosophy

Technology should remain invisible.

Care should remain visible.

Every feature must satisfy at least one of these goals:

- Reduce caregiver anxiety.
- Increase elder independence.
- Improve quality of care.
- Simplify communication.
- Reduce caregiving costs.

If a feature does not satisfy any of these goals, it does not belong in Yara.

---

# Design Principles

## Elder First

Technology adapts to the elder.

Never the opposite.

---

## Simplicity First

Every interaction should feel calm and effortless.

---

## Trust Before Intelligence

Reliability is more valuable than advanced AI.

---

## Offline First

The system must continue operating during internet outages.

Medication reminders must never depend on cloud availability.

---

## Privacy by Design

Respecting the elder's dignity is mandatory.

Monitoring capabilities should always be transparent and configurable.

---

## Security by Design

Security is part of the architecture.

Never an afterthought.

---

## Platform Thinking

Every component should strengthen the ecosystem.

Avoid isolated features.

---

# Ecosystem

Yara consists of four logical layers.

```text
                Care Layer
         (Caregiver Applications)

                     │

                Cloud Layer
        (Backend + AI + Services)

                     │

                 Hub Layer
      (Android Dedicated Device)

                     │

                 IoT Layer
 (Pill Box + Sensors + Future Devices)
```

---

# Components

## Android Hub

Dedicated Android appliance installed in the elder's home.

Responsibilities:

- Medication reminders
- Daily interaction
- Offline operation
- BLE communication
- Device monitoring
- Local storage
- Cloud synchronization

The Hub is NOT a consumer Android application.

It behaves more like an ATM or POS terminal than a traditional mobile app.

---

## Caregiver App

A modern mobile application used by family members and caregivers.

Responsibilities:

- Dashboard
- Elder management
- Medication overview
- Device monitoring
- Notifications
- Communication
- Subscription management

This application is a thin client.

Business logic belongs to the backend.

---

## Backend

Central platform responsible for:

- Authentication
- Authorization
- Synchronization
- Notifications
- Subscription
- Device management
- Caregiver management
- APIs
- Future AI services

---

## Smart Pill Box

ESP32-C3 based BLE device.

Responsibilities:

- Door detection
- Battery monitoring
- BLE communication
- Medication confirmation

---

## Future Devices

Future hardware may include:

- Power Sensor
- Gas Sensor
- Smart Camera
- Wearables
- Medical Devices

The current architecture must support future expansion without major redesign.

---

# Care Model

One Elder

↓

One Subscription

↓

One Hub

↓

Multiple Caregivers

Each caregiver has an independent account.

Permissions are determined by the relationship with the elder.

Possible roles include:

- Owner
- Family
- Nurse
- Doctor
- Viewer

Roles belong to the membership between a caregiver and an elder.

They are not global user roles.

---

# Current Technology Stack

## Android Hub

- Kotlin
- Jetpack Compose
- Room
- WorkManager
- BLE
- LiveKit WebRTC (Audio/Video Calling)
- Local Audio/Media Playback & Storage
- Device Owner / Kiosk Mode (Postponed to Production Readiness)

---

## Caregiver App

- Expo
- React Native
- TypeScript
- Zustand
- TanStack Query
- Axios
- React Navigation
- MMKV
- LiveKit Native WebRTC

---

## Backend

- Django
- Django REST Framework
- PostgreSQL
- LiveKit Server Token Provider

---

## Firmware

- ESP32-C3
- Arduino Framework
- NimBLE

---

# Development Principles

The project prioritizes:

- Reliability
- Simplicity
- Maintainability
- Fast iteration
- Clean architecture

Not:

- unnecessary abstractions
- premature optimization
- over-engineering

---

# Current Project Status

**Phase 2 (Licensing & Billing) is CLOSED.** All 6 stages accepted. Backend is mature and well-tested (419 tests green).

**Current phase: Phase 3 — MVP Core Stabilization & Elder UX.**

### Component Maturity

| Component | Status | Notes |
|-----------|--------|-------|
| Backend | Mature | All domains implemented, 419 tests green, Phase 2 complete |
| Family App | Substantially complete, needs stabilization | Core flows work but known bugs in messaging and medication screens |
| Android Hub | Substantially complete (~85%) | Runtime, sync, calling, messaging implemented; needs real device validation |
| Firmware | Scaffold only | ESP32-C3 scaffolded; Hub↔PillBox integration deferred to Hardware Phase |

### Known Issues Requiring Stabilization

- Messaging bugs (Family App and Hub)
- Medication / Reminder bugs
- No real device validation completed yet
- UI not yet hardened for elder users (RTL, accessibility, font sizes)
- TD-MSG-001: Messaging polling bridge should migrate to unified Sync architecture

### Current Focus

Phase 3 prioritizes stabilization over new features:

1. Fix core flow bugs (messaging, medication, reminders)
2. Validate on real devices (Hub + Family App)
3. Harden elder-facing UX (RTL, accessibility, simplicity)

New feature development (Radio, Push Notifications) is deferred until core flows are stable.

---

# Core Architectural Clarifications & Exceptions

## 1. LiveKit Real-Time Media Transport Exception
Real-time media transport (LiveKit) is an approved architectural exception via the Communication provider abstraction:

```text
Family App / Hub  ──(Credentials / Session Control)──►  Backend
        │                                                  │
        │                                        (Issues Opaque Token)
        ▼                                                  ▼
LiveKit Server    ◄────────────(Direct Media)──────────────┘
```

- Backend owns session lifecycle, participant validation, and token minting (`joinToken`).
- Backend does NOT proxy media traffic.
- Hub and Family App speak only to Backend for session control, receive opaque join credentials, and never call LiveKit REST administration APIs or hold vendor API secrets.
- Real-time media streams peer-to-server directly through LiveKit WebRTC.

## 2. Calling vs. Two-Way Messaging
- **Two-way messaging is part of MVP:** Supports Text, Voice Messages, Images, and Videos.
- **Voice Message is NOT a Voice Call (`Voice Message != Voice Call`):**
  - A *Voice Call* is a synchronous, real-time `CommunicationSession` using LiveKit audio tracks.
  - A *Voice Message* is an asynchronous, stored media recording attached to a `Message` aggregate with sender, recipient, duration, delivered, and read status.
- Messaging and Calling have separate aggregates, state machines, and lifecycles.

## 3. Kiosk Mode Postponement
- Kiosk Mode / Android LockTask mode has been temporarily postponed from the daily active MVP to **Production Readiness & Deployment Hardening**.
- This enables fast QA, testing, and debugging on commercial hardware while preserving the appliance architectural model.

---

# MVP Scope

The MVP includes:

### Android Hub
- Offline Storage & Replicas (Room)
- Offline Reminder Execution & Local Postpone
- Synchronization Runtime (Deltas, Checkpoints, Outbox)
- Real-Time LiveKit Video & Audio Calling (ADR-013)
- Two-Way Messaging (Text, Voice Message, Image, Video)
- Local Audio Caching & Playback
- BLE Device Driver (Hardware Integration phase)

### Backend
- Authentication & Identity & Access (Users, Elders, Memberships, Invitations)
- Care Domain (CareActivities, Prescriptions, CareCompletions)
- Scheduling Domain (ScheduleDefinitions, Recurrence, Occurrences)
- Workflow Engine (WorkflowDefinitions, Executions, Evidence Evaluation)
- Communication Domain (Contacts, Sessions, LiveKit Token Provider)
- Two-Way Messaging Subsystem (Messages, Attachments, Media Storage)
- Event Store & Transactional Outbox
- Synchronization Engine & Hub Sync Facade
- In-App Caregiver Alert Inbox (ADR-015)
- Licensing Domain (Plan, Entitlement, License, Subscription)
- Billing Domain (Invoice, InvoiceLineItem, PaymentAttempt, PlanPrice)
- Payment Provider Infrastructure (Provider Port, ZarinPal Adapter, FakePaymentProvider)
- Payment Application Coordinator (Checkout, Settlement, Subscription Activation, PaymentSucceeded Event)

### Caregiver App (Family App)
- Authentication & Login (Phone / Password / OTP)
- Elder Selection & Caregiver Memberships
- Dashboard & Today Care Overview
- Medication Management (Create, Edit, Schedule)
- Hub & Device Health Overview
- Real-Time LiveKit Video & Audio Calling
- Two-Way Messaging (Text, Voice Message, Image, Video)
- Contacts & Emergency Recipients
- In-App Alert Center (ADR-015)
- Subscription Management & Payment Checkout (Two-step checkout, server-authoritative pricing, ZarinPal gateway redirect)

### Smart Pill Box (Hardware Integration Phase)
- ESP32-C3 Firmware
- BLE Pairing with Hub
- Compartment Reed Switch Open/Close Detection
- Battery Monitoring

---

# Out of Scope (MVP) / Planned Later

The following features are intentionally excluded from MVP:

- Kiosk Mode / Android LockTask (Postponed to Production Readiness)
- Push Notifications (FCM / APNs — Planned Phase 4)
- Radio inside Elder Hub (Deferred until after MVP stabilization)
- Ambient Camera Streaming (Passive 24/7 room surveillance / CCTV — distinct from interactive Video Calling)
- Smart Home Integration (Gas leak, power failure environmental sensors)
- Medical Device & Continuous Wearable Telemetry (Doctor portal, continuous ECG/vitals graphs)
- AI Care Assistant / Voice Assistant / Local LLM
- Predictive Health Analytics

These belong to future releases.

---

# Definition of Success

The MVP succeeds when:

- Families trust the system.
- Medication adherence improves.
- The Hub operates reliably.
- Caregivers understand the elder's status within seconds.
- The platform can scale without architectural redesign.

---

# Definition of Failure

The project fails if:

- Reliability is sacrificed for features.
- Complexity increases without clear value.
- The elder becomes confused by the interface.
- Core medication workflows become dependent on internet connectivity.
- New features compromise maintainability.

---

# Golden Rules

Before implementing any feature, always ask:

1. Does this reduce caregiver anxiety?
2. Does this preserve elder independence?
3. Does this fit the product philosophy?
4. Can it work offline when required?
5. Is it simple enough for long-term maintenance by a small team?

If the answer to any of these questions is "No", the implementation should be reconsidered.

---

# Long-Term Vision

Yara aims to become the trusted operating system for elderly care.

One ecosystem.

One platform.

One subscription.

Multiple caregivers.

Connected devices.

Human-centered technology.

Built under the SAYDA brand.