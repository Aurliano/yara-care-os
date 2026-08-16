import * as SecureStore from "expo-secure-store";

const ACCESS_KEY = "yara.accessToken";
const REFRESH_KEY = "yara.refreshToken";

export type TokenStore = {
  getAccessToken: () => Promise<string | null>;
  getRefreshToken: () => Promise<string | null>;
  setTokens: (access: string, refresh?: string | null) => Promise<void>;
  clear: () => Promise<void>;
};

export const secureTokenStore: TokenStore = {
  async getAccessToken() {
    return SecureStore.getItemAsync(ACCESS_KEY);
  },
  async getRefreshToken() {
    return SecureStore.getItemAsync(REFRESH_KEY);
  },
  async setTokens(access, refresh) {
    await SecureStore.setItemAsync(ACCESS_KEY, access);
    if (refresh) {
      await SecureStore.setItemAsync(REFRESH_KEY, refresh);
    }
  },
  async clear() {
    await SecureStore.deleteItemAsync(ACCESS_KEY);
    await SecureStore.deleteItemAsync(REFRESH_KEY);
  },
};

let activeStore: TokenStore = secureTokenStore;

export function setTokenStore(store: TokenStore): void {
  activeStore = store;
}

export function getTokenStore(): TokenStore {
  return activeStore;
}
