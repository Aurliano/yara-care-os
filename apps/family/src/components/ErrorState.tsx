import { StyleSheet, View } from "react-native";
import { t } from "../i18n";
import { colors, spacing } from "../theme/tokens";
import { AppText } from "./AppText";
import { Button } from "./Button";

export function ErrorState({
  title = t.errorTitle,
  body = t.errorBody,
  onRetry,
}: {
  title?: string;
  body?: string;
  onRetry?: () => void;
}) {
  return (
    <View style={styles.wrap}>
      <AppText variant="title" align="center">
        {title}
      </AppText>
      <AppText variant="body" color={colors.textSecondary} align="center">
        {body}
      </AppText>
      {onRetry ? <Button label={t.retry} onPress={onRetry} /> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { gap: spacing.md, alignItems: "center", paddingVertical: spacing.xl },
});
