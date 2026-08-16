import { CommunicationRuntime, DEFAULT_JOIN_TIMEOUT_MS } from "../communication/CommunicationRuntime";
import {
  InMemoryKeyValueStore,
  PersistentCommunicationRepository,
} from "../communication/CommunicationRepository";
import { ActiveCallExistsError, err, ok } from "../communication/result";
import type { AppResult } from "../communication/result";
import type { CallSession } from "../communication/model";
import type { CommunicationGateway } from "../communication/CommunicationGateway";
import type {
  ConnectivitySource,
  IncomingSessionSource,
  Scheduler,
} from "../communication/ports";
import type { IncomingSessionNotice } from "../communication/model";

const ELDER_ID = "elder-1";
const CONTACT_ID = "contact-1";
const NOW = 1_700_000_000_000;

class FakeScheduler implements Scheduler {
  nowMs = NOW;
  private timers: { at: number; callback: () => void; cancelled: boolean }[] = [];

  now(): number {
    return this.nowMs;
  }

  delay(ms: number, callback: () => void): () => void {
    const timer = { at: this.nowMs + ms, callback, cancelled: false };
    this.timers.push(timer);
    return () => {
      timer.cancelled = true;
    };
  }

  async advance(ms: number): Promise<void> {
    this.nowMs += ms;
    const due = this.timers.filter((timer) => !timer.cancelled && timer.at <= this.nowMs);
    this.timers = this.timers.filter((timer) => !timer.cancelled && timer.at > this.nowMs);
    for (const timer of due) {
      timer.callback();
    }
    await flush();
  }
}

class FakeGateway implements CommunicationGateway {
  startCount = 0;
  refreshCount = 0;
  endedSessionIds: string[] = [];
  startError: Error | null = null;
  startSession: CallSession = makeSession({
    sessionId: "session-1",
    joinToken: "opaque-join-token",
    direction: "Outgoing",
  });
  refreshSession: CallSession = makeSession({
    sessionId: "existing-session",
    joinToken: "refreshed-token",
    direction: "Incoming",
  });

  async startCall(
    elderId: string,
    channel: string,
    recipientContactId: string,
  ): Promise<AppResult<CallSession>> {
    this.startCount += 1;
    if (this.startError) {
      return err(this.startError);
    }
    return ok({
      ...this.startSession,
      elderId,
      channel,
      recipientContactId,
    });
  }

  async endCall(sessionId: string): Promise<AppResult<void>> {
    this.endedSessionIds.push(sessionId);
    return ok(undefined);
  }

  async refreshJoinToken(elderId: string): Promise<AppResult<CallSession>> {
    this.refreshCount += 1;
    return ok({
      ...this.refreshSession,
      elderId,
    });
  }
}

class FakeIncoming implements IncomingSessionSource {
  private listener: ((sessions: IncomingSessionNotice[]) => void) | null = null;

  observe(listener: (sessions: IncomingSessionNotice[]) => void): () => void {
    this.listener = listener;
    return () => {
      this.listener = null;
    };
  }

  emit(sessions: IncomingSessionNotice[]): void {
    this.listener?.(sessions);
  }
}

class FakeConnectivity implements ConnectivitySource {
  private listener: ((online: boolean) => void) | null = null;

  observeOnline(listener: (online: boolean) => void): () => void {
    this.listener = listener;
    listener(true);
    return () => {
      this.listener = null;
    };
  }

  setOnline(online: boolean): void {
    this.listener?.(online);
  }
}

function makeSession(partial: Partial<CallSession> = {}): CallSession {
  return {
    sessionId: "session-1",
    elderId: ELDER_ID,
    channel: "VOICE",
    recipientContactId: CONTACT_ID,
    runtimeState: "Connecting",
    joinToken: "opaque-join-token",
    expiresAtEpochMillis: NOW + 3_600_000,
    updatedAtEpochMillis: NOW,
    direction: "Outgoing",
    ...partial,
  };
}

async function flush(): Promise<void> {
  for (let i = 0; i < 8; i += 1) {
    await Promise.resolve();
  }
  await new Promise<void>((resolve) => {
    setImmediate(resolve);
  });
}

function createHarness(options: {
  gateway?: FakeGateway;
  incoming?: FakeIncoming;
  connectivity?: FakeConnectivity;
  store?: InMemoryKeyValueStore;
  joinTimeoutMs?: number;
} = {}) {
  const gateway = options.gateway ?? new FakeGateway();
  const store = options.store ?? new InMemoryKeyValueStore();
  const repository = new PersistentCommunicationRepository(store);
  const scheduler = new FakeScheduler();
  const states: (CallSession["runtimeState"] | null)[] = [];
  const runtime = new CommunicationRuntime(gateway, repository, scheduler, {
    joinTimeoutMs: options.joinTimeoutMs,
    incoming: options.incoming,
    connectivity: options.connectivity,
    onSession: (session) => {
      states.push(session?.runtimeState ?? null);
    },
  });
  return { gateway, store, repository, scheduler, runtime, states };
}

