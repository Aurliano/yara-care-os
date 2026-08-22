import { listElderDevices, type ElderDeviceSummary } from "../../api/endpoints/device";

export type ElderDeviceItem = {
  id: string;
  kind: "HUB" | "PILLBOX" | "OTHER";
  lastSeenAt: string | null;
  batteryPercent: number | null;
  pairingStatus: string | null;
  connectivity: "online" | "offline" | "unknown";
};

export type ElderDeviceCatalog =
  | { available: false; reason: "ELDER_DEVICE_LIST_MISSING"; items: [] }
  | { available: true; items: ElderDeviceItem[] };

export function normalizeConnectivity(value: unknown): "online" | "offline" | "unknown" {
  if (value === "online" || value === "offline") {
    return value;
  }
  return "unknown";
}

export function isDeviceConnected(connectivity: "online" | "offline" | "unknown"): boolean {
  return connectivity === "online";
}

function toCatalogItem(device: ElderDeviceSummary): ElderDeviceItem {
  return {
    id: device.id,
    kind: device.kind,
    lastSeenAt: device.last_seen_at,
    batteryPercent: device.battery_percent,
    pairingStatus: device.pairing_status,
    connectivity: normalizeConnectivity(device.connectivity),
  };
}

export async function loadElderDevices(elderId: string): Promise<ElderDeviceCatalog> {
  const devices = await listElderDevices(elderId);
  return { available: true, items: devices.map(toCatalogItem) };
}

export function readBattery(state: Record<string, unknown>): number | null {
  const value = state.battery_percent ?? state.battery ?? state.charge;
  return typeof value === "number" ? value : null;
}
