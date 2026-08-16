import { useState } from "react";
import { Pressable, StyleSheet, TextInput, View } from "react-native";
import { colors, radius, spacing, typography } from "../theme/tokens";
import { AppText } from "./AppText";
import { Icon } from "./Icon";
import type { IconKey } from "../ui/iconXml";
import { toLatinDigits, toPersianDigits } from "../i18n/numerals";

type Props = {
  label: string;
  value: string;
  onChangeText: (value: string) => void;
  placeholder?: string;
  icon?: IconKey;
  secure?: boolean;
  keyboardType?: "default" | "phone-pad" | "email-address" | "numeric";
  persianValue?: boolean;
};

export function TextField({
  label,
  value,
  onChangeText,
  placeholder,
  icon,
  secure,
  keyboardType = "default",
  persianValue = true,
}: Props) {
  const [hidden, setHidden] = useState(secure ?? false);
  const display = persianValue ? toPersianDigits(value) : value;
  return (
    <View style={styles.wrap}>
      <AppText variant="caption" color={colors.text}>
        {label}
      </AppText>
      <View style={styles.inputWrap}>
        <TextInput
          value={display}
          onChangeText={(next) => onChangeText(persianValue ? toLatinDigits(next) : next)}
          placeholder={placeholder}
          placeholderTextColor={colors.textPlaceholder}
          secureTextEntry={hidden}
          keyboardType={keyboardType}
          style={styles.input}
          textAlign="right"
        />
        {icon ? (
          <View style={styles.leading}>
            <Icon name={icon} color={colors.textMuted} width={16} height={20} />
          </View>
        ) : null}
        {secure ? (
          <Pressable style={styles.trailing} onPress={() => setHidden((value) => !value)}>
            <Icon name="eye_off" color={colors.textMuted} width={22} height={20} />
          </Pressable>
        ) : null}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { gap: spacing.xs, width: "100%" },
  inputWrap: { position: "relative", justifyContent: "center" },
  input: {
    height: 44,
    backgroundColor: colors.background,
    borderWidth: 1,
    borderColor: colors.borderStrong,
    borderRadius: radius.sm,
    paddingHorizontal: 48,
    ...typography.body,
    color: colors.text,
  },
  leading: { position: "absolute", right: 16, top: 10 },
  trailing: { position: "absolute", left: 16, top: 10 },
});
