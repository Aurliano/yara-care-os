import { PermissionsAndroid, Platform, type Permission } from "react-native";

export type MediaPermissionResult = {
  camera: boolean;
  microphone: boolean;
};

/**
 * Request runtime camera and microphone permissions from the operating system.
 * Essential for LiveKit Native WebRTC calls on Android & iOS.
 */
export async function requestMediaPermissions(
  channel: "VOICE" | "VIDEO" = "VIDEO",
): Promise<MediaPermissionResult> {
  if (Platform.OS === "android") {
    try {
      const permissionsToRequest: Permission[] = [
        PermissionsAndroid.PERMISSIONS.RECORD_AUDIO,
      ];
      if (channel === "VIDEO") {
        permissionsToRequest.push(PermissionsAndroid.PERMISSIONS.CAMERA);
      }

      const granted = await PermissionsAndroid.requestMultiple(permissionsToRequest);

      const micGranted =
        granted[PermissionsAndroid.PERMISSIONS.RECORD_AUDIO] ===
        PermissionsAndroid.RESULTS.GRANTED;
      const camGranted =
        channel === "VIDEO"
          ? granted[PermissionsAndroid.PERMISSIONS.CAMERA] ===
            PermissionsAndroid.RESULTS.GRANTED
          : true;

      return {
        microphone: micGranted,
        camera: camGranted,
      };
    } catch (e) {
      console.warn("Failed to request media permissions on Android", e);
      return { camera: false, microphone: false };
    }
  }

  // On iOS / Web, permissions are prompted when accessing navigator.mediaDevices / native module
  return { camera: true, microphone: true };
}
