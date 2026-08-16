import { useRouter } from "expo-router";
import { Image, StyleSheet, View } from "react-native";
import { t } from "../i18n";
import { colors, spacing } from "../theme/tokens";
import { images } from "./Icon";
import { AppText } from "./AppText";
import { Button } from "./Button";
import { Screen } from "./Screen";
import { TopAppBar } from "./TopAppBar";

export function PermissionDenied() {
  const router = useRouter();
  return (
    <Screen>
      <TopAppBar />
      <View style={styles.body}>
        <Image source={images.permissionDenied} style={styles.image} resizeMode="contain" />
        <AppText variant="headline" align="center">
          {t.permissionDeniedTitle}
        </AppText>
        <AppText variant="body" color={colors.textSecondary} align="center">
          {t.permissionDeniedBody}
        </AppText>
        <Button label={t.backHome} onPress={() => router.replace("/(app)/(tabs)")} icon="nav_home" />
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  body: { gap: spacing.md, alignItems: "center", paddingTop: spacing.xl },
  image: { width: 192, height: 192 },
});
