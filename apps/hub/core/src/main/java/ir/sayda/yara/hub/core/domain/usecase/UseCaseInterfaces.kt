package ir.sayda.yara.hub.core.domain.usecase

import ir.sayda.yara.hub.core.domain.model.HomeRuntimeSnapshot
import ir.sayda.yara.hub.core.domain.model.HubIdentity
import ir.sayda.yara.hub.core.domain.model.ReminderPresentation
import ir.sayda.yara.hub.core.domain.model.ReplicaState
import ir.sayda.yara.hub.core.result.AppResult
import ir.sayda.yara.hub.core.sync.SyncDirection
import kotlinx.coroutines.flow.Flow

interface ObserveHomeSnapshotUseCase {
    operator fun invoke(): Flow<HomeRuntimeSnapshot>
}

interface ObserveReplicaStateUseCase {
    operator fun invoke(): Flow<ReplicaState?>
}

interface ObserveHubIdentityUseCase {
    operator fun invoke(): Flow<HubIdentity?>
}

interface RunIntegrationCycleUseCase {
    suspend operator fun invoke(): AppResult<Map<String, Int>>
}

interface RunSynchronizationCycleUseCase {
    suspend operator fun invoke(idempotencyKey: String): AppResult<ir.sayda.yara.hub.core.sync.ApplySummary>
}

interface StartSynchronizationUseCase {
    suspend operator fun invoke(direction: SyncDirection, idempotencyKey: String): AppResult<Unit>
}

interface RecoverRuntimeUseCase {
    suspend operator fun invoke(): AppResult<Unit>
}

interface ConfirmReminderUseCase {
    suspend operator fun invoke(executionId: String, interactionReference: String): AppResult<String>
}

interface ObserveReminderPresentationUseCase {
    suspend operator fun invoke(executionId: String): ReminderPresentation?
}
