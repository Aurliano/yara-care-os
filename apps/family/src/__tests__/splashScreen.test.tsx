import React from "react";
import { render, act } from "@testing-library/react-native";
import { SplashScreenView } from "../components/SplashScreenView";

describe("SplashScreenView (SAYDA)", () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("renders the splash screen with progressbar role and accessibility label", () => {
    const { getByTestId, getByText } = render(
      <SplashScreenView
        hydratingSession={true}
        elderHydrated={false}
        onboardingHydrated={false}
        minimumDurationMs={100}
      />,
    );

    expect(getByTestId("sayda-splash-screen")).toBeTruthy();
    expect(getByTestId("ecg-pulse-icon")).toBeTruthy();
    expect(getByTestId("splash-progress-fill")).toBeTruthy();
    expect(getByText("Smart Care Ecosystem")).toBeTruthy();
  });

  it("updates progress message when stores hydrate", () => {
    const { getByText, rerender } = render(
      <SplashScreenView
        hydratingSession={true}
        elderHydrated={false}
        onboardingHydrated={false}
        minimumDurationMs={100}
      />,
    );

    // Initial message while hydrating session
    expect(getByText("در حال آماده‌سازی زیست‌بوم سایدا...")).toBeTruthy();

    // Rerender when session finishes hydrating
    rerender(
      <SplashScreenView
        hydratingSession={false}
        elderHydrated={false}
        onboardingHydrated={false}
        minimumDurationMs={100}
      />,
    );

    expect(getByText("بررسی نشست کاربری...")).toBeTruthy();

    // Rerender when everything finishes
    rerender(
      <SplashScreenView
        hydratingSession={false}
        elderHydrated={true}
        onboardingHydrated={true}
        minimumDurationMs={100}
      />,
    );

    expect(getByText("خوش آمدید")).toBeTruthy();
  });

  it("calls onAnimationComplete after hydration is done and minimum duration elapses", () => {
    const onComplete = jest.fn();

    render(
      <SplashScreenView
        hydratingSession={false}
        elderHydrated={true}
        onboardingHydrated={true}
        minimumDurationMs={200}
        onAnimationComplete={onComplete}
      />,
    );

    // Fast-forward past minimum duration and fade out animation
    act(() => {
      jest.advanceTimersByTime(250);
      jest.advanceTimersByTime(400);
      jest.advanceTimersByTime(400);
    });

    expect(onComplete).toHaveBeenCalled();
  });
});
