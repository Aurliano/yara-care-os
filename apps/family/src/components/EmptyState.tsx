import { Image, StyleSheet, View } from "react-native";
import { colors, spacing } from "../theme/tokens";
import { AppText } from "./AppText";
import { Button } from "./Button";

type Props = {
  title: string;
  body: string;
  image?: number;
  actionLabel?: string;
  onAction?: () => void;
  secondaryLabel?: string;
  onSecondary?: () => void;
};

export function EmptyState({
  title,
  body,
  image,
  actionLabel,
  onAction,
  secondaryLabel,
  onSecondary,
}: Props) {
  return (
    <View style={styles.wrap}>
      {image ? <Image source={image} style={styles.image} resizeMode="contain" /> : null}
      <AppText variant="title" align="center">
        {title}
      </AppText>
      <AppText variant="subtitle" color={colors.textSecondary} align="center">
        {body}
      </AppText>
      {actionLabel && onAction ? <Button label={actionLabel} onPress={onAction} /> : null}
      {secondaryLabel && onSecondary ? (
        <Button label={secondaryLabel} onPress={onSecondary} variant="secondary" />
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { gap: spacing.md, alignItems: "center", paddingVertical: spacing.xl },
  image: { width: 220, height: 160 },
});
