import { useState } from "react";
import { Alert, Linking, ScrollView, StyleSheet, View } from "react-native";
import { AppText, Button, Card, Screen, StatusBadge, TopAppBar } from "../../src/components";
import { Icon } from "../../src/components/Icon";
import { colors, radius, spacing } from "../../src/theme/tokens";

type ProductItem = {
  id: string;
  title: string;
  subtitle: string;
  description: string;
  features: string[];
  itemsIncluded: string[];
  status: "available" | "coming_soon";
  statusLabel: string;
  url: string;
  icon: "hub" | "pillbox" | "heart";
  priceSummary?: string;
  priceOriginal?: string;
  discountBadge?: string;
  priceNote?: string;
};

const PRODUCTS: ProductItem[] = [
  {
    id: "sayda-hub",
    title: "هاب رومیزی سایدا (SAYDA Hub)",
    subtitle: "همراه آرام و باوقار سالمند در خانه",
    description:
      "دستگاه رومیزی مستقل با صفحه‌نمایش لمسی، ساعت و تاریخ شمسی بزرگ، یادآوری صوتی ملایم نوبت‌های دارو و دکمه تک‌لمسی تأیید مصرف. کارکرد مستقل حتی در زمان قطعی اینترنت.",
    priceSummary: "۳۸,۹۰۰,۰۰۰ تومان",
    priceOriginal: "۴۲,۰۰۰,۰۰۰ تومان",
    discountBadge: "تخفیف ویژه ۳,۱۰۰,۰۰۰ تومان",
    priceNote: "شامل ۳ ماه اشتراک رایگان سامانه و پشتیبانی دائمی | امکان اجاره مدت‌دار دستگاه",
    features: [
      "یادآوری صوتی و لمسی سر ساعت",
      "امکان تماس صوتی و تصویری مستقیم با خانواده",
      "کارکرد پایدار ساعت و داروها به صورت آفلاین",
    ],
    itemsIncluded: ["تبلت هاب رومیزی سایدا", "پایه چوبی باوقار", "آداپتور و کابل تغذیه دائم", "راهنمای راه‌اندازی"],
    status: "available",
    statusLabel: "آماده سفارش",
    url: "https://care-app.saydatech.ir/#pricing",
    icon: "hub",
  },
  {
    id: "smart-pillbox",
    title: "جعبه داروی هوشمند سایدا",
    subtitle: "محفظه ۷ روزه با راهنمای نوری خانه دارو",
    description:
      "جعبه داروی متصل به هاب خانگی با نشانگرهای نوری که در هر نوبت، فقط درب خانهٔ داروی همان وعده را مشخص می‌کند تا از اشتباهات دارویی پیشگیری شود.",
    priceSummary: "به‌زودی عرضه می‌شود",
    features: [
      "روشن شدن چراغ خانهٔ داروی مورد نظر",
      "سنسور تشخیص باز شدن درب محفظه",
      "همگام‌سازی خودکار با هاب و اپلیکیشن خانواده",
    ],
    itemsIncluded: ["جعبه داروی هوشمند ۷ روزه", "کابل شارژ اختصاصی", "راهنمای فارسی"],
    status: "coming_soon",
    statusLabel: "به‌زودی عرضه می‌شود",
    url: "https://care-app.saydatech.ir/#product-smart-pillbox",
    icon: "pillbox",
  },
  {
    id: "health-band",
    title: "دستبند سلامت و پایش آرام",
    subtitle: "پایش ضربان قلب و ایمنی عزیز سالخورده",
    description:
      "دستبند ضدآب و سبک با باتری بادوام که ضربان قلب و پایداری فیزیکی سالمند را به آرامی ثبت و به هاب رومیزی منتقل می‌کند.",
    priceSummary: "به‌زودی عرضه می‌شود",
    features: [
      "پایش پیوسته ضربان قلب",
      "طراحی بدون دکمه‌های گیج‌کننده و بدون مزاحمت",
      "هشدار باتری در برنامه خانواده قبل از خاموش شدن",
    ],
    itemsIncluded: ["دستبند پایش سلامت", "بند ضدحساسیت", "شارژر مغناطیسی"],
    status: "coming_soon",
    statusLabel: "به‌زودی عرضه می‌شود",
    url: "https://care-app.saydatech.ir/#product-health-band",
    icon: "heart",
  },
];

