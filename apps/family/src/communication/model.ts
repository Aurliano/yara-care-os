export type CallDirection = "Outgoing" | "Incoming";

export type CallRuntimeState =
  | "Idle"
  | "Connecting"
  | "Connected"
  | "ConnectionLost"
  | "Reconnecting"
  | "Finished";

export const ACTIVE_CALL_STATES: readonly CallRuntimeState[] = [
  "Connecting",
  "Connected",
  "ConnectionLost",
  "Reconnecting",
];

export function isActiveCallState(state: CallRuntimeState): boolean {
  return ACTIVE_CALL_STATES.includes(state);
}

export type CallSession = {
  sessionId: string;
  elderId: string;
  channel: string;
  recipientContactId: string;
  runtimeState: CallRuntimeState;
  joinToken: string;
  expiresAtEpochMillis: number;
  updatedAtEpochMillis: number;
  direction: CallDirection;
};

export type IncomingSessionNotice = {
  elderId: string;
  channel: string;
  status: string;
};

export const INCOMING_SESSION_STATUSES = ["INITIATED", "CONNECTING", "CONNECTED"] as const;
