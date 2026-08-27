import { PermissionsAndroid, Platform } from "react-native";
import { requestMediaPermissions } from "../permissions/mediaPermissions";

describe("requestMediaPermissions", () => {
  const originalPlatform = Platform.OS;

  afterEach(() => {
    Object.defineProperty(Platform, "OS", {
      value: originalPlatform,
      configurable: true,
    });
    jest.clearAllMocks();
  });

  it("requests audio and camera permissions on Android for VIDEO call", async () => {
    Object.defineProperty(Platform, "OS", {
      value: "android",
      configurable: true,
    });

    const requestMultipleSpy = jest
      .spyOn(PermissionsAndroid, "requestMultiple")
      .mockResolvedValueOnce({
        [PermissionsAndroid.PERMISSIONS.RECORD_AUDIO]: PermissionsAndroid.RESULTS.GRANTED,
        [PermissionsAndroid.PERMISSIONS.CAMERA]: PermissionsAndroid.RESULTS.GRANTED,
      } as never);

    const result = await requestMediaPermissions("VIDEO");

    expect(requestMultipleSpy).toHaveBeenCalledWith([
      PermissionsAndroid.PERMISSIONS.RECORD_AUDIO,
      PermissionsAndroid.PERMISSIONS.CAMERA,
    ]);
    expect(result).toEqual({
      microphone: true,
      camera: true,
    });
  });

  it("requests only audio permission on Android for VOICE call", async () => {
    Object.defineProperty(Platform, "OS", {
      value: "android",
      configurable: true,
    });

    const requestMultipleSpy = jest
      .spyOn(PermissionsAndroid, "requestMultiple")
      .mockResolvedValueOnce({
        [PermissionsAndroid.PERMISSIONS.RECORD_AUDIO]: PermissionsAndroid.RESULTS.GRANTED,
      } as never);

    const result = await requestMediaPermissions("VOICE");

    expect(requestMultipleSpy).toHaveBeenCalledWith([
      PermissionsAndroid.PERMISSIONS.RECORD_AUDIO,
    ]);
    expect(result).toEqual({
      microphone: true,
      camera: true,
    });
  });

  it("handles denied permissions on Android gracefully", async () => {
    Object.defineProperty(Platform, "OS", {
      value: "android",
      configurable: true,
    });

    jest.spyOn(PermissionsAndroid, "requestMultiple").mockResolvedValueOnce({
      [PermissionsAndroid.PERMISSIONS.RECORD_AUDIO]: PermissionsAndroid.RESULTS.DENIED,
      [PermissionsAndroid.PERMISSIONS.CAMERA]: PermissionsAndroid.RESULTS.DENIED,
    } as never);

    const result = await requestMediaPermissions("VIDEO");

    expect(result).toEqual({
      microphone: false,
      camera: false,
    });
  });

  it("returns true on iOS / non-android platforms", async () => {
    Object.defineProperty(Platform, "OS", {
      value: "ios",
      configurable: true,
    });

    const result = await requestMediaPermissions("VIDEO");

    expect(result).toEqual({
      microphone: true,
      camera: true,
    });
  });
});
