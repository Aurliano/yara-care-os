import type { CallSession } from "./model";

export interface KeyValueStore {
  getItem(key: string): Promise<string | null>;
  setItem(key: string, value: string): Promise<void>;
  removeItem(key: string): Promise<void>;
}

export interface CommunicationRepository {
  saveCurrent(session: CallSession): Promise<void>;
  getCurrent(): Promise<CallSession | null>;
  clear(): Promise<void>;
  observeCurrent(listener: (session: CallSession | null) => void): () => void;
}

const STORAGE_KEY = "yara.family.local_call_session";

export class PersistentCommunicationRepository implements CommunicationRepository {
  private listeners = new Set<(session: CallSession | null) => void>();
  private memory: CallSession | null = null;

  constructor(private readonly store: KeyValueStore) {}

  async saveCurrent(session: CallSession): Promise<void> {
    this.memory = session;
    await this.store.setItem(STORAGE_KEY, JSON.stringify(session));
    this.emit(session);
  }

  async getCurrent(): Promise<CallSession | null> {
    if (this.memory) {
      return this.memory;
    }
    const raw = await this.store.getItem(STORAGE_KEY);
    if (!raw) {
      return null;
    }
    try {
      this.memory = JSON.parse(raw) as CallSession;
      return this.memory;
    } catch {
      await this.store.removeItem(STORAGE_KEY);
      this.memory = null;
      return null;
    }
  }

  async clear(): Promise<void> {
    this.memory = null;
    await this.store.removeItem(STORAGE_KEY);
    this.emit(null);
  }

  observeCurrent(listener: (session: CallSession | null) => void): () => void {
    this.listeners.add(listener);
    listener(this.memory);
    return () => {
      this.listeners.delete(listener);
    };
  }

  private emit(session: CallSession | null): void {
    for (const listener of this.listeners) {
      listener(session);
    }
  }
}

export class InMemoryKeyValueStore implements KeyValueStore {
  private values = new Map<string, string>();

  async getItem(key: string): Promise<string | null> {
    return this.values.get(key) ?? null;
  }

  async setItem(key: string, value: string): Promise<void> {
    this.values.set(key, value);
  }

  async removeItem(key: string): Promise<void> {
    this.values.delete(key);
  }
}
