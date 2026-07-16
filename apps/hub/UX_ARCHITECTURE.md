# UX Architecture

**Product:** Yara Smart Care
**Module:** Android Hub
**Version:** MVP v1
**Status:** Draft

---

# UX Principles

Yara is **not a tablet**.

Yara is a trusted companion for elderly people.

Every interaction must be:

- Simple
- Predictable
- Fast
- Safe
- Accessible

The elderly user should never feel they are using a complicated Android device.

---

# Design Philosophy

The Hub is designed around one idea:

> Stay on Home.
> Leave Home only when necessary.
> Return Home immediately after the task is completed.

There are no deep navigation hierarchies.

There are no hidden menus.

There are no complex settings.

---

# Primary Screens

## Home

The central screen of the system.

Responsibilities:

- Current time
- Greeting
- Next medication
- Voice messages
- Notifications
- Favorite contacts
- Device status

The Home screen is always the default destination.

---

## Medication Reminder

Activated automatically.

Flow:

Home

↓

Reminder

↓

Take medication

↓

Automatic confirmation from Pill Box

OR

Manual confirmation

↓

Home

If confirmation is not received within the configured time:

Notify Family

---

## Calls

Large contact cards.

Each card contains:

- Photo
- Name

One tap starts the call.

No contact list.

No dial pad.

No recent calls.

---

## Voice Messages

Receive:

Large play button.

Send:

Hold to record.

Release to send.

No keyboard.

No text messages.

---

## Notifications

Large cards.

Only one notification is focused at a time.

System notifications and family notifications use the same UI.

Examples:

- Medication reminder
- Voice message
- Family notification

---

## Settings

Not intended for elderly users.

Access:

Long Press

↓

PIN

↓

Settings

Most settings should be configured remotely by the Family App.

---

# Navigation Rules

Default state:

Home

Navigation only occurs when a task requires it.

After completing a task:

Return to Home automatically.

---

# Emergency

Not shown as a permanent large button.

Avoid accidental activation.

Preferred interaction:

Long press

↓

Countdown

↓

Emergency call

---

# Display Behavior

Default:

Screen sleeps after inactivity.

Wake:

- Touch (MVP)

Future versions:

- Presence Detection
- Camera Detection

---

# MVP Features

- Home
- Medication Reminder
- Calls
- Voice Messages
- Notifications

Everything else belongs to future releases.

---

# UX Success Criteria

An elderly user should be able to use Yara without prior training.

If a feature requires explanation,
the UX should be redesigned.

# Interaction Principles

- One tap whenever possible.
- Never require double tap.
- No hidden gestures.
- Maximum two actions to complete a task.
- Always provide visual feedback.
- Always provide audio feedback for important actions.

# Error Recovery

The user should never reach a dead end.

Every screen must provide a clear path back to Home.

If an operation fails:

- Explain what happened.
- Recover automatically whenever possible.
- Never expose technical errors.