import { ActiveCallExistsError, err, ok } from "./result";
import type { AppResult } from "./result";
import {
  INCOMING_SESSION_STATUSES,
  isActiveCallState,
} from "./model";
import type { CallRuntimeState, CallSession } from "./model";
import type { CommunicationGateway } from "./CommunicationGateway";
import type { CommunicationRepository } from "./CommunicationRepository";
import { CommunicationStateMachine } from "./CommunicationStateMachine";
import type { ConnectivitySource, IncomingSessionSource, Scheduler } from "./ports";

export const DEFAULT_JOIN_TIMEOUT_MS = 120_000;

export type CommunicationRuntimeOptions = {
  joinTimeoutMs?: number;
  incoming?: IncomingSessionSource;
  connectivity?: ConnectivitySource;
  onSession?: (session: CallSession | null) => void;
};

export class CommunicationRuntime {
  private readonly machine = new CommunicationStateMachine();
  private readonly joinTimeoutMs: number;
  private cancelTimeout: (() => void) | null = null;
  private collectorsStarted = false;
  private queue: Promise<void> = Promise.resolve();

  constructor(
    private readonly gateway: CommunicationGateway,
    private readonly repository: CommunicationRepository,
    private readonly scheduler: Scheduler,
    private readonly options: CommunicationRuntimeOptions = {},
  ) {
    this.joinTimeoutMs = options.joinTimeoutMs ?? DEFAULT_JOIN_TIMEOUT_MS;
  }

  observeCurrent(listener: (session: CallSession | null) => void): () => void {
    return this.repository.observeCurrent(listener);
  }

  startCollectors(): void {
    if (this.collectorsStarted) {
      return;
    }
    this.collectorsStarted = true;
    this.options.incoming?.observe((sessions) => {
      void this.maybeAcceptIncoming(sessions);
    });
    let seenFirst = false;
    this.options.connectivity?.observeOnline((online) => {
      if (!seenFirst) {
        seenFirst = true;
        return;
      }
      if (online) {
        void this.reconnect();
      } else {
        void this.markConnectionLost();
      }
    });
  }

  startCall(
    elderId: string,
    channel: string,
    recipientContactId: string,
  ): Promise<AppResult<CallSession>> {
    this.startCollectors();
    return this.serialized(async () => {
      const current = await this.repository.getCurrent();
      if (
        current &&
        isActiveCallState(current.runtimeState) &&
        current.expiresAtEpochMillis > this.scheduler.now()
      ) {
        return ok(current);
      }
      const started = await this.gateway.startCall(elderId, channel, recipientContactId);
      if (!started.ok) {
        if (started.error instanceof ActiveCallExistsError) {
          return this.prepareIncoming(elderId, channel, recipientContactId);
        }
        return started;
      }
      const connecting = await this.persistTransition(
        {
          ...started.data,
          direction: "Outgoing",
        },
        "Connecting",
      );
      if (!connecting.ok) {
        return connecting;
      }
      return this.consumeJoinToken(connecting.data);
    });
  }

  joinIncomingCall(
    elderId: string,
    channel = "VOICE",
    recipientContactId = "",
  ): Promise<AppResult<CallSession>> {
    this.startCollectors();
    return this.serialized(async () => {
      const current = await this.repository.getCurrent();
      if (
        current &&
        isActiveCallState(current.runtimeState) &&
        current.expiresAtEpochMillis > this.scheduler.now()
      ) {
        return ok(current);
      }
      return this.prepareIncoming(elderId, channel, recipientContactId);
    });
  }

  retry(): Promise<AppResult<CallSession | null>> {
    return this.reconnect();
  }

  reconnect(): Promise<AppResult<CallSession | null>> {
    this.startCollectors();
    return this.serialized(() => this.reconnectLocked());
  }

  endCall(): Promise<AppResult<void>> {
    return this.serialized(async () => {
      const current = await this.repository.getCurrent();
      if (!current) {
        return ok(undefined);
      }
      const ended = await this.gateway.endCall(current.sessionId);
      if (!ended.ok) {
        return ended;
      }
      await this.finishAndCleanup(current);
      return ok(undefined);
    });
  }

  markConnectionLost(): Promise<AppResult<CallSession | null>> {
    return this.serialized(async () => {
      const current = await this.repository.getCurrent();
      if (!current) {
        return ok(null);
      }
      if (
        current.runtimeState !== "Connected" &&
        current.runtimeState !== "Connecting" &&
        current.runtimeState !== "Reconnecting"
      ) {
        return ok(current);
      }
      return this.persistTransition(current, "ConnectionLost");
    });
  }

  recover(): Promise<AppResult<CallSession | null>> {
    this.startCollectors();
    return this.serialized(async () => {
      const stored = await this.repository.getCurrent();
      if (!stored) {
        this.machine.resetToIdle();
        return ok(null);
      }
      if (!isActiveCallState(stored.runtimeState)) {
        await this.cleanupIdle();
        return ok(null);
      }
      if (stored.expiresAtEpochMillis <= this.scheduler.now()) {
        await this.gateway.endCall(stored.sessionId);
        await this.cleanupIdle();
        return ok(null);
      }
      this.machine.restore(stored.runtimeState);
      this.options.onSession?.(stored);
      if (stored.runtimeState === "ConnectionLost") {
        return this.reconnectLocked();
      }
      return this.consumeJoinToken(stored);
    });
  }