describe("CommunicationRuntime", () => {
  it("starts an outgoing call, consumes joinToken, and reaches Connected", async () => {
    const { runtime, repository, gateway } = createHarness();

    const result = await runtime.startCall(ELDER_ID, "VOICE", CONTACT_ID);

    expect(result.ok).toBe(true);
    if (!result.ok) {
      return;
    }
    expect(result.data.sessionId).toBe("session-1");
    expect(result.data.direction).toBe("Outgoing");
    expect(result.data.runtimeState).toBe("Connected");
    expect(result.data.joinToken).toBe("opaque-join-token");
    expect(gateway.startCount).toBe(1);
    await expect(repository.getCurrent()).resolves.toMatchObject({
      runtimeState: "Connected",
      joinToken: "opaque-join-token",
    });
  });

  it("reuses a local active session instead of starting again", async () => {
    const { runtime, gateway } = createHarness();
    await runtime.startCall(ELDER_ID, "VOICE", CONTACT_ID);
    const second = await runtime.startCall(ELDER_ID, "VOICE", CONTACT_ID);

    expect(second.ok).toBe(true);
    expect(gateway.startCount).toBe(1);
    if (second.ok) {
      expect(second.data.sessionId).toBe("session-1");
    }
  });

  it("on HTTP 409 refreshes login-url and joins the existing session", async () => {
    const gateway = new FakeGateway();
    gateway.startError = new ActiveCallExistsError();
    const { runtime, repository } = createHarness({ gateway });

    const result = await runtime.startCall(ELDER_ID, "VOICE", CONTACT_ID);

    expect(result.ok).toBe(true);
    if (!result.ok) {
      return;
    }
    expect(result.data.sessionId).toBe("existing-session");
    expect(result.data.joinToken).toBe("refreshed-token");
    expect(result.data.direction).toBe("Incoming");
    expect(result.data.runtimeState).toBe("Connected");
    expect(gateway.startCount).toBe(1);
    expect(gateway.refreshCount).toBe(1);
    await expect(repository.getCurrent()).resolves.toMatchObject({
      sessionId: "existing-session",
      runtimeState: "Connected",
    });
  });

  it("joinIncomingCall uses login-url only", async () => {
    const { runtime, gateway } = createHarness();

    const result = await runtime.joinIncomingCall(ELDER_ID, "VIDEO");

    expect(result.ok).toBe(true);
    if (!result.ok) {
      return;
    }
    expect(result.data.direction).toBe("Incoming");
    expect(result.data.channel).toBe("VIDEO");
    expect(gateway.startCount).toBe(0);
    expect(gateway.refreshCount).toBe(1);
  });

  it("accepts an incoming replica session", async () => {
    const incoming = new FakeIncoming();
    const { runtime, gateway, repository } = createHarness({ incoming });
    runtime.startCollectors();
    incoming.emit([
      { elderId: ELDER_ID, channel: "VOICE", status: "CONNECTING" },
    ]);
    await flush();

    expect(gateway.refreshCount).toBe(1);
    await expect(repository.getCurrent()).resolves.toMatchObject({
      direction: "Incoming",
      runtimeState: "Connected",
    });
  });

  it("marks ConnectionLost, then reconnects through Reconnecting", async () => {
    const { runtime, repository, states } = createHarness();
    await runtime.startCall(ELDER_ID, "VOICE", CONTACT_ID);

    const lost = await runtime.markConnectionLost();
    expect(lost.ok).toBe(true);
    await expect(repository.getCurrent()).resolves.toMatchObject({
      runtimeState: "ConnectionLost",
    });

    const reconnected = await runtime.retry();
    expect(reconnected.ok).toBe(true);
    await expect(repository.getCurrent()).resolves.toMatchObject({
      runtimeState: "Connected",
      sessionId: "session-1",
    });
    expect(states).toEqual([
      "Connecting",
      "Connected",
      "ConnectionLost",
      "Reconnecting",
      "Connected",
    ]);
  });

  it("network drop marks ConnectionLost and restore reconnects", async () => {
    const connectivity = new FakeConnectivity();
    const { runtime, repository } = createHarness({ connectivity });
    await runtime.startCall(ELDER_ID, "VOICE", CONTACT_ID);

    connectivity.setOnline(false);
    await flush();
    await expect(repository.getCurrent()).resolves.toMatchObject({
      runtimeState: "ConnectionLost",
    });

    connectivity.setOnline(true);
    await flush();
    await expect(repository.getCurrent()).resolves.toMatchObject({
      runtimeState: "Connected",
    });
  });

  it("reconnects from a cached session without calling startCall", async () => {
    const { runtime, gateway, repository } = createHarness();
    await runtime.startCall(ELDER_ID, "VOICE", CONTACT_ID);
    await runtime.markConnectionLost();
    const before = gateway.startCount;

    await runtime.reconnect();

    expect(gateway.startCount).toBe(before);
    await expect(repository.getCurrent()).resolves.toMatchObject({
      runtimeState: "Connected",
      joinToken: "opaque-join-token",
    });
  });

  it("refreshes joinToken when reconnecting an expired cached session", async () => {
    const { runtime, gateway, repository, scheduler } = createHarness();
    await runtime.startCall(ELDER_ID, "VOICE", CONTACT_ID);
    await runtime.markConnectionLost();
    const current = await repository.getCurrent();
    if (!current) {
      throw new Error("expected session");
    }
    await repository.saveCurrent({
      ...current,
      expiresAtEpochMillis: scheduler.now(),
    });

    const result = await runtime.reconnect();

    expect(result.ok).toBe(true);
    expect(gateway.refreshCount).toBe(1);
    await expect(repository.getCurrent()).resolves.toMatchObject({
      joinToken: "refreshed-token",
      runtimeState: "Connected",
    });
  });

  it("endCall ends the Backend session and idle-cleans local state", async () => {
    const { runtime, gateway, repository, states } = createHarness();
    await runtime.startCall(ELDER_ID, "VOICE", CONTACT_ID);

    const ended = await runtime.endCall();

    expect(ended.ok).toBe(true);
    expect(gateway.endedSessionIds).toEqual(["session-1"]);
    await expect(repository.getCurrent()).resolves.toBeNull();
    expect(states.at(-1)).toBeNull();
  });

  it("recovers an unexpired session after process death", async () => {
    const store = new InMemoryKeyValueStore();
    const first = createHarness({ store });
    await first.runtime.startCall(ELDER_ID, "VOICE", CONTACT_ID);

    const second = createHarness({ store, gateway: first.gateway });
    const recovered = await second.runtime.recover();

    expect(recovered.ok).toBe(true);
    await expect(second.repository.getCurrent()).resolves.toMatchObject({
      sessionId: "session-1",
      runtimeState: "Connected",
      joinToken: "opaque-join-token",
    });
  });

  it("recovers ConnectionLost by reconnecting from cache", async () => {
    const store = new InMemoryKeyValueStore();
    const first = createHarness({ store });
    await first.runtime.startCall(ELDER_ID, "VOICE", CONTACT_ID);
    await first.runtime.markConnectionLost();

    const second = createHarness({ store, gateway: first.gateway });
    await second.runtime.recover();

    await expect(second.repository.getCurrent()).resolves.toMatchObject({
      runtimeState: "Connected",
    });
  });

  it("drops an expired stored session and ends it on Backend", async () => {
    const store = new InMemoryKeyValueStore();
    const first = createHarness({ store });
    await first.runtime.startCall(ELDER_ID, "VOICE", CONTACT_ID);
    const current = await first.repository.getCurrent();
    if (!current) {
      throw new Error("expected session");
    }
    await first.repository.saveCurrent({
      ...current,
      expiresAtEpochMillis: NOW,
    });

    const second = createHarness({ store, gateway: first.gateway });
    const recovered = await second.runtime.recover();

    expect(recovered.ok).toBe(true);
    if (recovered.ok) {
      expect(recovered.data).toBeNull();
    }
    expect(first.gateway.endedSessionIds).toContain("session-1");
    await expect(second.repository.getCurrent()).resolves.toBeNull();
  });

  it("times out a Connecting session, ends Backend, and idle-cleans", async () => {
    const gateway = new FakeGateway();
    gateway.startSession = makeSession({ joinToken: "" });
    const { runtime, repository, scheduler } = createHarness({
      gateway,
      joinTimeoutMs: DEFAULT_JOIN_TIMEOUT_MS,
    });

    const started = await runtime.startCall(ELDER_ID, "VOICE", CONTACT_ID);
    expect(started.ok).toBe(false);
    await expect(repository.getCurrent()).resolves.toMatchObject({
      runtimeState: "Connecting",
    });

    await scheduler.advance(DEFAULT_JOIN_TIMEOUT_MS);

    expect(gateway.endedSessionIds).toEqual(["session-1"]);
    await expect(repository.getCurrent()).resolves.toBeNull();
  });

  it("does not fire join timeout after Connected", async () => {
    const { runtime, gateway, repository, scheduler } = createHarness();
    await runtime.startCall(ELDER_ID, "VOICE", CONTACT_ID);

    await scheduler.advance(DEFAULT_JOIN_TIMEOUT_MS);

    expect(gateway.endedSessionIds).toEqual([]);
    await expect(repository.getCurrent()).resolves.toMatchObject({
      runtimeState: "Connected",
    });
  });

  it("can start again after idle cleanup", async () => {
    const { runtime, gateway } = createHarness();
    await runtime.startCall(ELDER_ID, "VOICE", CONTACT_ID);
    await runtime.endCall();

    const second = await runtime.startCall(ELDER_ID, "VOICE", CONTACT_ID);

    expect(second.ok).toBe(true);
    expect(gateway.startCount).toBe(2);
  });
});
