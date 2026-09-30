import { useEffect } from "react";
import { Redirect } from "expo-router";
import { useSessionStore } from "../src/stores/sessionStore";
import { useElderStore } from "../src/stores/elderStore";
import { useAlertAckStore } from "../src/stores/alertAckStore";
import { useOnboardingStore } from "../src/stores/onboardingStore";
import { LoadingSkeleton } from "../src/components";
import { Screen } from "../src/components/Screen";

export default function Index() {
  const hydrateSession = useSessionStore((state) => state.hydrate);
  const hydrating = useSessionStore((state) => state.hydrating);
  const user = useSessionStore((state) => state.user);
  const hydrateElder = useElderStore((state) => state.hydrate);
  const elderHydrated = useElderStore((state) => state.hydrated);
  const selectedElderId = useElderStore((state) => state.selectedElderId);
  const hydrateAcks = useAlertAckStore((state) => state.hydrate);
  const hydrateOnboarding = useOnboardingStore((state) => state.hydrate);
  const onboardingHydrated = useOnboardingStore((state) => state.hydrated);
  const discoveryStatus = useOnboardingStore((state) => state.status);

  useEffect(() => {
    void hydrateSession();
    void hydrateElder();
    void hydrateAcks();
    void hydrateOnboarding();
  }, [hydrateSession, hydrateElder, hydrateAcks, hydrateOnboarding]);

  if (hydrating || !elderHydrated || !onboardingHydrated) {
    return (
      <Screen>
        <LoadingSkeleton />
      </Screen>
    );
  }

  if (user) {
    if (!selectedElderId) {
      return <Redirect href="/(auth)/select-elder" />;
    }
    return <Redirect href="/(app)/(tabs)" />;
  }

  if (discoveryStatus === "not_started") {
    return <Redirect href="/(auth)/discovery" />;
  }

  return <Redirect href="/(auth)/sign-in" />;
}
