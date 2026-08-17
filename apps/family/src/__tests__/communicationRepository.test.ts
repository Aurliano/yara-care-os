import {
  InMemoryKeyValueStore,
  PersistentCommunicationRepository,
} from "../communication/CommunicationRepository";
import type { CallSession } from "../communication/model";

const SESSION: CallSession = {
  sessionId: "session-1",
  elderId: "elder-1",
  channel: "VOICE",
  recipientContactId: "contact-1",
  runtimeState: "Connected",
  joinToken: "opaque-join-token",
  expiresAtEpochMillis: 1_800_000_000_000,
  updatedAtEpochMillis: 1_700_000_000_000,
  direction: "Outgoing",
};

describe("PersistentCommunicationRepository", () => {
  it("persists and returns the current CallSession", async () => {
    const repo = new PersistentCommunicationRepository(new InMemoryKeyValueStore());
    await repo.saveCurrent(SESSION);
    await expect(repo.getCurrent()).resolves.toEqual(SESSION);
  });

  it("recovers a session from storage after a new repository is created", async () => {
    const store = new InMemoryKeyValueStore();
    const first = new PersistentCommunicationRepository(store);
    await first.saveCurrent(SESSION);

    const recovered = new PersistentCommunicationRepository(store);
    await expect(recovered.getCurrent()).resolves.toEqual(SESSION);
  });

  it("clears the current session", async () => {
    const repo = new PersistentCommunicationRepository(new InMemoryKeyValueStore());
    const seen: (CallSession | null)[] = [];
    repo.observeCurrent((session) => {
      seen.push(session);
    });
    await repo.saveCurrent(SESSION);
    await repo.clear();
    await expect(repo.getCurrent()).resolves.toBeNull();
    expect(seen).toEqual([null, SESSION, null]);
  });

  it("ignores corrupt stored JSON", async () => {
    const store = new InMemoryKeyValueStore();
    await store.setItem("yara.family.local_call_session", "{not-json");
    const repo = new PersistentCommunicationRepository(store);
    await expect(repo.getCurrent()).resolves.toBeNull();
  });
});
