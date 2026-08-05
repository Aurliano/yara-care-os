# Hub DI Scope Decisions

Runtime Hardening documents every Hilt scope choice for the Android Hub.

## Singleton (`@Singleton`)

Long-lived infrastructure that must survive process lifetime and back shared runtime state:

| Binding | Module | Rationale |
|---|---|---|
| `HubRuntimeKernel` / `RuntimeKernel` | `runtime` | Single runtime coordinator |
| `HubRuntimeOrchestrator` | implicit via `@Singleton` class | Bootstraps kernel once per process |
| Runtime replica components | `RuntimeComponentModule` | Registered once with kernel |
| `ActionDispatcher`, `ActionRegistry` | `runtime` | Shared routing infrastructure |
| `SynchronizationClient` | `sync` | Holds active session state |
| All repositories | `data` | Room-backed, process-wide caches |
| `HubDatabase`, Retrofit, OkHttp, interceptors | `database`, `network` | Android platform singletons |
| `RuntimeScheduler` / `WorkManagerRuntimeScheduler` | `app` | Schedules process-wide background work |
| Replica identity / correlation providers | `data` | Shared request metadata |

## Unscoped (default / transient)

Stateless or short-lived orchestration that should not retain cycle-specific state:

| Binding | Module | Rationale |
|---|---|---|
| `RunIntegrationCycleUseCase` | `runtime` | One-shot worker/app invocation |
| `RecoverRuntimeUseCase` | `runtime` | One-shot recovery invocation |
| `ObserveHomeSnapshotUseCase` | `data` | Thin Flow wrapper |
| `ObserveReplicaStateUseCase` | `data` | Thin Flow wrapper |
| `ObserveHubIdentityUseCase` | `data` | Thin Flow wrapper |
| `StartSynchronizationUseCase` | `data` | Session delegated to singleton client |

## ViewModel / UI scope

ViewModels remain `@HiltViewModel` with no `@Singleton`. UI modules were not modified in this hardening pass.

## Notes

- Use cases depend on singleton repositories; unscoped use cases receive fresh instances per injection site while repositories stay shared.
- `:sync` now exposes `SyncModule` so the session client is explicitly bound.
- `:app` owns the only `WorkManager` dependency through `WorkManagerRuntimeScheduler`.
