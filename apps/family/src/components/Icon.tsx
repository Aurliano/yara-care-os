import { Image, type ImageStyle, type StyleProp } from "react-native";
import { SvgXml } from "react-native-svg";
import { ICON_XML, type IconKey } from "../ui/iconXml";
import { colors, sizes } from "../theme/tokens";

type Props = {
  name: IconKey;
  color?: string;
  width?: number;
  height?: number;
};

function viewBoxOf(xml: string): { w: number; h: number } {
  const match = xml.match(/viewBox="0 0 ([0-9.]+) ([0-9.]+)"/);
  if (!match) {
    return { w: sizes.iconMd, h: sizes.iconMd };
  }
  return { w: Number(match[1]), h: Number(match[2]) };
}

export function Icon({ name, color = colors.primary, width, height }: Props) {
  const xml = ICON_XML[name].replaceAll("currentColor", color);
  const box = viewBoxOf(ICON_XML[name]);
  const w = width ?? box.w;
  const h = height ?? box.h;
  return <SvgXml xml={xml} width={w} height={h} />;
}

export function LocalImage({
  source,
  style,
}: {
  source: number;
  style?: StyleProp<ImageStyle>;
}) {
  return <Image source={source} style={style} />;
}

export const images = {
  logo: require("../../assets/images/yara-logo.png"),
  noElder: require("../../assets/illustrations/no-elder.png"),
  permissionDenied: require("../../assets/illustrations/permission-denied.png"),
};