export default function ProductCatalogScreen() {
  const [openingId, setOpeningId] = useState<string | null>(null);

  async function handleOpenProduct(product: ProductItem) {
    setOpeningId(product.id);
    try {
      const supported = await Linking.canOpenURL(product.url);
      if (supported) {
        await Linking.openURL(product.url);
      } else {
        Alert.alert("خطا در بازکردن صفحه", "امکان باز کردن مرورگر در دستگاه شما وجود ندارد.");
      }
    } catch {
      Alert.alert(
        "ارتباط با وب‌سایت",
        "برای مشاهده مشخصات فنی و ثبت سفارش، لطفاً به وب‌سایت رسمی سایدا به نشانی care-app.saydatech.ir مراجعه فرمایید.",
      );
    } finally {
      setOpeningId(null);
    }
  }

  return (
    <Screen>
      <TopAppBar title="محصولات و تجهیزات سایدا" showBack />
      <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>
        <Card>
          <View style={styles.noticeBox}>
            <AppText variant="title">زیست‌بوم مراقبت هوشمند سایدا</AppText>
            <AppText variant="body" color={colors.textSecondary}>
              تجهیزات فیزیکی سایدا به گونه‌ای طراحی شده‌اند که زندگی مستقل و با عزت را برای سالمندان عزیز فراهم کرده و به
              خانواده‌ها آرامش خاطر هدیه دهند. خرید و ثبت سفارش تجهیزات از طریق وب‌سایت رسمی سایدا انجام می‌پذیرد.
            </AppText>
          </View>
        </Card>

        {PRODUCTS.map((product) => {
          const isAvailable = product.status === "available";
          return (
            <Card key={product.id}>
              <View style={styles.productCard}>
                <View style={styles.headerRow}>
                  <View style={styles.iconWrap}>
                    <Icon name={product.icon} width={28} height={28} color={colors.primary} />
                  </View>
                  <View style={styles.titleArea}>
                    <AppText variant="title">{product.title}</AppText>
                    <AppText variant="caption" color={colors.textSecondary}>
                      {product.subtitle}
                    </AppText>
                  </View>
                  <StatusBadge
                    tone={isAvailable ? "success" : "neutral"}
                    label={product.statusLabel}
                  />
                </View>

                <AppText variant="body" color={colors.textSecondary}>
                  {product.description}
                </AppText>

                <View style={styles.featuresList}>
                  <AppText variant="label">قابلیت‌های برجسته:</AppText>
                  {product.features.map((feat, idx) => (
                    <View key={idx} style={styles.bulletRow}>
                      <View style={styles.bulletDot} />
                      <AppText variant="body" style={{ flex: 1 }}>
                        {feat}
                      </AppText>
                    </View>
                  ))}
                </View>

                <View style={styles.itemsIncludedBox}>
                  <AppText variant="caption" color={colors.textMuted}>
                    اقلام همراه: {product.itemsIncluded.join(" • ")}
                  </AppText>
                </View>

                {product.priceSummary ? (
                  <View style={styles.priceContainer}>
                    <View style={styles.priceRow}>
                      <AppText variant="caption" color={colors.textSecondary}>
                        مبلغ:
                      </AppText>
                      <View style={styles.priceValues}>
                        {product.priceOriginal ? (
                          <AppText variant="caption" color={colors.textMuted} style={styles.strikeThrough}>
                            {product.priceOriginal}
                          </AppText>
                        ) : null}
                        <AppText variant="title" color={colors.primary}>
                          {product.priceSummary}
                        </AppText>
                      </View>
                    </View>
                    {product.discountBadge ? (
                      <View style={styles.discountBadge}>
                        <AppText variant="caption" color={colors.success}>
                          {product.discountBadge}
                        </AppText>
                      </View>
                    ) : null}
                    {product.priceNote ? (
                      <AppText variant="caption" color={colors.textMuted}>
                        {product.priceNote}
                      </AppText>
                    ) : null}
                  </View>
                ) : null}

                <Button
                  label={isAvailable ? "مشاهده و سفارش در وب‌سایت" : "مشاهده جزئیات در وب‌سایت"}
                  variant={isAvailable ? "primary" : "secondary"}
                  loading={openingId === product.id}
                  onPress={() => void handleOpenProduct(product)}
                />
              </View>
            </Card>
          );
        })}

        {/* Subscription & Rental Overview */}
        <Card>
          <View style={styles.noticeBox}>
            <AppText variant="title">طرح‌های اشتراک و اجاره مدت‌دار</AppText>
            <AppText variant="body" color={colors.textSecondary}>
              • اشتراک ماهانه: ۶۵۰,۰۰۰ تومان{"\n"}
              • اشتراک سه‌ماهه (با تخفیف): ۱,۸۵۰,۰۰۰ تومان{"\n"}
              • اشتراک سالانه (با تخفیف ویژه): ۶,۵۰۰,۰۰۰ تومان{"\n"}
              • امکان اجاره مدت‌دار دستگاه هاب با محاسبه روزانه و بدون هزینه اولیه خرید قطعی
            </AppText>
            <View style={styles.supportCallout}>
              <AppText variant="caption" color={colors.primary}>
                در صورت نیاز به همراهی یا عدم امکان تهیه دستگاه، با پشتیبانی سایدا در ارتباط باشید (info@saydatech.ir).
              </AppText>
            </View>
            <Button
              label="مشاهده تعرفه‌ها و محاسبه اجاره در وب‌سایت"
              variant="secondary"
              onPress={() => void Linking.openURL("https://care-app.saydatech.ir/#pricing")}
            />
          </View>
        </Card>
      </ScrollView>
    </Screen>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: spacing.lg,
    paddingBottom: spacing.xl,
  },
  noticeBox: {
    gap: spacing.xs,
  },
  supportCallout: {
    padding: spacing.sm,
    backgroundColor: colors.surfaceMuted,
    borderRadius: radius.sm,
    marginVertical: spacing.xs,
  },
  productCard: {
    gap: spacing.md,
  },
  priceContainer: {
    padding: spacing.sm,
    backgroundColor: colors.surfaceMuted,
    borderRadius: radius.sm,
    gap: 4,
  },
  priceRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  priceValues: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
  },
  strikeThrough: {
    textDecorationLine: "line-through",
  },
  discountBadge: {
    alignSelf: "flex-start",
  },
  headerRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
  },
  iconWrap: {
    width: 48,
    height: 48,
    borderRadius: radius.md,
    backgroundColor: colors.surfaceMuted,
    alignItems: "center",
    justifyContent: "center",
  },
  titleArea: {
    flex: 1,
    gap: 2,
  },
  featuresList: {
    gap: spacing.xs,
    marginTop: spacing.xs,
  },
  bulletRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
  },
  bulletDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: colors.primary,
  },
  itemsIncludedBox: {
    padding: spacing.sm,
    backgroundColor: colors.surfaceMuted,
    borderRadius: radius.sm,
  },
});
