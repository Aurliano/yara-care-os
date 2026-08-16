jest.mock("expo-secure-store", () => ({
  getItemAsync: jest.fn(async () => null),
  setItemAsync: jest.fn(async () => undefined),
  deleteItemAsync: jest.fn(async () => undefined),
}));

jest.mock("expo-localization", () => ({
  getLocales: () => [{ languageTag: "fa-IR", languageCode: "fa", textDirection: "rtl" }],
}));

jest.mock("expo-constants", () => ({
  expoConfig: { extra: { apiBaseUrl: "http://localhost:8000/api/v1" } },
}));

jest.mock("expo/virtual/env", () => ({ env: process.env }), { virtual: true });
