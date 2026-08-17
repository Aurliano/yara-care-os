import * as SecureStore from "expo-secure-store";
import type { KeyValueStore } from "./CommunicationRepository";

export function createSecureStoreKeyValueStore(): KeyValueStore {
  return {
    getItem: (key) => SecureStore.getItemAsync(key),
    setItem: (key, value) => SecureStore.setItemAsync(key, value),
    removeItem: (key) => SecureStore.deleteItemAsync(key),
  };
}
