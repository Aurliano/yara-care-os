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

# Sprint 2 — Android Hub Runtime (Revised)
Goal

Transform the current Android prototype into the production Hub runtime that implements the frozen Backend architecture while remaining fully offline-first.

Sprint II-A — Foundation & Runtime

Goal

Replace the prototype architecture with the production Hub architecture.
Objectives
Platform Foundation
Multi-module architecture
Dependency Injection
ViewModel architecture
Navigation architecture
Configuration management
Persistence
Room Database
Replica storage
Outbox storage
Replica metadata
Checkpoint persistence
Networking
Retrofit
JWT Authentication
Device Registration
Correlation IDs
Replica IDs
Synchronization
Sync Session client
Delta download
Delta upload
Snapshot support
Checkpoint management
Runtime
Integration Runtime
WorkManager jobs
Boot recovery
Alarm recovery
Runtime lifecycle
Refactoring
Remove Medication aggregate
Remove InMemory repository
Remove Medication CRUD
Preserve UI Design System
Deliverables
Stable Hub architecture
Local replica database
Sync infrastructure
Runtime foundation
Backend connectivity
Exit Criteria
Hub authenticates with Backend.
Replica database survives reboot.
Synchronization session works.
Outbox persists offline.
Integration Runtime runs locally.
Prototype domain removed.

Sprint II-B — Reminder Runtime

Goal

Implement the complete offline reminder runtime using replicated backend domains.
Objectives
Scheduling Runtime
ScheduleDefinition replicas
Local occurrence generation
Alarm scheduling
Boot rescheduling
Workflow Runtime
WorkflowExecution replicas
Action dispatcher
Reminder lifecycle
Retry
Timeout
Escalation
Reminder UI
Today screen from replicas
Reminder screen from WorkflowExecution
Confirmation UI
Active execution UI
Offline Confirmation
Pending evidence queue
Confirmation upload
Idempotent replay
Integration
Hub Confirmation API
Runtime processing
Sync after confirmation
Deliverables
Complete reminder runtime
Offline reminder execution
Workflow confirmations
Evidence queue
End-to-end backend integration
Exit Criteria
Reminder works without internet.
Workflow executes locally.
Confirmation syncs after reconnect.
No local medication logic remains.
Backend reminder flow is fully mirrored.

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

# Sprint 5 — Caregiver App MVP

Goal

Deliver the first caregiver-facing application.

Objectives

- Authentication
- Pair with Elder
- Dashboard
- Medication Status
- Hub Status
- Notifications
- Contacts
- Settings

Deliverables

- Android App
- iOS App (via Expo)
- Push Notifications

Exit Criteria

- Caregivers can monitor an elder remotely.
- Notifications work.
- Hub status is visible.

---

# Sprint 6 — Care Platform

Goal

Expand remote caregiving capabilities.

Objectives

- Medication Management
- Appointment Tracking
- Reminder Configuration
- Timeline
- Activity History
- Subscription Management

Deliverables

- Complete care workflow
- Remote medication management

Exit Criteria

- Daily caregiving tasks can be managed remotely.

---

# Sprint 7 — Smart Home Foundation

Goal

Extend Yara beyond medication reminders.

Objectives

- Power Failure Detection
- Gas Leak Detection
- Sensor Framework
- Alert Escalation
- SMS Backup Notifications

Deliverables

- Sensor integration
- Alert engine

Exit Criteria

- Sensor alerts reach caregivers reliably.

---

# Sprint 8 — Pilot Release

Goal

Prepare the first production-ready pilot.

Objectives

- Bug Fixes
- Performance Optimization
- Security Review
- UX Improvements
- Documentation Cleanup
- Internal Pilot

Deliverables

- Release Candidate
- Deployment Guide
- Installation Guide

Exit Criteria

- MVP ready for pilot deployment.

---

# Future Roadmap

## AI Platform

- AI Care Assistant
- Predictive Analytics
- Personalized Care Suggestions
- Local LLM Support

---

## Communication

- Voice Calls
- Video Calls
- Voice Messages
- Family Timeline

---

## Healthcare

- Doctor Portal
- Nurse Portal
- Health Reports
- Prescription Management

---

## Smart Home

- Smart Camera
- Motion Detection
- Wearables
- Medical Devices
- Environmental Sensors

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