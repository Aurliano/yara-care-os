import React, { useEffect, useRef, useState } from "react";
import {
  Animated,
  Dimensions,
  Easing,
  Image,
  StyleSheet,
  Text,
  useWindowDimensions,
  View,
} from "react-native";
import { images } from "./Icon";
import { colors } from "../theme/tokens";

type Props = {
  hydratingSession?: boolean;
  elderHydrated?: boolean;
  onboardingHydrated?: boolean;
  onAnimationComplete?: () => void;
  minimumDurationMs?: number;
  testID?: string;
};

// Dimensions of the high-res artwork (sayda-splash-empty-track.png)
const ARTWORK_WIDTH = 1536;
const ARTWORK_HEIGHT = 2752;
const ARTWORK_ASPECT = ARTWORK_WIDTH / ARTWORK_HEIGHT;

// Mathematical ratios of the capsule progress bar inside the artwork
const TRACK_LEFT_RATIO = 576 / ARTWORK_WIDTH;
const TRACK_TOP_RATIO = 2478 / ARTWORK_HEIGHT;
const TRACK_WIDTH_RATIO = 612 / ARTWORK_WIDTH;
const TRACK_HEIGHT_RATIO = 38 / ARTWORK_HEIGHT;

// Ratios for the ECG pulse section
const PULSE_LEFT_RATIO = 343 / ARTWORK_WIDTH;
const PULSE_TOP_RATIO = 2415 / ARTWORK_HEIGHT;
const PULSE_WIDTH_RATIO = 207 / ARTWORK_WIDTH;
const PULSE_HEIGHT_RATIO = 150 / ARTWORK_HEIGHT;

function useSafeDimensions() {
  try {
    if (typeof useWindowDimensions === "function") {
      const dims = useWindowDimensions();
      if (dims?.width && dims?.height) {
        return dims;
      }
    }
  } catch {
    // ignore
  }
  try {
    if (typeof Dimensions !== "undefined" && typeof Dimensions.get === "function") {
      const dims = Dimensions.get("window");
      if (dims?.width && dims?.height) {
        return dims;
      }
    }
  } catch {
    // ignore
  }
  return { width: 390, height: 844 };
}

