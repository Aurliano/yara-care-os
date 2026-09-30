import { useState } from "react";
import {
  AccessibilityInfo,
  Pressable,
  ScrollView,
  StyleSheet,
  View,
} from "react-native";
import { useRouter } from "expo-router";
import { SafeAreaView, useSafeAreaInsets } from "react-native-safe-area-context";
import { t } from "../../src/i18n";
import { colors, elevation, radius, sizes, spacing } from "../../src/theme/tokens";
import { AppText } from "../../src/components/AppText";
import { BrandLockup } from "../../src/components/BrandLockup";
import { Button } from "../../src/components/Button";
import { Card } from "../../src/components/Card";
import { Icon } from "../../src/components/Icon";
import type { IconKey } from "../../src/ui/iconXml";
import { useOnboardingStore } from "../../src/stores/onboardingStore";

type DiscoverySlide = {
  key: string;
  icon: IconKey;
  tag: string;
  title: string;
  description: string;
  bullets: string[];
  disclaimer?: string;
};

const SLIDES: DiscoverySlide[] = [
  {
    key: "ecosystem",
    icon: "heart",
    tag: "زیست‌بوم مراقبت سالمند",
    title: "آرامش خاطر خانواده، کرامت عزیزانتان",
    description:
      "یارا پلی میان شما و عزیز سالخورده‌تان است؛ سامانه‌ای اختصاصی برای حفظ استقلال سالمند در منزل و همراهی مداوم خانواده از راه دور، بدون هیاهو و استرس.",
    bullets: [
      "مراقبت باوقار و همراهی بدون احساس نظارت تحمیلی",
      "کاهش اضطراب دوری برای همه اعضای خانواده",
      "دیده‌بانی پیوسته وضعیت روزمره با احترام کامل به حریم شخصی",
    ],
  },
  {
    key: "hub",
    icon: "hub",
    tag: "هاب رومیزی یارا",
    title: "هاب اختصاصی؛ همراه بدون پیچیدگی",
    description:
      "یک دستگاه رومیزی همیشه روشن و آرام در منزل سالمند. نیازی به کار با گوشی هوشمند یا منوهای پیچیده نیست؛ هاب یارا با هشدارهای دیداری و صوتی ملایم، وظایف روزانه را یادآوری می‌کند.",
    bullets: [
      "طراحی ویژه با نوشته‌های درشت و لمس بسیار ساده",
      "پایداری محلی: یادآوری‌ها بدون وابستگی به اینترنت فعال می‌مانند",
      "پل ارتباطی مستقیم و خودکار میان سالمند و اپلیکیشن خانواده",
    ],
  },
  {
    key: "medication",
    icon: "medication",
    tag: "نظم و روال مراقبت",
    title: "انضباط دارویی و روال‌های روزمره",
    description:
      "تنظیم برنامه داروها و یادآوری‌های روزانه توسط خانواده، اعلام دقیق و به‌موقع روی هاب رومیزی، و ثبت آرامش‌بخش وضعیت مصرف برای مراقبان.",
    bullets: [
      "پیشگیری از سردرگمی یا فراموشی دوزهای دارو",
      "ثبت شفاف و لحظه‌ای وضعیت برای مراقبان خانواده",
      "امکان تعریف یادآوری‌های اختصاصی و مراقبت‌های دوره‌ای",
    ],
  },
  {
    key: "connection",
    icon: "phone",
    tag: "ارتباط و آرامش",
    title: "همیشه نزدیک، با یک لمس ساده",
    description:
      "برقراری ارتباط آسان، ارسال پیام‌های صوتی و متنی و دریافت هشدارهای هوشمند در صورت نیاز به پیگیری. همه اعضای خانواده می‌توانند در حلقه مراقبت حضور داشته باشند.",
    bullets: [
      "ارتباط سریع و مستقیم با هاب رومیزی سالمند",
      "آگاهی از نیاز به پیگیری بدون ایجاد دلهره و نگرانی کاذب",
      "تقسیم وظایف مراقبت میان اعضای خانواده در برنامه‌ای هماهنگ",
    ],
    disclaimer: t.discoveryDisclaimer,
  },
];

