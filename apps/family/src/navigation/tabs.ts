import { t } from "../i18n";
import type { IconKey } from "../ui/iconXml";

export const APP_TABS: { href: string; label: string; icon: IconKey; match: string }[] = [
  { href: "/(app)/(tabs)", label: t.navHome, icon: "nav_home", match: "home" },
  { href: "/(app)/(tabs)/program", label: t.navProgram, icon: "nav_program", match: "program" },
  { href: "/(app)/(tabs)/call", label: t.navCall, icon: "phone", match: "call" },
  { href: "/(app)/(tabs)/devices", label: t.navDevices, icon: "nav_devices", match: "devices" },
  { href: "/(app)/(tabs)/more", label: t.navMore, icon: "nav_more", match: "more" },
];
