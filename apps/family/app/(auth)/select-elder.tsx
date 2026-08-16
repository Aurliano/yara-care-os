import { Pressable, StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { t } from "../../src/i18n";
import { colors, spacing } from "../../src/theme/tokens";
import {
  AppText,
  Avatar,
  Card,
  EmptyState,
  ErrorState,
  LoadingSkeleton,
  Screen,
  TopAppBar,
} from "../../src/components";
import { images } from "../../src/components/Icon";
import { listElders } from "../../src/api/endpoints/identity";
import { queryKeys } from "../../src/api/queryKeys";
import { useElderStore } from "../../src/stores/elderStore";

export default function SelectElderScreen() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const selectElder = useElderStore((state) => state.selectElder);
  const query = useQuery({ queryKey: queryKeys.elders, queryFn: listElders });

  async function onSelect(elderId: string) {
    await selectElder(elderId);
    await queryClient.invalidateQueries({ queryKey: ["elder"] });
    router.replace("/(app)/(tabs)");
  }

  if (query.isPending) {
    return (
      <Screen>
        <LoadingSkeleton />
      </Screen>
    );
  }
  if (query.isError) {
    return (
      <Screen>
        <ErrorState onRetry={() => void query.refetch()} />
      </Screen>
    );
  }
  if (!query.data?.length) {
    return (
      <Screen>
        <TopAppBar showBell={false} />
        <EmptyState
          title={t.noElderTitle}
          body={t.noElderBody}
          image={images.noElder}
          actionLabel={t.setupElder}
          onAction={() => router.push("/(auth)/create-elder")}
          secondaryLabel={t.acceptInvite}
          onSecondary={() => router.push("/(auth)/accept-invitation")}
        />
      </Screen>
    );
  }

  return (
    <Screen>
      <TopAppBar title={t.selectElder} showBell={false} />
      <AppText variant="body" color={colors.textSecondary}>
        {t.selectElderHint}
      </AppText>
      <View style={styles.list}>
        {query.data.map((elder) => (
          <Pressable key={elder.id} onPress={() => void onSelect(elder.id)}>
            <Card>
              <View style={styles.row}>
                <View style={{ flex: 1 }}>
                  <AppText variant="title">{elder.full_name}</AppText>
                  <AppText variant="caption" color={colors.textSecondary}>
                    {elder.status === "ACTIVE" ? "فعال" : "غیرفعال"}
                  </AppText>
                </View>
                <Avatar name={elder.full_name} />
              </View>
            </Card>
          </Pressable>
        ))}
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  list: { gap: spacing.md, marginTop: spacing.lg },
  row: { flexDirection: "row", alignItems: "center", gap: spacing.md },
});
