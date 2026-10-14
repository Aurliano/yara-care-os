import React, { useEffect, useRef, useState } from "react";
import {
  Animated,
  Easing,
  Image,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { SvgXml } from "react-native-svg";
import { images } from "./Icon";
import { colors } from "../theme/tokens";

const PULSE_SVG_XML = `
<svg viewBox="0 0 74 36" fill="none">
  <defs>
    <linearGradient id="pulseGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#1E88E5" />
      <stop offset="45%" stop-color="#00897B" />
      <stop offset="100%" stop-color="#10B981" />
    </linearGradient>
  </defs>
  <path
    d="M 2 18 L 18 18 L 24 24 L 30 10 L 38 30 L 46 2 L 54 22 L 60 16 L 66 18 L 72 18"
    stroke="url(#pulseGrad)"
    stroke-width="3.4"
    stroke-linecap="round"
    stroke-linejoin="round"
  />
</svg>
`;

type Props = {
  hydratingSession?: boolean;
  elderHydrated?: boolean;
  onboardingHydrated?: boolean;
  onAnimationComplete?: () => void;
  minimumDurationMs?: number;
  testID?: string;
};

export function SplashScreenView({
  hydratingSession = false,
  elderHydrated = true,
  onboardingHydrated = true,
  onAnimationComplete,
  minimumDurationMs = 1500,
  testID = "sayda-splash-screen",
}: Props) {
  const [currentProgress, setCurrentProgress] = useState(15);
  const [statusMessage, setStatusMessage] = useState("در حال آماده‌سازی سامانه...");

  const hasAnimated = typeof Animated !== "undefined" && typeof Animated?.Value === "function";
  const progressAnim = useRef(hasAnimated ? new Animated.Value(15) : null).current;
  const heartbeatAnim = useRef(hasAnimated ? new Animated.Value(1) : null).current;
  const fadeAnim = useRef(hasAnimated ? new Animated.Value(1) : null).current;

  // Heartbeat pulse loop
  useEffect(() => {
    if (!hasAnimated || !heartbeatAnim) return;

    const pulse = Animated.loop(
      Animated.sequence([
        Animated.timing(heartbeatAnim, {
          toValue: 1.15,
          duration: 180,
          easing: Easing.out(Easing.quad),
          useNativeDriver: true,
        }),
        Animated.timing(heartbeatAnim, {
          toValue: 0.98,
          duration: 160,
          easing: Easing.in(Easing.quad),
          useNativeDriver: true,
        }),
        Animated.timing(heartbeatAnim, {
          toValue: 1.08,
          duration: 140,
          easing: Easing.out(Easing.quad),
          useNativeDriver: true,
        }),
        Animated.timing(heartbeatAnim, {
          toValue: 1.0,
          duration: 180,
          easing: Easing.in(Easing.quad),
          useNativeDriver: true,
        }),
        Animated.delay(650),
      ]),
    );

    pulse.start();
    return () => pulse.stop();
  }, [hasAnimated, heartbeatAnim]);

  // Compute target progress from real hydration milestones
  useEffect(() => {
    let target = 20;
    let msg = "در حال آماده‌سازی زیست‌بوم سایدا...";

    if (!hydratingSession) {
      target += 25;
      msg = "بررسی نشست کاربری...";
    }
    if (onboardingHydrated) {
      target += 25;
      msg = "آماده‌سازی تنظیمات...";
    }
    if (elderHydrated) {
      target += 30;
      msg = "بارگذاری همراهی سالمند...";
    }

    if (target >= 100) {
      target = 100;
      msg = "خوش آمدید";
    }

    setCurrentProgress(target);
    setStatusMessage(msg);

    if (hasAnimated && progressAnim) {
      Animated.timing(progressAnim, {
        toValue: target,
        duration: 350,
        easing: Easing.out(Easing.cubic),
        useNativeDriver: false,
      }).start();
    }
  }, [hydratingSession, elderHydrated, onboardingHydrated, hasAnimated, progressAnim]);

  // Transition out once ready and minimum time elapsed
  useEffect(() => {
    const isReady = !hydratingSession && elderHydrated && onboardingHydrated;
    if (!isReady) return;

    const timer = setTimeout(() => {
      if (hasAnimated && progressAnim && fadeAnim) {
        Animated.sequence([
          Animated.timing(progressAnim, {
            toValue: 100,
            duration: 250,
            easing: Easing.out(Easing.quad),
            useNativeDriver: false,
          }),
          Animated.delay(180),
          Animated.timing(fadeAnim, {
            toValue: 0,
            duration: 320,
            easing: Easing.out(Easing.quad),
            useNativeDriver: true,
          }),
        ]).start(() => {
          onAnimationComplete?.();
        });
      } else {
        setCurrentProgress(100);
        setStatusMessage("خوش آمدید");
        onAnimationComplete?.();
      }
    }, minimumDurationMs);

    return () => clearTimeout(timer);
  }, [hydratingSession, elderHydrated, onboardingHydrated, minimumDurationMs, onAnimationComplete, hasAnimated, progressAnim, fadeAnim]);

  const progressWidth =
    hasAnimated && progressAnim
      ? progressAnim.interpolate({
          inputRange: [0, 100],
          outputRange: ["0%", "100%"],
        })
      : `${currentProgress}%`;

  const ContainerView: any = hasAnimated && Animated?.View ? Animated.View : View;
  const PulseView: any = hasAnimated && Animated?.View ? Animated.View : View;
  const BarFillView: any = hasAnimated && Animated?.View ? Animated.View : View;

  return (
    <ContainerView
      testID={testID}
      accessibilityRole="progressbar"
      accessibilityLabel={`بارگذاری سایدا ${Math.round(currentProgress)} درصد`}
      accessibilityValue={{ min: 0, max: 100, now: Math.round(currentProgress) }}
      style={[
        styles.container,
        hasAnimated && fadeAnim ? { opacity: fadeAnim } : null,
      ]}
    >
      <Image
        source={images.splashBg}
        style={StyleSheet.absoluteFillObject}
        resizeMode="cover"
      />
      <View style={styles.bottomSection}>
        <View style={styles.loaderRow}>
          {/* Heartbeat ECG Pulse */}
          <PulseView
            testID="ecg-pulse-icon"
            style={[
              styles.pulseContainer,
              hasAnimated && heartbeatAnim
                ? { transform: [{ scale: heartbeatAnim }] }
                : null,
            ]}
          >
            <SvgXml xml={PULSE_SVG_XML} width={46} height={26} />
          </PulseView>

          {/* Dynamic Capsule Progress Bar */}
          <View style={styles.barTrack}>
            <BarFillView
              testID="splash-progress-fill"
              style={[
                styles.barFill,
                { width: progressWidth },
              ]}
            />
          </View>
        </View>

        {/* Subtitle from user's design */}
        <Text style={styles.ecosystemText}>Smart Care Ecosystem</Text>
        <Text style={styles.statusText}>{statusMessage}</Text>
      </View>
    </ContainerView>
  );
}

const styles = StyleSheet.create({
  container: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: "#F4F0E7",
    zIndex: 9999,
    justifyContent: "flex-end",
  },
  bottomSection: {
    width: "100%",
    alignItems: "center",
    paddingBottom: 48,
    paddingHorizontal: 24,
  },
  loaderRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 12,
    direction: "ltr",
  },
  pulseContainer: {
    alignItems: "center",
    justifyContent: "center",
  },
  barTrack: {
    width: 220,
    height: 18,
    borderRadius: 10,
    borderWidth: 1.6,
    borderColor: "#164E3D",
    backgroundColor: "rgba(235, 230, 218, 0.7)",
    overflow: "hidden",
    padding: 1.5,
    justifyContent: "center",
  },
  barFill: {
    height: "100%",
    borderRadius: 7,
    backgroundColor: "#0F766E",
  },
  ecosystemText: {
    marginTop: 14,
    fontSize: 13,
    letterSpacing: 0.6,
    color: "#1E3A34",
    fontFamily: "System",
    fontWeight: "500",
  },
  statusText: {
    marginTop: 4,
    fontSize: 11,
    color: colors.textMuted,
  },
});
