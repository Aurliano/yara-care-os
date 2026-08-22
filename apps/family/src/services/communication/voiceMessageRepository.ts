/**
 * Voice messages (پیام صوتی) are an asynchronous recording, not a call.
 * The Communication Domain Contract only defines real-time sessions today, so
 * there is no Backend endpoint to record, upload, or play them. See ADR-014.
 *
 * All voice-message UI must go through this repository so we never invent an API.
 */

export type VoiceMessageAvailability =
  | { available: false; reason: "VOICE_MESSAGE_API_MISSING" }
  | { available: true };

export function voiceMessageAvailability(): VoiceMessageAvailability {
  return { available: false, reason: "VOICE_MESSAGE_API_MISSING" };
}
