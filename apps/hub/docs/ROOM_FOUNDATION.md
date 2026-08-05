# Hub Room Foundation Review

Runtime Hardening review of the Hub local database foundation.

## Current configuration

| Item | Status |
|---|---|
| `exportSchema = true` | Enabled |
| Schema output | `database/schemas/ir.sayda.yara.hub.database.HubDatabase/` |
| KSP `room.schemaLocation` | Configured in `database/build.gradle.kts` |
| Current version | **2** |
| Entities | 15 replica / infrastructure tables (unchanged count) |

## Version 2 changes (Runtime Hardening)

Metadata-only migration `MIGRATION_1_2`:

- **outbox_entry**: `priority`, `updated_at_epoch_millis`, `last_error`
- **pending_evidence**: `correlation_id`, `idempotency_key`, `retry_count`, `updated_at_epoch_millis`, `last_error`

No business semantics changed. Retry execution remains deferred.

## Migration strategy

1. **Production path**: `addMigrations(MIGRATION_1_2)` preserves existing installs.
2. **Development fallback**: `fallbackToDestructiveMigration()` remains for schema drift during MVP.
3. **AutoMigration**: Not enabled yet. Schema JSON is exported so AutoMigration can be evaluated when entity changes stabilize.

## Future readiness

- Export schema JSON for every version bump before release.
- Prefer explicit `Migration` objects over destructive fallback once field devices exist.
- Keep infrastructure tables (`outbox_entry`, `pending_evidence`, `runtime_state`) isolated from replica domain tables to simplify incremental migrations.
- DAO ordering contracts for outbox priority are covered by `OutboxOrderingContractTest` (pure JVM, no Robolectric).

## Known limitation

Robolectric-based DAO tests were removed because `:database:testDebugUnitTest` hung repeatedly on Windows. Instrumented DAO tests can be added later without blocking Runtime Hardening verification.