  async cleanupIdle(): Promise<void> {
    this.clearJoinTimeout();
    await this.repository.clear();
    this.machine.resetToIdle();
    this.options.onSession?.(null);
  }

  private async prepareIncoming(
    elderId: string,
    channel: string,
    recipientContactId: string,
  ): Promise<AppResult<CallSession>> {
    const refreshed = await this.gateway.refreshJoinToken(elderId);
    if (!refreshed.ok) {
      return refreshed;
    }
    if (!refreshed.data.sessionId) {
      return err(new ActiveCallExistsError());
    }
    const connecting = await this.persistTransition(
      {
        ...refreshed.data,
        elderId,
        channel: channel || refreshed.data.channel || "VOICE",
        recipientContactId: recipientContactId || refreshed.data.recipientContactId,
        direction: "Incoming",
      },
      "Connecting",
    );
    if (!connecting.ok) {
      return connecting;
    }
    return this.consumeJoinToken(connecting.data);
  }

  private async consumeJoinToken(session: CallSession): Promise<AppResult<CallSession>> {
    if (!session.joinToken) {
      return err(new Error("Backend joinToken was empty."));
    }
    if (session.runtimeState === "Connected") {
      return ok(session);
    }
    return this.persistTransition(session, "Connected");
  }

  private async reconnectLocked(): Promise<AppResult<CallSession | null>> {
    const current = await this.repository.getCurrent();
    if (!current || !isActiveCallState(current.runtimeState)) {
      return ok(null);
    }
    let refreshed = current;
    if (current.expiresAtEpochMillis <= this.scheduler.now()) {
      const token = await this.gateway.refreshJoinToken(current.elderId);
      if (!token.ok) {
        return token;
      }
      refreshed = {
        ...current,
        sessionId: token.data.sessionId || current.sessionId,
        joinToken: token.data.joinToken,
        expiresAtEpochMillis: token.data.expiresAtEpochMillis,
      };
    }
    if (current.runtimeState === "Connecting") {
      return this.consumeJoinToken(refreshed);
    }
    if (current.runtimeState === "Connected") {
      const next: CallSession = {
        ...refreshed,
        updatedAtEpochMillis: this.scheduler.now(),
      };
      await this.repository.saveCurrent(next);
      this.options.onSession?.(next);
      return ok(next);
    }
    const reconnecting = await this.persistTransition(refreshed, "Reconnecting");
    if (!reconnecting.ok) {
      return reconnecting;
    }
    return this.consumeJoinToken(reconnecting.data);
  }

  private async persistTransition(
    session: CallSession,
    to: CallRuntimeState,
  ): Promise<AppResult<CallSession>> {
    if (this.machine.current() !== to) {
      if (!this.machine.canTransition(to)) {
        this.machine.restore(session.runtimeState);
      }
      if (this.machine.current() !== to) {
        try {
          this.machine.transition(to);
        } catch (caught) {
          const error = caught instanceof Error ? caught : new Error(String(caught));
          return err(error);
        }
      }
    }
    const next: CallSession = {
      ...session,
      runtimeState: to,
      updatedAtEpochMillis: this.scheduler.now(),
    };
    await this.repository.saveCurrent(next);
    this.options.onSession?.(next);
    if (to === "Connecting") {
      this.armJoinTimeout();
    } else {
      this.clearJoinTimeout();
    }
    return ok(next);
  }

  private armJoinTimeout(): void {
    this.clearJoinTimeout();
    this.cancelTimeout = this.scheduler.delay(this.joinTimeoutMs, () => {
      void this.handleJoinTimeout();
    });
  }

  private clearJoinTimeout(): void {
    this.cancelTimeout?.();
    this.cancelTimeout = null;
  }

  private async handleJoinTimeout(): Promise<void> {
    await this.serialized(async () => {
      const current = await this.repository.getCurrent();
      if (!current || current.runtimeState !== "Connecting") {
        return;
      }
      await this.gateway.endCall(current.sessionId);
      await this.finishAndCleanup(current);
    });
  }

  private async finishAndCleanup(session: CallSession): Promise<void> {
    this.machine.restore(session.runtimeState);
    if (this.machine.current() !== "Finished") {
      this.machine.transition("Finished");
    }
    const finished: CallSession = {
      ...session,
      runtimeState: "Finished",
      updatedAtEpochMillis: this.scheduler.now(),
    };
    await this.repository.saveCurrent(finished);
    this.options.onSession?.(finished);
    await this.cleanupIdle();
  }

  private async maybeAcceptIncoming(
    sessions: { elderId: string; channel: string; status: string }[],
  ): Promise<void> {
    const ringing = sessions.find(
      (session) =>
        session.channel !== "MESSAGE" &&
        (INCOMING_SESSION_STATUSES as readonly string[]).includes(session.status),
    );
    if (!ringing) {
      return;
    }
    const current = await this.repository.getCurrent();
    if (current && isActiveCallState(current.runtimeState)) {
      return;
    }
    await this.joinIncomingCall(ringing.elderId, ringing.channel || "VOICE");
  }

  private serialized<T>(work: () => Promise<T>): Promise<T> {
    const run = this.queue.then(work, work);
    this.queue = run.then(
      () => undefined,
      () => undefined,
    );
    return run;
  }
}
