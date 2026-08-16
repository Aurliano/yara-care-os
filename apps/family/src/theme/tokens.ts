/**
 * Design tokens from Figma file 4dI1cdsCzaD2d6X02T8O0W
 * (Calm dashboard 1:535 and shared chrome) plus design/TOKENS.md.
 */
export const colors = {
  background: "#F5FAF8",
  surface: "#FFFFFF",
  surfaceMuted: "#F0F5F2",
  surfaceSoft: "#EAEFED",
  primary: "#00685F",
  primaryPressed: "#00554E",
  primaryOn: "#FFFFFF",
  secondary: "#006398",
  success: "#008378",
  successSoft: "#ECFDF5",
  successOn: "#006A61",
  warning: "#E65100",
  warningSoft: "#FFF8E1",
  warningBorder: "#FFE082",
  warningAccent: "#F57F17",
  warningBrown: "#924628",
  error: "#BA1A1A",
  errorSoft: "#FFDAD6",
  errorOn: "#93000A",
  info: "#5BB8FE",
  infoOn: "#00476E",
  infoSoft: "rgba(91, 184, 254, 0.2)",
  text: "#171D1C",
  textSecondary: "#3D4947",
  textMuted: "#6D7A77",
  textPlaceholder: "#BCC9C6",
  border: "#E5E7EB",
  borderStrong: "#BCC9C6",
  borderMuted: "#DEE4E1",
  timeline: "#DEE4E1",
  medicationAccent: "#6BD8CB",
  overlay: "rgba(0, 0, 0, 0.05)",
} as const;

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  screen: 20,
} as const;

export const radius = {
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  pill: 9999,
} as const;

export const typography = {
  display: { fontSize: 32, lineHeight: 40, fontFamily: "Vazirmatn_700Bold" },
  headline: { fontSize: 24, lineHeight: 36, fontFamily: "Vazirmatn_700Bold" },
  title: { fontSize: 20, lineHeight: 30, fontFamily: "Vazirmatn_700Bold" },
  subtitle: { fontSize: 16, lineHeight: 24, fontFamily: "Vazirmatn_400Regular" },
  body: { fontSize: 16, lineHeight: 24, fontFamily: "Vazirmatn_400Regular" },
  bodyStrong: { fontSize: 16, lineHeight: 24, fontFamily: "Vazirmatn_600SemiBold" },
  label: { fontSize: 14, lineHeight: 20, fontFamily: "Vazirmatn_600SemiBold" },
  caption: { fontSize: 12, lineHeight: 16, fontFamily: "Vazirmatn_500Medium" },
  time: { fontSize: 32, lineHeight: 40, fontFamily: "Vazirmatn_700Bold" },
} as const;

export const elevation = {
  card: {
    shadowColor: "#1E2923",
    shadowOpacity: 0.05,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 4 },
    elevation: 2,
  },
  bar: {
    shadowColor: "#000000",
    shadowOpacity: 0.1,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: -2 },
    elevation: 8,
  },
} as const;

export const sizes = {
  touch: 44,
  nav: 64,
  iconSm: 16,
  iconMd: 20,
  iconLg: 24,
  avatarSm: 32,
  avatarMd: 40,
  avatarLg: 64,
  heroIcon: 64,
} as const;

export const motion = {
  duration: 180,
} as const;

export type ColorToken = keyof typeof colors;
