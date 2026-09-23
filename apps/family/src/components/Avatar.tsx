import { useState } from "react";
import { Image, StyleSheet, View } from "react-native";
import { colors, sizes } from "../theme/tokens";
import { AppText } from "./AppText";

export function Avatar({
  name,
  photoUrl,
  size = sizes.avatarLg,
}: {
  name: string;
  photoUrl?: string | null;
  size?: number;
}) {
  const [loadFailed, setLoadFailed] = useState(false);
  const initial = name.trim().slice(0, 1) || "؟";

  if (photoUrl && !loadFailed) {
    return (
      <View style={[styles.circle, { width: size, height: size, borderRadius: size / 2, overflow: "hidden" }]}>
        <Image
          source={{ uri: photoUrl }}
          style={{ width: size, height: size }}
          resizeMode="cover"
          onError={() => setLoadFailed(true)}
        />
      </View>
    );
  }

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
