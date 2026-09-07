# ADR-014 — Voice Message Slice (پیام صوتی)

Status: Accepted (Superseded by Two-Way Messaging Subsystem)  
Scope: Communication domain, Backend, Hub, Family App  
Related: ADR-010 (communication boundaries), ADR-011 (session lifecycle), ADR-013 (provider abstraction)

## Context

The elder-first UX (`docs/UX_ARCHITECTURE.md`) lists voice messages as an MVP
feature: a large play button to listen, hold-to-record to send, no keyboard,
no text. `docs/BACKLOG.md` and `docs/ROADMAP.md` list Voice Messages under the
future backlog. The two documents disagree about timing.

The frozen Communication Domain Contract defines `MESSAGE` only as a
`Communication Channel` of a real-time `CommunicationSession`
(`INITIATED → CONNECTING → CONNECTED → ENDED`). It defines no recorded audio
entity, no media storage, and no delivery or listened state.

Originally neither client could record or play audio:

- The Family App had no recording library and no voice-message UI.
- The Hub declared `RECORD_AUDIO` for live calls only; `MediaRecorder`,
  `MediaPlayer`, and ExoPlayer were unused. `VoiceMessageCard` existed in the UI
  library but was never wired to data.
- The Backend had no message entity, no upload endpoint, and no audio storage.

A caregiver reported the Family call screen offering «تماس صوتی» while
expecting «پیام صوتی». Voice *calls* are implemented (`channel = VOICE`, same
provider room as video with the camera off); voice *messages* are not.

## Decision (Historical & Architectural)

1. **Voice messages are asynchronous and are not a `CommunicationSession`.**
   A session is a live conversation with participants and a connect timestamp.
   A voice message is a stored recording with a sender, a recipient, and a
   listened state. Modelling it as a session with `channel = MESSAGE` would
   overload a frozen aggregate with a lifecycle it does not have.
   **Fundamental Rule:** `Voice Message != Voice Call`.

2. **Superseded by Unified Two-Way Messaging Subsystem:**
   The architectural decision that voice messages are asynchronous stored media
   rather than real-time sessions was accepted. Rather than implementing voice
   recordings as a disconnected one-off feature, the architecture was generalized
   into a complete **Two-Way Messaging Subsystem** residing inside the Communication domain.

3. **Implemented Architecture:**
   - **Backend Domain (`domains.communication`):**
     - `Message` aggregate root: supports `message_type` (`TEXT`, `VOICE`, `IMAGE`, `VIDEO`),
       `direction` (`HUB_TO_FAMILY`, `FAMILY_TO_HUB`), and base status (`PENDING`, `SENT`, `FAILED`).
     - `MessageRecipient` entity: isolates `delivered_at` and `read_at` per active caregiver (`user_id`).
       Guarantees that one caregiver reading/receiving a message never marks it read/delivered for other caregivers.
     - `MessageAttachment`: file storage path, MIME validation, duration in seconds, dimensions.
     - Endpoints:
       - `GET / POST /api/v1/communication/elders/{elder_id}/messages/` (projects per-recipient status)
       - `POST /api/v1/communication/messages/{message_id}/delivered/` (caregiver-isolated delivery acknowledgment)
       - `POST /api/v1/communication/messages/{message_id}/read/` (caregiver-isolated read acknowledgment)
       - `POST /api/v1/communication/media/upload/`
       - `GET /api/v1/communication/media/{attachment_id}/download/`
   - **Android Hub:**
     - Room `MessageEntity` and `MessageDao` in database module.
     - `MessagingRepositoryImpl` in `:data` module handling message caching, audio playback,
       outbox dispatch, and synchronization.
   - **Family App:**
     - `app/(app)/messages.tsx` conversation screen.
     - `useMessages` hook handling optimistic updates and automatic delivery receipts.
     - Audio recording via `expo-av` and media picking via `expo-image-picker`.

4. **Voice Call vs. Voice Message Boundary Preserved:**
   - Real-time voice calls continue to use `CommunicationSession` (`channel = VOICE`) over LiveKit WebRTC.
   - Asynchronous voice messages use `Message` (`message_type = VOICE`) with media storage.
   - The two systems remain completely decoupled in state machines, lifecycles, and data models.

## Consequences

- The distinction between real-time calls and asynchronous messages is rigorously maintained across all clients and backend.
- Asynchronous voice messages work alongside text, image, and video messaging under a single unified messaging contract.
- Multi-recipient semantics guarantee that every active caregiver tracks their own message delivery and read status independently without state leakage.
- Clients are no longer blocked or stubbed; two-way messaging is active in the MVP.
