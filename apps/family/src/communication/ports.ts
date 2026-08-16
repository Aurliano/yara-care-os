import type { IncomingSessionNotice } from "./model";

export interface IncomingSessionSource {
  observe(listener: (sessions: IncomingSessionNotice[]) => void): () => void;
}

export interface ConnectivitySource {
  observeOnline(listener: (online: boolean) => void): () => void;
}

export interface Scheduler {
  now(): number;
  delay(ms: number, callback: () => void): () => void;
}

export function createRealtimeScheduler(): Scheduler {
  return {
    now: () => Date.now(),
    delay: (ms, callback) => {
      const handle = setTimeout(callback, ms);
      return () => clearTimeout(handle);
    },
  };
}
