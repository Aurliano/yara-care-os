import { create } from "zustand";
import * as SecureStore from "expo-secure-store";

const ELDER_KEY = "yara.selectedElderId";

type ElderState = {
  selectedElderId: string | null;
  hydrated: boolean;
  hydrate: () => Promise<void>;
  selectElder: (elderId: string) => Promise<void>;
  clearElder: () => Promise<void>;
};

export const useElderStore = create<ElderState>((set) => ({
  selectedElderId: null,
  hydrated: false,
  async hydrate() {
    const stored = await SecureStore.getItemAsync(ELDER_KEY);
    set({ selectedElderId: stored, hydrated: true });
  },
  async selectElder(elderId) {
    await SecureStore.setItemAsync(ELDER_KEY, elderId);
    set({ selectedElderId: elderId });
  },
  async clearElder() {
    await SecureStore.deleteItemAsync(ELDER_KEY);
    set({ selectedElderId: null });
  },
}));
