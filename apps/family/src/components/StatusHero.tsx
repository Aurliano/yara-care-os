import { StyleSheet, View } from "react-native";
import { t, toPersianDigits } from "../i18n";
import { colors, radius, spacing } from "../theme/tokens";
import type { DashboardTone } from "../services/dashboard/composeDashboard";
import { AppText } from "./AppText";
import { Icon } from "./Icon";

const COPY: Record<DashboardTone, { title: (name: string, count?: number) => string; body: string; bg: string; fg: string; icon: "heart" | "attention" | "info" }> =
  {
    calm: {
      title: (name) => t.calmTitle(name),
      body: t.calmBody,
      bg: colors.successSoft,
      fg: colors.success,
      icon: "heart",
    },
    attention: {
      title: (_name, count = 1) => t.attentionTitle(toPersianDigits(count)),
      body: t.attentionBody,
      bg: colors.warningSoft,
      fg: colors.warning,
      icon: "attention",
    },
    urgent: {
      title: () => t.urgentTitle,
      body: t.attentionBody,
      bg: colors.errorSoft,
      fg: colors.error,
      icon: "attention",
    },
    unknown: {
      title: () => t.unknownTitle,
      body: t.unknownBody,
      bg: colors.surfaceMuted,
      fg: colors.textSecondary,
      icon: "info",
    },
  };

export function StatusHero({
  tone,
  elderName,
  count,
}: {
  tone: DashboardTone;
  elderName: string;
  count?: number;
}) {
  const spec = COPY[tone];
  return (
    <View style={[styles.hero, { backgroundColor: spec.bg, borderColor: tone === "attention" ? colors.warningBorder : colors.border }]}>
      <View style={[styles.iconWrap, { backgroundColor: spec.fg }]}>
        <Icon name={spec.icon} color={colors.primaryOn} width={24} height={24} />
      </View>
      <AppText variant="headline" color={spec.fg} align="center">
        {spec.title(elderName.split(" ")[0] ?? elderName, count)}
      </AppText>
      <AppText variant="body" color={colors.textSecondary} align="center">
        {spec.body}
      </AppText>
    </View>
  );
}

const styles = StyleSheet.create({
  hero: {
    borderRadius: radius.md,
    borderWidth: 1,
    padding: spacing.lg,
    alignItems: "center",
    gap: spacing.sm,
  },
  iconWrap: {
    width: 64,
    height: 64,
    borderRadius: 32,
    alignItems: "center",
    justifyContent: "center",
  },
});
