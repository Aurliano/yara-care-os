# YARA Caregiver App (`apps/family`)

Expo React Native thin client for family caregivers.

## Stack

- Expo
- React Native
- TypeScript
- Zustand (session / selected elder / local alert ack)
- TanStack Query (server state)

## Scripts

```bash
pnpm --filter @yara/family typecheck
pnpm --filter @yara/family lint
pnpm --filter @yara/family test
pnpm --filter @yara/family start
```

Set `EXPO_PUBLIC_API_BASE_URL` to the Backend origin including `/api/v1`.

Persian RTL and Vazirmatn are enabled by default. Missing Backend read-models are listed in `BACKEND_GAPS.md`.
