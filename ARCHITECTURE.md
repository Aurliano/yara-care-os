# Yara Architecture

## High-Level Overview

```
                Family App
          (React Native + Expo)
                     │
             HTTPS / REST API
                     │
        Django REST Backend
                     │
              PostgreSQL
                     │
────────────────────────────────────
                     │
             Android Hub
       (Kotlin + Jetpack Compose)
                     │
          Local Room Database
                     │
                BLE Connection
                     │
            ESP32 Smart Pill Box
                     │
      Power Sensor / Gas Sensor
```

---

## Components

### Android Hub

Responsibilities

- Kiosk Mode
- Device Owner
- Medication Reminder
- BLE Communication
- Local Room Database
- Offline Synchronization
- Device Health Monitoring
- Background Services

---

### Family App

Responsibilities

- Authentication
- Elder Management
- Medication Management
- Device Monitoring
- Notifications

---

### Backend

Responsibilities

- Authentication
- Data Synchronization
- Medication Management
- Device Management
- Notification Services

---

### Firmware

Responsibilities

- BLE Communication
- Door Detection
- Battery Monitoring
- Sensor Events

---

## Communication

### Hub ↔ Backend

- HTTPS
- REST API
- JWT
- TLS

### Hub ↔ Pill Box

- BLE

### Backend → Family

- Firebase Cloud Messaging

---

## Storage

### Hub

Room (SQLite)

### Backend

PostgreSQL

---

## Design Principles

- Offline First
- Security by Design
- Dedicated Hardware
- Native Android Hub
- Simple Architecture
- Modular Components

---

## Out of Scope (MVP)

- AI Assistant
- OTA Updates
- MQTT
- Redis
- Celery
- Medical Devices
- Smart Home Integration