import { Text as RNText, type TextProps, type TextStyle } from "react-native";
import { toPersianDigits } from "../i18n/numerals";
import { colors, typography } from "../theme/tokens";

type Variant = keyof typeof typography;

type Props = TextProps & {
  variant?: Variant;
  color?: string;
  persianDigits?: boolean;
  align?: TextStyle["textAlign"];
};

export function AppText({
  variant = "body",
  color = colors.text,
  persianDigits = true,
  align = "right",
  style,
  children,
  ...rest
}: Props) {
  const content =
    persianDigits && (typeof children === "string" || typeof children === "number")
      ? toPersianDigits(children)
      : children;
  return (
    <RNText
      {...rest}
      style={[typography[variant], { color, textAlign: align, writingDirection: "rtl" }, style]}
    >
      {content}
    </RNText>
  );
}
