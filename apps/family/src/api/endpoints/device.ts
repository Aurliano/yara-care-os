import { apiRequest } from "../client";
import type { Device, DeviceState, Pairing } from "../types";

export type ElderDeviceSummary = {
  id: string;
  kind: "HUB" | "PILLBOX" | "OTHER";
  serial_number: string;
  operational_status: string;
  last_seen_at: string | null;
  battery_percent: number | null;
  pairing_status: string | null;
  connectivity: "online" | "offline" | "unknown" | string;
  assignment_type: string;
};

export function listElderDevices(elderId: string): Promise<ElderDeviceSummary[]> {
  return apiRequest(`/elders/${elderId}/devices/`);
}

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
