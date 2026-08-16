import { useEffect } from "react";
import { Redirect } from "expo-router";
import { useSessionStore } from "../src/stores/sessionStore";
import { useElderStore } from "../src/stores/elderStore";
import { useAlertAckStore } from "../src/stores/alertAckStore";
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

  useEffect(() => {
    void hydrateSession();
    void hydrateElder();
    void hydrateAcks();
  }, [hydrateSession, hydrateElder, hydrateAcks]);

  if (hydrating || !elderHydrated) {
    return (
      <Screen>
        <LoadingSkeleton />
      </Screen>
    );
  }

  if (!user) {
    return <Redirect href="/(auth)/sign-in" />;
  }
  if (!selectedElderId) {
    return <Redirect href="/(auth)/select-elder" />;
  }
  return <Redirect href="/(app)/(tabs)" />;
}
