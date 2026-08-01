# ARCHITECTURE.md

Version: 3.0
Status: Approved
Product: Yara Care Ecosystem

---

# Purpose

This document defines the software architecture of the Yara ecosystem.

It establishes:

- System architecture
- Domain ownership
- Integration boundaries
- Synchronization strategy
- Communication flows
- Offline-first behavior
- Architectural constraints

All implementation decisions must conform to this document.

The detailed business behavior of each domain is defined by its Frozen Contract.

---

# Architectural Principles

- Offline First
- API First
- Security by Design
- Thin Clients
- Domain Driven Design
- Event Driven Architecture
- Clean Architecture
- Single Responsibility
- Modular Components
- Future Ready
- MVP First

---

# High-Level Architecture

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
        │ Integration Runtime      │
        │ Event Engine             │
        │ Synchronization          │
        └─────────────┬────────────┘
                      │ HTTPS
                      ▼
        ┌──────────────────────────┐
        │       Hub Layer          │
        │ Kotlin + Compose         │
        │ Room                     │
        │ Offline Engine           │
        │ BLE                      │
        └─────────────┬────────────┘
                      │ BLE
                      ▼
        ┌──────────────────────────┐
        │       IoT Layer          │
        │ ESP32 Smart Pill Box     │
        │ Future Sensors           │
        └──────────────────────────┘

---

# Backend Domain Architecture

The backend is composed of independent domains.

Current domains:

- Identity & Access
- Licensing
- Event
- Scheduling
- Workflow
- Care
- Device
- Communication
- Synchronization
- Integration

Each domain owns:

- its data
- its business rules
- its public services

Domains communicate only through:

- Public Services
- Published Events
- Integration Orchestration

Direct cross-domain ORM access is prohibited.

---

# Integration Layer

Integration coordinates domains.

Responsibilities:

- Consume domain events
- Call public services
- Route Hub callbacks
- Dispatch workflow actions
- Submit synchronization payloads
- Runtime orchestration

Integration owns no business rules.

Business meaning remains inside domain services.

---

# Event Architecture

Events represent immutable facts.

The Event domain:

- stores facts
- provides querying
- supports transactional outbox

It never:

- executes workflows
- performs business logic
- routes notifications
- synchronizes replicas

Event consumers live outside the Event domain.

---

# Synchronization Architecture

Synchronization owns replication only.

Responsibilities:

- replica management
- checkpoint management
- delta application
- conflict detection
- synchronization sessions

Business domains generate synchronization payloads.

Synchronization never reads business aggregates directly.

Synchronization never interprets business meaning.

---

# Runtime Flow

Typical medication reminder flow:

Scheduling

↓

Workflow

↓

Care

↓

Integration

↓

Device / Communication

↓

Workflow Confirmation

↓

Care Interpretation

↓

Synchronization

---

# System Components

## Caregiver App

Responsibilities:

- Authentication
- Dashboard
- Elder overview
- Hub monitoring
- Medication status
- Notifications
- Contact management
- Subscription management

Business rules belong to the backend.

---

## Backend

The backend is the single source of truth.

Responsibilities:

- Authentication
- Authorization
- Care Management
- Scheduling
- Workflow Execution
- Device Management
- Communication
- Synchronization
- Integration Runtime
- Future AI Services

---

## Android Hub

Responsibilities:

- Reminder execution
- Offline scheduling
- Local workflow execution
- BLE communication
- Device monitoring
- Synchronization
- Local persistence
- Kiosk mode

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

| Capability | Owner |
|------------|-------|
| Identity | Identity & Access |
| Permissions | Identity & Access |
| Licensing | Licensing |
| Scheduling | Scheduling |
| Workflow Execution | Workflow |
| Care Meaning | Care |
| Device State | Device |
| Communication | Communication |
| Replication | Synchronization |
| Orchestration | Integration |
| Immutable Facts | Event |

---

# Communication

## Caregiver App ↔ Backend

- HTTPS
- REST API
- JWT

---

## Hub ↔ Backend

- HTTPS
- REST API
- JWT

Synchronization:

- Incremental Delta Sync
- Checkpoints
- Conflict Detection
- Retry
- Resume

---

## Hub ↔ Pill Box

BLE only.

No cloud communication.

---

# Offline Strategy

Backend remains the source of truth.

Hub is capable of autonomous operation.

Workflow execution must continue offline.

Synchronization reconciles changes after connectivity returns.

---

# Security

Authentication

JWT

Authorization

Permission-based Membership model

Transport

TLS

Storage

Encrypted where appropriate

---

# Architectural Constraints

Allowed domain communication:

- Public Services
- Domain Events
- Integration Layer

Forbidden:

- Cross-domain ORM access
- Cross-domain foreign keys unless explicitly approved
- Business logic inside Integration
- Business logic inside Synchronization
- Business logic inside Event

---

# Future Expansion

Designed to support:

- AI Assistant
- Video Calls
- Smart Home
- Medical Devices
- Wearables
- OTA
- MQTT
- Web Portal
- Multi-Hub

without major architectural redesign.

---

# Non Goals

The architecture is intentionally not optimized for:

- Microservices
- Event Sourcing
- Kubernetes
- Massive Scale
- Premature Optimization

---

# Definition of Good Architecture

A successful architecture:

- is understandable by a small team
- supports future expansion
- minimizes coupling
- maximizes reliability
- keeps domains independent
- supports offline-first operation
- enables rapid MVP delivery