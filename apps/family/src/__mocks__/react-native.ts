import React from "react";

export const Platform = {
  OS: "android",
  select: (obj: Record<string, unknown>) => obj.android ?? obj.default,
};

export const PermissionsAndroid = {
  PERMISSIONS: {
    RECORD_AUDIO: "android.permission.RECORD_AUDIO",
    CAMERA: "android.permission.CAMERA",
  },
  RESULTS: {
    GRANTED: "granted",
    DENIED: "denied",
    NEVER_ASK_AGAIN: "never_ask_again",
  },
  requestMultiple: jest.fn(async () => ({
    "android.permission.RECORD_AUDIO": "granted",
    "android.permission.CAMERA": "granted",
  })),
  request: jest.fn(async () => "granted"),
  check: jest.fn(async () => true),
};

export const Linking = {
  openURL: jest.fn(async () => undefined),
  canOpenURL: jest.fn(async () => true),
};

export const AppState = {
  currentState: "active",
  addEventListener: jest.fn(() => ({ remove: jest.fn() })),
};

export const StyleSheet = {
  create: <T extends Record<string, unknown>>(styles: T): T => styles,
  flatten: (style: any): any => {
    if (!style) return {};
    if (Array.isArray(style)) {
      return style.reduce((acc, curr) => ({ ...acc, ...(curr ? StyleSheet.flatten(curr) : {}) }), {});
    }
    return style;
  },
};

export const View = ({ children, ...props }: any) => React.createElement("View", props, children);
export const Text = ({ children, ...props }: any) => React.createElement("Text", props, children);
export const Modal = ({ children, ...props }: any) => props.visible !== false ? React.createElement("Modal", props, children) : null;
export const Pressable = ({ children, onPress, ...props }: any) => React.createElement("Pressable", { onClick: onPress, ...props }, typeof children === "function" ? children({ pressed: false }) : children);
export const ActivityIndicator = (props: any) => React.createElement("ActivityIndicator", props);
export const Touchable = { Mixin: {} };
export const Image = (props: any) => React.createElement("Image", props);

export default {
  Platform,
  PermissionsAndroid,
  Linking,
  AppState,
  StyleSheet,
  View,
  Text,
  Modal,
  Pressable,
  ActivityIndicator,
  Touchable,
  Image,
};
