import { create } from "zustand";
import * as SecureStore from "expo-secure-store";

const ACK_KEY = "yara.alertAcks";

type AlertAckState = {
  acknowledgedIds: string[];
  hydrate: () => Promise<void>;
  acknowledge: (alertId: string) => Promise<void>;
  isAcknowledged: (alertId: string) => boolean;
};

export const useAlertAckStore = create<AlertAckState>((set, get) => ({
  acknowledgedIds: [],
  async hydrate() {
    const raw = await SecureStore.getItemAsync(ACK_KEY);
    set({ acknowledgedIds: raw ? (JSON.parse(raw) as string[]) : [] });
  },
  async acknowledge(alertId) {
    const next = Array.from(new Set([...get().acknowledgedIds, alertId]));
    await SecureStore.setItemAsync(ACK_KEY, JSON.stringify(next));
    set({ acknowledgedIds: next });
  },
  isAcknowledged(alertId) {
    return get().acknowledgedIds.includes(alertId);
  },
}));
