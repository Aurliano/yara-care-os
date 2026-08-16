import { useLocalSearchParams } from "expo-router";
import { useQuery } from "@tanstack/react-query";
import { AppText, Card, EmptyState, LoadingSkeleton, Screen, StatusBadge, TopAppBar } from "../../../src/components";
import { t, formatRelative, toPersianDigits } from "../../../src/i18n";
import { spacing } from "../../../src/theme/tokens";
import { getDevice, getDeviceState, listPairings } from "../../../src/api/endpoints/device";
import { readBattery } from "../../../src/services/devices/deviceRepository";
import { queryKeys } from "../../../src/api/queryKeys";
import { firstParam } from "../../../src/navigation/params";
import { StyleSheet, View } from "react-native";

export default function DeviceDetailScreen() {
  const deviceId = firstParam(useLocalSearchParams<{ deviceId: string }>().deviceId) ?? "";
  const device = useQuery({
    queryKey: ["device", deviceId],
    enabled: Boolean(deviceId),
    queryFn: () => getDevice(deviceId),
  });
  const state = useQuery({
    queryKey: queryKeys.deviceState(deviceId),
    enabled: Boolean(deviceId),
    queryFn: () => getDeviceState(deviceId),
  });
  const pairings = useQuery({
    queryKey: queryKeys.pairings(deviceId),
    enabled: Boolean(deviceId),
    queryFn: () => listPairings(deviceId),
  });

  if (device.isPending) {
    return (
      <Screen>
        <LoadingSkeleton />
      </Screen>
    );
  }
  if (device.isError || !device.data) {
    return (
      <Screen>
        <TopAppBar title={t.devicesTitle} showBack />
        <EmptyState title={t.devicesUnavailableTitle} body={t.devicesUnavailableBody} />
      </Screen>
    );
  }

  const battery = state.data ? readBattery(state.data.current_state) : null;
  const lastSeen = state.data?.last_seen_at ?? device.data.last_seen_at;

  return (
    <Screen>
      <TopAppBar title={t.viewDetails} showBack />
      <Card accent={device.data.operational_status === "ACTIVE" ? "success" : "error"}>
        <AppText variant="title">{device.data.serial_number}</AppText>
        <StatusBadge
          label={device.data.operational_status === "ACTIVE" ? t.connected : t.disconnected}
          tone={device.data.operational_status === "ACTIVE" ? "success" : "error"}
        />
        <View style={styles.row}>
          <AppText variant="caption">
            {t.lastSeen}: {lastSeen ? formatRelative(lastSeen) : t.unknownValue}
          </AppText>
          <AppText variant="title">
            {battery === null ? t.batteryUnknown : `${toPersianDigits(battery)}٪`}
          </AppText>
        </View>
      </Card>
      {(pairings.data ?? []).map((pairing) => (
        <Card key={pairing.id}>
          <AppText variant="label">{pairing.status}</AppText>
        </Card>
      ))}
    </Screen>
  );
}

const styles = StyleSheet.create({
  row: { marginTop: spacing.md, flexDirection: "row", justifyContent: "space-between" },
});
