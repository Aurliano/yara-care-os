# Yara Architecture

## Components

```text
                Family App
                     │
              HTTPS / REST API
                     │
               Django Backend
                     │
        ┌────────────┴────────────┐
        │                         │
 Android Hub                PostgreSQL
        │
        │ BLE
        │
 Smart Pill Box
        │
  Power Sensor
  Gas Sensor
```

---

## Android Hub

Responsibilities

- Run in Kiosk Mode
- Medication Reminder
- BLE Communication
- Local Database
- Offline Sync

---

## Family App

Responsibilities

- Elder Management
- Medication Management
- Device Monitoring
- Notifications

---

## Backend

Responsibilities

- Authentication
- Data Synchronization
- Device Management
- Medication Management

---

## Firmware

Responsibilities

- BLE Communication
- Door Detection
- Battery Monitoring
- Sensor Events