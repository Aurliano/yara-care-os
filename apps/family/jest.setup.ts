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

jest.mock("react-native-safe-area-context", () => {
  const React = require("react");
  return {
    SafeAreaView: ({ children, ...props }: any) => React.createElement("SafeAreaView", props, children),
    SafeAreaProvider: ({ children }: any) => children,
    useSafeAreaInsets: () => ({ top: 0, bottom: 0, left: 0, right: 0 }),
  };
});

jest.mock("react-native-svg", () => {
  const React = require("react");
  return {
    SvgXml: (props: any) => React.createElement("SvgXml", props),
    Svg: ({ children, ...props }: any) => React.createElement("Svg", props, children),
    Path: (props: any) => React.createElement("Path", props),
  };
});

jest.mock("livekit-client", () => {
  class MockRoom {
    on = jest.fn();
    off = jest.fn();
    connect = jest.fn(async () => undefined);
    disconnect = jest.fn();
    localParticipant = {
      setMicrophoneEnabled: jest.fn(async () => undefined),
      setCameraEnabled: jest.fn(async () => undefined),
    };
  }
  return {
    Room: MockRoom,
    RoomEvent: {
      Connected: "connected",
      Disconnected: "disconnected",
      TrackSubscribed: "trackSubscribed",
      TrackUnsubscribed: "trackUnsubscribed",
    },
  };
});
