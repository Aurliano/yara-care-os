import { useState } from "react";
import { StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { AppText, Button, Card, Screen, TopAppBar } from "../../../src/components";
import { t } from "../../../src/i18n";
import { colors, spacing } from "../../../src/theme/tokens";
import { createInvitation } from "../../../src/api/endpoints/identity";
import { useElderStore } from "../../../src/stores/elderStore";
import { usePermissions } from "../../../src/permissions/usePermission";
import { PERMISSIONS } from "../../../src/permissions/codes";
import { PermissionDenied } from "../../../src/components/PermissionDenied";
import { toPersianDigits } from "../../../src/i18n/numerals";

export default function InviteScreen() {
  const router = useRouter();
  const elderId = useElderStore((s) => s.selectedElderId);
  const { can } = usePermissions();
  const [role, setRole] = useState("CAREGIVER");
  const [code, setCode] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (!can(PERMISSIONS.MANAGE_MEMBERS)) {
    return <PermissionDenied />;
  }

  async function onInvite() {
    if (!elderId) return;
    setLoading(true);
    setError(null);
    try {
      const expires = new Date();
      expires.setDate(expires.getDate() + 7);
      const invitation = await createInvitation(elderId, {
        role_code: role,
        expires_at: expires.toISOString(),
      });
      setCode(invitation.invite_code);
    } catch {
      setError(t.accessDenied);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Screen>
      <TopAppBar title={t.inviteMember} showBack showBell={false} />
      <Card>
        <View style={styles.form}>
          <AppText variant="caption">{t.roleCode}</AppText>
          {(["CAREGIVER", "VIEWER"] as const).map((item) => (
            <Button
              key={item}
              label={item === "CAREGIVER" ? t.roleCaregiver : t.roleViewer}
              variant={role === item ? "primary" : "secondary"}
              onPress={() => setRole(item)}
            />
          ))}
          {code ? (
            <AppText variant="title" align="center">
              {toPersianDigits(code)}
            </AppText>
          ) : null}
          {error ? (
            <AppText variant="caption" color={colors.error}>
              {error}
            </AppText>
          ) : null}
          <Button label={t.inviteMember} onPress={() => void onInvite()} loading={loading} />
          <Button label={t.notNow} variant="secondary" onPress={() => router.back()} />
        </View>
      </Card>
    </Screen>
  );
}

const styles = StyleSheet.create({
  form: { gap: spacing.md },
});
