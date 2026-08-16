import { Tabs } from "expo-router";
import { BottomNav } from "../../../src/components/BottomNav";
import { colors } from "../../../src/theme/tokens";

export default function TabsLayout() {
  return (
    <Tabs
      tabBar={() => <BottomNav />}
      screenOptions={{
        headerShown: false,
        tabBarStyle: { backgroundColor: colors.background },
      }}
    />
  );
}
