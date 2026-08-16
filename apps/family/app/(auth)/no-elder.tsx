import { Redirect } from "expo-router";

export default function NoElderScreen() {
  return <Redirect href="/(auth)/select-elder" />;
}
