import { type ReactNode } from "react";
import type { PermissionCode } from "../api/types";
import { PermissionDenied } from "../components/PermissionDenied";
import { usePermissions } from "./usePermission";

type Props = {
  permission: PermissionCode;
  children: ReactNode;
  fallback?: ReactNode;
};

export function PermissionGuard({ permission, children, fallback }: Props) {
  const { can, isPending } = usePermissions();
  if (isPending) {
    return null;
  }
  if (!can(permission)) {
    return fallback ?? <PermissionDenied />;
  }
  return children;
}
