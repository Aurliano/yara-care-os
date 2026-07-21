# AGENTS.md

Version: 2.0
Status: Approved

---

# Purpose

This document defines the mandatory working rules for every AI agent and every developer contributing to the Yara project.

These rules apply to:

- ChatGPT
- Claude
- Codex
- Cursor
- GitHub Copilot
- Gemini
- Lovable
- Future AI coding assistants
- Human developers

If any instruction conflicts with this document, this document takes precedence unless explicitly overridden by the project owner.

---

# Read Order

Before generating code, every agent must understand the project by reading the documentation in this order:

1. PROJECT_CONTEXT.md
2. ARCHITECTURE.md
3. BACKLOG.md
4. ROADMAP.md
5. Relevant ADR documents
6. Current Sprint tasks

Never start implementation without understanding the product.

---

# Product Philosophy

Always remember:

Yara is NOT:

- a generic Android application
- a medication reminder
- a hospital system
- a medical device

Yara IS:

- an elderly care ecosystem
- a calm companion
- an offline-first platform
- a long-term product

Every implementation should reinforce these principles.

---

# Engineering Principles

Always prioritize:

- Reliability
- Simplicity
- Maintainability
- Readability
- Testability

Never optimize prematurely.

Never add unnecessary abstractions.

---

# Architecture Rules

Respect component boundaries.

Business logic belongs in the backend.

The Caregiver App is a thin client.

The Hub owns local execution and BLE communication.

Firmware only controls hardware behavior.

Never duplicate business logic across layers.

---

# Technology Stack

## Android Hub

- Kotlin
- Jetpack Compose
- Room
- WorkManager

## Caregiver App

- Expo
- React Native
- TypeScript
- Zustand
- TanStack Query

## Backend

- Django
- Django REST Framework
- PostgreSQL

## Firmware

- ESP32-C3
- Arduino Framework
- NimBLE

Do not introduce new frameworks without approval.

---

# Code Style

Write code that is:

- simple
- modular
- documented when necessary
- easy to review
- production-oriented

Avoid:

- dead code
- commented-out code
- duplicated logic
- large classes
- large functions
- unnecessary inheritance

---

# Documentation Rules

Whenever architecture changes:

Update:

- PROJECT_CONTEXT.md (if affected)
- ARCHITECTURE.md
- Relevant ADR
- BACKLOG.md (if scope changes)
- ROADMAP.md (if planning changes)

Documentation is part of the implementation.

---

# Sprint Rules

Only implement features that belong to the current sprint.

Do not implement future roadmap items unless explicitly requested.

Avoid feature creep.

---

# MVP Rules

During MVP:

Prefer:

- stability
- simplicity
- reliability

Avoid:

- experimental features
- AI integrations
- premature optimizations
- unnecessary UI polish

Deliver working software first.

---

# UI Principles

Always follow:

- Large touch targets
- High contrast
- Minimal navigation
- Clear typography
- Calm interactions
- No distracting animations

The interface must reduce cognitive load for elderly users.

---

# Offline Rules

Never assume internet connectivity.

Medication reminders must always work offline.

The Hub must continue operating without cloud access.

---

# Security Rules

Always:

- validate input
- authenticate users
- authorize requests
- protect sensitive data
- use secure communication

Never hardcode:

- passwords
- tokens
- API keys
- secrets

---

# Git Rules

Every change should be:

- focused
- atomic
- reviewable

Avoid mixing unrelated changes into one commit.

---

# Pull Request Checklist

Before considering a task complete:

- Code builds successfully
- No lint errors
- No obvious warnings
- Documentation updated if required
- Acceptance criteria satisfied

---

# AI Behavior

AI agents should:

- ask questions when requirements are unclear
- avoid making product decisions independently
- explain architectural trade-offs
- follow existing project conventions
- preserve consistency across modules

Never invent APIs, database tables, or workflows that are not documented.

---

# Decision Making

When multiple implementation options exist:

1. Choose the simplest correct solution.
2. Prefer consistency over novelty.
3. Prefer maintainability over cleverness.
4. Prefer product value over technical elegance.

---

# Definition of Success

A successful contribution:

- solves the requested problem,
- keeps the architecture clean,
- preserves product philosophy,
- introduces no unnecessary complexity,
- and leaves the project easier to maintain than before.

---

# Final Rule

Every line of code should answer one question:

"Does this make Yara a more reliable companion for elderly people and their caregivers?"

If the answer is no, reconsider the implementation.