export function SplashScreenView({
  hydratingSession = false,
  elderHydrated = true,
  onboardingHydrated = true,
  onAnimationComplete,
  minimumDurationMs = 1500,
  testID = "sayda-splash-screen",
}: Props) {
  const { width: windowWidth, height: windowHeight } = useSafeDimensions();

  // Compute exact rendered dimensions that fit the screen without any cropping
  let renderW = windowWidth;
  let renderH = windowWidth / ARTWORK_ASPECT;
  if (renderH > windowHeight) {
    renderH = windowHeight;
    renderW = windowHeight * ARTWORK_ASPECT;
  }

  const [currentProgress, setCurrentProgress] = useState(20);
  const [statusMessage, setStatusMessage] = useState("در حال آماده‌سازی سامانه...");

  const hasAnimated = typeof Animated !== "undefined" && typeof Animated?.Value === "function";
  const progressAnim = useRef(hasAnimated ? new Animated.Value(20) : null).current;
  const heartbeatAnim = useRef(hasAnimated ? new Animated.Value(1) : null).current;
  const fadeAnim = useRef(hasAnimated ? new Animated.Value(1) : null).current;

  // Gentle heartbeat pulse on the ECG area
  useEffect(() => {
    if (!hasAnimated || !heartbeatAnim) return;

    const pulse = Animated.loop(
      Animated.sequence([
        Animated.timing(heartbeatAnim, {
          toValue: 1.12,
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
          toValue: 1.06,
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
        Animated.delay(700),
      ]),
    );

    pulse.start();
    return () => pulse.stop();
  }, [hasAnimated, heartbeatAnim]);

  // Compute target progress from real hydration milestones
  useEffect(() => {
    let target = 25;
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
      target += 25;
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

  // Transition out once ready and minimum time elapsed - guaranteeing 100% full green progress bar
  useEffect(() => {
    const isReady = !hydratingSession && elderHydrated && onboardingHydrated;
    if (!isReady) return;

    const timer = setTimeout(() => {
      if (hasAnimated && progressAnim && fadeAnim) {
        Animated.sequence([
          // Guarantee progress bar visibly fills to 100%
          Animated.timing(progressAnim, {
            toValue: 100,
            duration: 300,
            easing: Easing.out(Easing.quad),
            useNativeDriver: false,
          }),
          // Hold full green bar visibly for 250ms
          Animated.delay(250),
          // Smooth fade-out transition into the app
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
  const BarFillView: any = hasAnimated && Animated?.View ? Animated.View : View;
  const PulseView: any = hasAnimated && Animated?.View ? Animated.View : View;

  const trackLeft = renderW * TRACK_LEFT_RATIO;
  const trackTop = renderH * TRACK_TOP_RATIO;
  const trackWidth = renderW * TRACK_WIDTH_RATIO;
  const trackHeight = renderH * TRACK_HEIGHT_RATIO;
  const trackRadius = trackHeight / 2;

  const pulseLeft = renderW * PULSE_LEFT_RATIO;
  const pulseTop = renderH * PULSE_TOP_RATIO;
  const pulseWidth = renderW * PULSE_WIDTH_RATIO;
  const pulseHeight = renderH * PULSE_HEIGHT_RATIO;

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
      {/* Centered responsive container strictly bounded by the artwork's aspect ratio */}
      <View
        style={[
          styles.canvas,
          {
            width: renderW,
            height: renderH,
          },
        ]}
      >
        {/* Full uncropped high-resolution background artwork */}
        <Image
          source={images.splashEmptyTrack}
          style={styles.image}
          resizeMode="contain"
          fadeDuration={0}
        />

        {/* ECG Pulse test target and subtle pulse accent */}
        <PulseView
          testID="ecg-pulse-icon"
          style={[
            styles.pulseAnchor,
            {
              left: pulseLeft,
              top: pulseTop,
              width: pulseWidth,
              height: pulseHeight,
            },
            hasAnimated && heartbeatAnim
              ? { transform: [{ scale: heartbeatAnim }] }
              : null,
          ]}
        />

        {/* Animated Capsule Progress Bar Track - fits with sub-pixel precision */}
        <View
          style={[
            styles.trackContainer,
            {
              left: trackLeft,
              top: trackTop,
              width: trackWidth,
              height: trackHeight,
              borderRadius: trackRadius,
            },
          ]}
        >
          <BarFillView
            testID="splash-progress-fill"
            style={[
              styles.trackFill,
              {
                width: progressWidth,
                borderRadius: trackRadius,
              },
            ]}
          />
        </View>

        {/* Status indicator rendered below Smart Care Ecosystem on the warm desk surface */}
        <View
          style={[
            styles.statusWrapper,
            {
              top: trackTop + trackHeight + Math.max(28, renderH * 0.045),
            },
          ]}
        >
          <Text style={styles.statusText}>{statusMessage}</Text>
        </View>

        {/* Accessible screen-reader & test text anchors matching artwork typography */}
        <Text style={styles.srOnly}>Smart Care Ecosystem</Text>
      </View>
    </ContainerView>
  );
}

const styles = StyleSheet.create({
  container: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: "#F4F0E7",
    zIndex: 9999,
    justifyContent: "center",
    alignItems: "center",
  },
  canvas: {
    position: "relative",
    direction: "ltr",
    justifyContent: "center",
    alignItems: "center",
    overflow: "hidden",
  },
  image: {
    width: "100%",
    height: "100%",
  },
  pulseAnchor: {
    position: "absolute",
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "transparent",
  },
  trackContainer: {
    position: "absolute",
    backgroundColor: "#F1D7BE",
    overflow: "hidden",
    direction: "ltr",
    alignItems: "flex-start",
    justifyContent: "center",
  },
  trackFill: {
    height: "100%",
    backgroundColor: colors.primary, // #00685F SAYDA Brand Teal
  },
  statusWrapper: {
    position: "absolute",
    width: "100%",
    alignItems: "center",
    justifyContent: "center",
    direction: "rtl",
  },
  statusText: {
    fontSize: 12,
    fontFamily: "System",
    color: "#2C534A",
    fontWeight: "500",
    letterSpacing: 0.2,
  },
  srOnly: {
    position: "absolute",
    opacity: 0,
    width: 1,
    height: 1,
    overflow: "hidden",
  },
});
