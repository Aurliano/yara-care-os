# Project Context
This document is the single source of truth for every AI agent and developer working on Yara.

If any implementation conflicts with this document, this document wins.

## Product

Yara is a smart care platform.

It is NOT just a mobile application.

It is a hardware + software ecosystem.

---

## Components

- Android Hub
- Family App
- Backend
- Smart Pill Box
- Future Smart Devices

---

## Android Hub

The Hub is NOT a consumer Android application.

It is a dedicated Android device shipped together with the product.

Users are NOT expected to install it on arbitrary Android tablets.

The Hub behaves more like an ATM or POS terminal than a traditional Android tablet.

---

## Product Philosophy

The elder should never interact with Android itself.

The Hub boots directly into Yara.

The launcher is hidden.

Settings are hidden.

The device should always stay online.

Offline functionality is mandatory.

Reliability is more important than visual complexity.

---

## UI Philosophy

Simple.

Large buttons.

No animations unless they improve usability.

Minimal navigation.

Designed for elderly users.

---

## Design Philosophy

The Hub is an appliance.

Not a tablet.

Not a smartphone.

Not an Android application.

Users should never notice Android.

Users should feel they are using a dedicated care device.

## Hardware

ESP32-C3

BLE

Android Tablet

Future Sensors

---

## Family App

Regular mobile application.

Managed by family members.

Modern UI.

Easy to update.

---

## Product Principles

- Offline First
- Security by Design
- MVP First
- Simplicity over Complexity

---

## Constraints

- Team size: 1-2 developers
- MVP deadline: 2 months
- Simplicity has priority over scalability
- Hardware is controlled by the project
- Only officially supported Android tablets are targeted

## Success Metrics

The MVP is successful only if:

- Elder receives medication reminders.
- Pill Box reports door events.
- Family can monitor device status remotely.
- Hub survives reboot and power loss.
- Core features continue working without Internet.

## Non Functional Requirements

- Boot time < 30 seconds
- BLE reconnect automatically
- Offline operation is mandatory
- Recovery after power loss
- No user interaction required after reboot
- Support 24/7 operation
- Simple UI optimized for elderly users



## AI Development Philosophy

AI assistants are team members.

Every implementation should:

- Keep architecture simple.
- Avoid unnecessary abstractions.
- Minimize dependencies.
- Prefer proven solutions over clever solutions.
- Optimize for maintainability by a small team.

## Founder Constraints

Yara is being built by a very small team with limited resources.

Every technical decision must optimize for:

- Product quality
- Development speed
- Low operational cost
- Low maintenance cost
- Long device lifetime

Avoid solutions that increase complexity without creating clear user value.

## Future Vision

Future versions may include:

- AI Assistant
- Local LLM
- Speech Recognition
- Video Calls
- Medical Devices
- Smart Home Integration

Current architecture should not block these future capabilities.