export default function DiscoveryScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const [currentIndex, setCurrentIndex] = useState(0);

  const completeDiscovery = useOnboardingStore((state) => state.completeDiscovery);
  const skipDiscovery = useOnboardingStore((state) => state.skipDiscovery);

  const isLast = currentIndex === SLIDES.length - 1;
  const slide = SLIDES[currentIndex];

  async function handleSkip() {
    await skipDiscovery();
    router.replace("/(auth)/sign-in");
  }

  function handleNext() {
    if (currentIndex < SLIDES.length - 1) {
      const nextIndex = currentIndex + 1;
      setCurrentIndex(nextIndex);
      AccessibilityInfo.announceForAccessibility?.(`صفحه ${nextIndex + 1} از ${SLIDES.length}`);
    }
  }

  function handlePrev() {
    if (currentIndex > 0) {
      const prevIndex = currentIndex - 1;
      setCurrentIndex(prevIndex);
      AccessibilityInfo.announceForAccessibility?.(`صفحه ${prevIndex + 1} از ${SLIDES.length}`);
    }
  }

  async function handleLogin() {
    await completeDiscovery();
    router.replace("/(auth)/sign-in");
  }

  async function handleRegister() {
    await completeDiscovery();
    router.replace("/(auth)/register");
  }

  return (
    <SafeAreaView style={styles.safe} edges={["top", "bottom"]}>
      {/* Top Bar: Brand Lockup + Skip Button */}
      <View style={styles.header}>
        <BrandLockup size="sm" />
        {!isLast ? (
          <Pressable
            accessibilityRole="button"
            accessibilityLabel={t.discoverySkip}
            accessibilityHint="رد کردن بخش معرفی محصول و ورود مستقیم به صفحه ورود"
            onPress={() => void handleSkip()}
            hitSlop={12}
            style={({ pressed }) => [styles.skipButton, pressed && styles.pressed]}
          >
            <AppText variant="label" color={colors.textSecondary}>
              {t.discoverySkip}
            </AppText>
          </Pressable>
        ) : (
          <View style={styles.headerSpacer} />
        )}
      </View>

      {/* Progress Dots Indicator */}
      <View
        style={styles.indicatorContainer}
        accessibilityRole="progressbar"
        accessibilityLabel={`مرحله ${currentIndex + 1} از ${SLIDES.length}`}
        accessibilityValue={{ min: 1, max: SLIDES.length, now: currentIndex + 1 }}
      >
        {SLIDES.map((item, index) => {
          const isActive = index === currentIndex;
          return (
            <Pressable
              key={item.key}
              accessibilityRole="button"
              accessibilityLabel={`رفتن به صفحه ${index + 1}`}
              onPress={() => setCurrentIndex(index)}
              hitSlop={8}
              style={[
                styles.dot,
                isActive ? styles.dotActive : styles.dotInactive,
              ]}
            />
          );
        })}
      </View>

      {/* Scrollable Slide Content */}
      <ScrollView
        contentContainerStyle={[styles.scrollContent, { paddingBottom: insets.bottom + spacing.xl }]}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        <Card style={styles.slideCard}>
          {/* Hero Icon Badge */}
          <View style={styles.iconCircle}>
            <Icon name={slide.icon} color={colors.primary} width={32} height={32} />
          </View>

          {/* Category Tag */}
          <View style={styles.tagBadge}>
            <AppText variant="caption" color={colors.primary} align="center">
              {slide.tag}
            </AppText>
          </View>

          {/* Title & Description */}
          <AppText variant="headline" align="center" style={styles.title}>
            {slide.title}
          </AppText>

          <AppText variant="body" color={colors.textSecondary} align="center" style={styles.description}>
            {slide.description}
          </AppText>

          {/* Value Bullets */}
          <View style={styles.bulletList}>
            {slide.bullets.map((bullet, idx) => (
              <View key={idx} style={styles.bulletRow}>
                <View style={styles.bulletIconWrap}>
                  <Icon name="check" color={colors.success} width={14} height={14} />
                </View>
                <AppText variant="subtitle" color={colors.text} style={styles.bulletText}>
                  {bullet}
                </AppText>
              </View>
            ))}
          </View>

          {/* Medical Disclaimer on Final Slide */}
          {slide.disclaimer ? (
            <View style={styles.disclaimerBox}>
              <Icon name="info" color={colors.textMuted} width={18} height={18} />
              <AppText variant="caption" color={colors.textMuted} style={styles.disclaimerText}>
                {slide.disclaimer}
              </AppText>
            </View>
          ) : null}
        </Card>

        {/* Action Controls */}
        <View style={styles.actionContainer}>
          {!isLast ? (
            <View style={styles.navigationRow}>
              {currentIndex > 0 ? (
                <Button
                  label={t.discoveryPrev}
                  variant="ghost"
                  onPress={handlePrev}
                  style={styles.navButtonSecondary}
                />
              ) : (
                <View style={styles.navSpacer} />
              )}
              <Button
                label={t.discoveryNext}
                variant="primary"
                onPress={handleNext}
                style={styles.navButtonPrimary}
              />
            </View>
          ) : (
            <View style={styles.finalActions}>
              <Button
                label="مشاهده بسته‌ها و محصولات یارا"
                variant="primary"
                onPress={() => router.push("/(auth)/marketplace")}
              />
              <Button
                label={t.discoveryLogin}
                variant="secondary"
                onPress={() => void handleLogin()}
              />
              <Button
                label={t.discoveryRegister}
                variant="ghost"
                onPress={() => void handleRegister()}
              />
              <Button
                label={t.discoveryPrev}
                variant="ghost"
                onPress={handlePrev}
                style={styles.ghostBackButton}
              />
            </View>
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: colors.background,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: spacing.screen,
    paddingTop: spacing.md,
    paddingBottom: spacing.sm,
    minHeight: sizes.touch,
  },
  skipButton: {
    minHeight: sizes.touch,
    minWidth: sizes.touch,
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: spacing.sm,
  },
  headerSpacer: {
    width: sizes.touch,
    height: sizes.touch,
  },
  pressed: {
    opacity: 0.65,
  },
  indicatorContainer: {
    flexDirection: "row",
    justifyContent: "center",
    alignItems: "center",
    gap: spacing.sm,
    paddingVertical: spacing.sm,
  },
  dot: {
    height: 8,
    borderRadius: radius.pill,
  },
  dotActive: {
    width: 28,
    backgroundColor: colors.primary,
  },
  dotInactive: {
    width: 8,
    backgroundColor: colors.borderMuted,
  },
  scrollContent: {
    paddingHorizontal: spacing.screen,
    paddingTop: spacing.sm,
  },
  slideCard: {
    borderRadius: radius.xl,
    padding: spacing.lg,
    alignItems: "center",
    borderColor: colors.borderMuted,
    backgroundColor: colors.surface,
    ...elevation.card,
  },
  iconCircle: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: colors.surfaceMuted,
    justifyContent: "center",
    alignItems: "center",
    marginBottom: spacing.md,
  },
  tagBadge: {
    backgroundColor: colors.surfaceMuted,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
    borderRadius: radius.pill,
    marginBottom: spacing.sm,
  },
  title: {
    marginBottom: spacing.sm,
    lineHeight: 34,
  },
  description: {
    lineHeight: 24,
    marginBottom: spacing.lg,
  },
  bulletList: {
    width: "100%",
    gap: spacing.md,
    marginBottom: spacing.md,
  },
  bulletRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
  },
  bulletIconWrap: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: colors.successSoft,
    justifyContent: "center",
    alignItems: "center",
  },
  bulletText: {
    flex: 1,
    lineHeight: 22,
  },
  disclaimerBox: {
    width: "100%",
    flexDirection: "row",
    alignItems: "flex-start",
    backgroundColor: colors.surfaceMuted,
    padding: spacing.md,
    borderRadius: radius.md,
    marginTop: spacing.sm,
    gap: spacing.sm,
  },
  disclaimerText: {
    flex: 1,
    lineHeight: 18,
  },
  actionContainer: {
    marginTop: spacing.lg,
    width: "100%",
  },
  navigationRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: spacing.md,
  },
  navSpacer: {
    flex: 1,
  },
  navButtonSecondary: {
    flex: 1,
  },
  navButtonPrimary: {
    flex: 1,
  },
  finalActions: {
    gap: spacing.md,
    width: "100%",
  },
  ghostBackButton: {
    alignSelf: "center",
    marginTop: spacing.xs,
  },
});
