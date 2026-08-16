import { StyleSheet, View } from "react-native";
import { colors, sizes } from "../theme/tokens";
import { AppText } from "./AppText";

export function Avatar({ name, size = sizes.avatarLg }: { name: string; size?: number }) {
  const initial = name.trim().slice(0, 1) || "؟";
  return (
    <View style={[styles.circle, { width: size, height: size, borderRadius: size / 2 }]}>
      <AppText variant="label" color={colors.primary} align="center">
        {initial}
      </AppText>
    </View>
  );
}

const styles = StyleSheet.create({
  circle: {
    backgroundColor: colors.surfaceSoft,
    borderWidth: 2,
    borderColor: colors.borderMuted,
    alignItems: "center",
    justifyContent: "center",
  },
});
