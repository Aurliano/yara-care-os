import { create } from "zustand";
import { login } from "../api/client";
import { getCurrentUser } from "../api/endpoints/identity";
import { getTokenStore } from "../api/tokenStore";
import type { User } from "../api/types";
import { toLatinDigits } from "../i18n/numerals";

type SessionState = {
  hydrating: boolean;
  user: User | null;
  hydrate: () => Promise<void>;
  signIn: (phone: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  setUser: (user: User | null) => void;
};

export const useSessionStore = create<SessionState>((set) => ({
  hydrating: true,
  user: null,
  async hydrate() {
    const store = getTokenStore();
    const access = await store.getAccessToken();
    if (!access) {
      set({ hydrating: false, user: null });
      return;
    }
    try {
      const user = await getCurrentUser();
      set({ user, hydrating: false });
    } catch {
      await store.clear();
      set({ user: null, hydrating: false });
    }
  },
  async signIn(phone, password) {
    const tokens = await login(toLatinDigits(phone).trim(), password);
    await getTokenStore().setTokens(tokens.access, tokens.refresh);
    const user = await getCurrentUser();
    set({ user });
  },
  async signOut() {
    await getTokenStore().clear();
    set({ user: null });
  },
  setUser(user) {
    set({ user });
  },
}));
