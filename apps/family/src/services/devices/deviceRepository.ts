/**
 * Backend has device-scoped routes but no GET /elders/{id}/devices/ read-model.
 * Until that exists, the family app cannot list Hub/Pill Box for an elder.
 */

export type ElderDeviceCatalog =
  | { available: false; reason: "ELDER_DEVICE_LIST_MISSING"; items: [] }
  | {
      available: true;
      items: {
        id: string;
        kind: "HUB" | "PILLBOX" | "OTHER";
        lastSeenAt: string | null;
        batteryPercent: number | null;
        pairingStatus: string | null;
        connectivity: "online" | "offline" | "unknown";
      }[];
    };

export async function loadElderDevices(_elderId: string): Promise<ElderDeviceCatalog> {
  return { available: false, reason: "ELDER_DEVICE_LIST_MISSING", items: [] };
}

export function readBattery(state: Record<string, unknown>): number | null {
  const value = state.battery_percent ?? state.battery ?? state.charge;
  return typeof value === "number" ? value : null;
}
