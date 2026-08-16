import { Redirect, Stack } from "expo-router";
import { useSessionStore } from "../../src/stores/sessionStore";
import { useElderStore } from "../../src/stores/elderStore";

export default function AppLayout() {
  const user = useSessionStore((state) => state.user);
  const hydrating = useSessionStore((state) => state.hydrating);
  const elderId = useElderStore((state) => state.selectedElderId);

  if (!hydrating && !user) {
    return <Redirect href="/(auth)/sign-in" />;
  }
  if (!hydrating && user && !elderId) {
    return <Redirect href="/(auth)/select-elder" />;
  }

  return <Stack screenOptions={{ headerShown: false }} />;
}
