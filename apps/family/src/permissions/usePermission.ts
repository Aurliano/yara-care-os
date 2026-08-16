import { useQuery } from "@tanstack/react-query";
import { getMyPermissions } from "../api/endpoints/identity";
import { queryKeys } from "../api/queryKeys";
import type { PermissionCode } from "../api/types";
import { useElderStore } from "../stores/elderStore";
import { hasPermission } from "./codes";

export function usePermissions() {
  const elderId = useElderStore((state) => state.selectedElderId);
  const query = useQuery({
    queryKey: elderId ? queryKeys.permissions(elderId) : ["permissions", "none"],
    queryFn: () => getMyPermissions(elderId as string),
    enabled: Boolean(elderId),
  });
  const granted = query.data?.permissions ?? [];
  return {
    ...query,
    granted,
    can: (code: PermissionCode) => hasPermission(granted, code),
  };
}
