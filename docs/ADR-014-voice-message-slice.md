# ADR-014 — Voice Message Slice (پیام صوتی)

Status: Proposed (not implemented)  
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

Today neither client can record or play audio:

- The Family App has no recording library and no voice-message UI.
- The Hub declares `RECORD_AUDIO` for live calls only; `MediaRecorder`,
  `MediaPlayer`, and ExoPlayer are unused. `VoiceMessageCard` exists in the UI
  library but was never wired to data.
- The Backend has no message entity, no upload endpoint, and no audio storage.

A caregiver reported the Family call screen offering «تماس صوتی» while
expecting «پیام صوتی». Voice *calls* are implemented (`channel = VOICE`, same
provider room as video with the camera off); voice *messages* are not.

## Decision

1. **Voice messages are asynchronous and are not a `CommunicationSession`.**
   A session is a live conversation with participants and a connect timestamp.
   A voice message is a stored recording with a sender, a recipient, and a
   listened state. Modelling it as a session with `channel = MESSAGE` would
   overload a frozen aggregate with a lifecycle it does not have.

2. **The slice is not implemented until this ADR is accepted.** Until then both
   clients show the entry as explicitly unavailable rather than hiding it:
   - Family: `voiceMessageRepository.ts` returns `VOICE_MESSAGE_API_MISSING`
     and the call screen shows a disabled «پیام صوتی» action with honest copy.
   - Hub: `VoiceMessageUnavailableCard` under «پیام‌های خانواده».

   Reason: the same rule already used for the caregiver alert inbox — never
   invent an API, never pretend a capability exists.

3. **`channel = MESSAGE` stays unused in clients** while this ADR is Proposed.
   The Family runtime already excludes it from incoming-call handling.

4. **When accepted, the slice needs all of the following** (an extension of the
   Communication contract, to be reviewed before implementation):
   - A voice message entity: sender subject, elder, recipient, media reference,
     duration, created timestamp, delivered and listened state.
   - Audio storage with an explicit decision between local filesystem and
     object storage, plus retention. `Prescription.media_reference` shows the
     existing media-reference convention.
   - Upload and download endpoints with size and duration limits
     (proposed: 60 seconds, 1 MB, one codec).
   - Offline behaviour: the Hub must play an already-downloaded message with no
     network. Synchronization must therefore carry the audio payload, not only
     metadata. This is the largest piece of work in the slice.
   - Recording UI: Family `expo-av`; Hub `MediaRecorder` with hold-to-record and
     a large play button, per the elder UX rules.

5. **Voice call stays available.** The Family call screen leads with video, and
   the Hub can still start or answer a `VOICE` session (contact
   `preferred_channel`). Removing the working voice path is not part of this
   decision.

## Consequences

- The caregiver sees «پیام صوتی» where they expect it, and is told plainly that
  it is not active yet, instead of finding a button that silently fails.
- The frozen Communication contract is untouched until the extension above is
  reviewed.
- Offline audio sync is identified as the main cost of the slice, so it is not
  mistaken for a UI-only task.
