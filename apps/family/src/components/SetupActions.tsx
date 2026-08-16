import { StyleSheet, View } from "react-native";
import { Button } from "./Button";
import { t } from "../i18n";
import { spacing } from "../theme/tokens";

type Props = {
  onAddMedication: () => void;
  onAddAppointment: () => void;
  onConnectDevice: () => void;
};

export function SetupActions({ onAddMedication, onAddAppointment, onConnectDevice }: Props) {
  return (
    <View style={styles.wrap}>
      <Button label={t.addMedication} icon="medication" onPress={onAddMedication} />
      <Button label={t.addAppointment} icon="calendar" onPress={onAddAppointment} variant="secondary" />
      <Button label={t.connectDevice} icon="nav_devices" onPress={onConnectDevice} variant="secondary" />
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { gap: spacing.sm, width: "100%", marginTop: spacing.md },
});
