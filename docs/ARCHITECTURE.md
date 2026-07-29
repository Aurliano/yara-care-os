# ARCHITECTURE.md

Version: 2.0
Status: Approved
Product: Yara Care Ecosystem

---

# Purpose

This document defines the software architecture of the Yara ecosystem.

It establishes the responsibilities of each component, communication flows, data ownership, synchronization strategy, and architectural constraints.

All implementation decisions must conform to this document.

---

# Architectural Principles

- Offline First
- API First
- Security by Design
- Thin Clients
- Modular Components
- Clean Architecture
- Single Responsibility
- Future Ready
- MVP First

---

# High-Level Architecture

```text
                 Care Layer
        ┌──────────────────────────┐
        │  Caregiver App (Expo RN) │
        │  Future Web Portal       │
        └─────────────┬────────────┘
                      │ HTTPS / REST
                      ▼
        ┌──────────────────────────┐
        │     Cloud Layer          │
        │ Django + DRF             │
        │ PostgreSQL               │
        │ Notification Services    │
        │ Authentication           │
        │ Synchronization          │
        └─────────────┬────────────┘
                      │ HTTPS
                      ▼
        ┌──────────────────────────┐
        │       Hub Layer          │
        │ Kotlin + Compose         │
        │ Room                     │
        │ BLE                      │
        │ Offline Engine           │
        └─────────────┬────────────┘
                      │ BLE
                      ▼
        ┌──────────────────────────┐
        │       IoT Layer          │
        │ ESP32 Smart Pill Box     │
        │ Future Sensors           │
        └──────────────────────────┘
```

---

# System Components

## Caregiver App

Purpose:

Provide caregivers with remote visibility and management.

Responsibilities:

- Authentication
- Dashboard
- Elder overview
- Hub monitoring
- Medication status
- Notifications
- Contact management
- Subscription management

The Caregiver App must remain a **thin client**.

Business rules belong to the backend.

---

## Backend

The backend is the central source of truth.

Responsibilities:

- Authentication
- Authorization
- Elder management
- Caregiver management
- Membership & Roles
- Subscription
- Hub management
- Medication management
- Notification engine
- Synchronization
- Audit logging
- Future AI services

No business logic should be duplicated in clients.

---

## Android Hub

Purpose:

Operate independently inside the elder's home.

Responsibilities:

- Medication reminders
- Local scheduling
- BLE communication
- Offline storage
- Sync with backend
- Device monitoring
- Kiosk mode
- Device Owner
- Background services

The Hub must continue operating without internet connectivity.

---

## Smart Pill Box

Responsibilities:

- BLE communication
- Door events
- Battery reporting
- Pairing
- Medication confirmation

---

# Domain Ownership

| Domain | Owner |
|---------|-------|
| Authentication | Backend |
| Users | Backend |
| Elder | Backend |
| Membership | Backend |
| Subscription | Backend |
| Medication | Backend |
| Hub Configuration | Backend |
| Reminder Execution | Hub |
| BLE State | Hub |
| Pill Box State | Hub |
| Sensor Events | Hub |

---

# Communication

## Caregiver App ↔ Backend

Protocol:

- HTTPS
- REST API
- JWT

---

## Hub ↔ Backend

Protocol:

- HTTPS
- REST API
- JWT

Synchronization:

- Incremental Sync
- Retry Queue
- Conflict Resolution

---

## Hub ↔ Pill Box

Protocol:

- BLE

Communication is local only.

---

# Offline Strategy

The Hub is fully offline capable.

The Caregiver App is online-first with local caching.

Backend is the single source of truth after synchronization.

Medication reminders must never depend on internet connectivity.

---

# Synchronization Strategy

Hub:

Local Room Database

↓

Sync Queue

↓

Backend

↓

Conflict Resolution

↓

Acknowledgement

Synchronization should always be resilient to intermittent connectivity.

---

# Security

Authentication:

JWT

Transport:

TLS

Storage:

Encrypted local storage where appropriate.

Sensitive operations require authenticated backend APIs.

---

# Role Model

One Elder

↓

Many Caregivers

↓

Membership

↓

Role

Possible roles:

- Owner
- Family
- Nurse
- Doctor
- Viewer

Permissions are assigned through Membership, not User.

---

# Future Expansion

The architecture intentionally supports:

- AI Assistant
- Video Communication
- Smart Home
- Medical Devices
- Camera Integration
- Wearables
- OTA Updates
- MQTT
- Web Portal

without requiring major architectural changes.

---

# Non Goals

The architecture is not optimized for:

- Microservices
- Event sourcing
- Kubernetes
- Massive scale
- Premature optimization

These may be introduced only when justified by product growth.

---

# Definition of Good Architecture

A successful architecture is one that:

- remains understandable by a 1–2 person team,
- supports future expansion,
- minimizes coupling,
- maximizes reliability,
- and allows rapid MVP delivery without sacrificing long-term maintainability.