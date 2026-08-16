import { StyleSheet, View } from "react-native";
import { t } from "../i18n";
import { colors, radius, spacing } from "../theme/tokens";
import { AppText } from "./AppText";

export function StaleBanner({ updatedLabel }: { updatedLabel: string }) {
  return (
    <View style={styles.banner} accessibilityLiveRegion="polite">
      <AppText variant="label" color={colors.warningBrown} align="center">
        {t.staleTitle}
      </AppText>
      <AppText variant="caption" color={colors.textSecondary} align="center">
        {`${t.staleBody} ${t.lastUpdated}: ${updatedLabel}`}
      </AppText>
    </View>
  );
}

const styles = StyleSheet.create({
  banner: {
    backgroundColor: colors.warningSoft,
    borderColor: colors.warningBorder,
    borderWidth: 1,
    borderRadius: radius.md,
    padding: spacing.md,
    gap: spacing.xs,
  },
});
