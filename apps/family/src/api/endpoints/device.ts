import { apiRequest } from "../client";
import type { Device, DeviceState, Pairing } from "../types";

export function getDevice(deviceId: string): Promise<Device> {
  return apiRequest(`/devices/${deviceId}/`);
}

export function getDeviceState(deviceId: string): Promise<DeviceState> {
  return apiRequest(`/devices/${deviceId}/state/`);
}

export function listPairings(deviceId: string): Promise<Pairing[]> {
  return apiRequest(`/devices/${deviceId}/pairings/`);
}

export function createPairing(
  hubDeviceId: string,
  body: { hub_device_id: string; peripheral_device_id: string },
): Promise<Pairing> {
  return apiRequest(`/devices/${hubDeviceId}/pairings/`, { method: "POST", body });
}

export function revokePairing(pairingId: string): Promise<Pairing> {
  return apiRequest(`/pairings/${pairingId}/revoke/`, { method: "POST" });
}
