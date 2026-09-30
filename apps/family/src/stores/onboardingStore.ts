import { create } from "zustand";
import * as SecureStore from "expo-secure-store";

export const DISCOVERY_STATUS_KEY = "yara.discoveryStatus";

export type DiscoveryStatus = "not_started" | "completed" | "skipped";

export type OnboardingStorage = {
  getStatus: () => Promise<string | null>;
  setStatus: (status: string) => Promise<void>;
  clearStatus: () => Promise<void>;
};

export const defaultOnboardingStorage: OnboardingStorage = {
  async getStatus() {
    return SecureStore.getItemAsync(DISCOVERY_STATUS_KEY);
  },
  async setStatus(status: string) {
    await SecureStore.setItemAsync(DISCOVERY_STATUS_KEY, status);
  },
  async clearStatus() {
    await SecureStore.deleteItemAsync(DISCOVERY_STATUS_KEY);
  },
};

let activeStorage: OnboardingStorage = defaultOnboardingStorage;

export function setOnboardingStorage(storage: OnboardingStorage): void {
  activeStorage = storage;
}

export function getOnboardingStorage(): OnboardingStorage {
  return activeStorage;
}

export type OnboardingState = {
  status: DiscoveryStatus;
  hydrated: boolean;
  hydrate: () => Promise<void>;
  completeDiscovery: () => Promise<void>;
  skipDiscovery: () => Promise<void>;
  resetDiscovery: () => Promise<void>;
};

export const useOnboardingStore = create<OnboardingState>((set) => ({
  status: "not_started",
  hydrated: false,
  async hydrate() {
    try {
      const stored = await activeStorage.getStatus();
      if (stored === "completed" || stored === "skipped") {
        set({ status: stored, hydrated: true });
      } else {
        set({ status: "not_started", hydrated: true });
      }
    } catch {
      set({ status: "not_started", hydrated: true });
    }
  },
  async completeDiscovery() {
    try {
      await activeStorage.setStatus("completed");
    } catch {
      // In edge environments, still update in-memory state
    }
    set({ status: "completed" });
  },
  async skipDiscovery() {
    try {
      await activeStorage.setStatus("skipped");
    } catch {
      // In edge environments, still update in-memory state
    }
    set({ status: "skipped" });
  },
  async resetDiscovery() {
    try {
      await activeStorage.clearStatus();
    } catch {
      // Ignore clear errors
    }
    set({ status: "not_started" });
  },
}));
