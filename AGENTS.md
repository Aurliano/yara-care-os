# Yara AI Agent Guide

## Read First

Before making any architectural or implementation decision, read:

1. PROJECT_CONTEXT.md
2. BACKLOG.md

These documents are the single source of truth.

---

## Your Goal

Deliver a production-ready MVP.

Do not optimize for theoretical scalability.

Optimize for reliability, maintainability and development speed.

---

## MVP Rules

- Never add features outside the MVP.
- Never change the architecture without discussion.
- Prefer simple solutions.
- Avoid unnecessary abstractions.
- Reuse existing code before creating new modules.
- Ask before adding new dependencies.

---

## Tech Stack

### Android Hub

- Kotlin
- Jetpack Compose
- Room
- WorkManager
- BLE
- Device Owner
- Kiosk Mode

### Family App

- React Native
- Expo
- TypeScript

### Backend

- Django
- Django REST Framework
- PostgreSQL

### Firmware

- ESP32-C3
- Arduino Framework
- NimBLE

---

## Coding Principles

- Keep files small.
- Prefer composition over inheritance.
- Prefer readability over clever code.
- Remove dead code immediately.
- Every feature should be testable.

---

## Product Principles

- MVP First
- Offline First
- Security by Design
- Simplicity over Complexity

---

## When In Doubt

If a decision conflicts with PROJECT_CONTEXT.md,
PROJECT_CONTEXT.md always wins.