package ir.sayda.yara.hub.data.usecase

import ir.sayda.yara.hub.core.domain.model.HomeRuntimeSnapshot
import ir.sayda.yara.hub.core.domain.model.HubIdentity
import ir.sayda.yara.hub.core.domain.model.ReplicaState
import ir.sayda.yara.hub.core.domain.repository.AuthRepository
import ir.sayda.yara.hub.core.domain.repository.ConnectivityRepository
import ir.sayda.yara.hub.core.domain.repository.HomeRepository
import ir.sayda.yara.hub.core.domain.repository.OutboxRepository
import ir.sayda.yara.hub.core.domain.repository.ReminderRepository
import ir.sayda.yara.hub.core.domain.repository.ReplicaMetadataRepository
import ir.sayda.yara.hub.core.domain.usecase.ObserveHomeSnapshotUseCase
import ir.sayda.yara.hub.core.domain.usecase.ObserveHubIdentityUseCase
import ir.sayda.yara.hub.core.domain.usecase.ObserveReminderPresentationUseCase
import ir.sayda.yara.hub.core.domain.usecase.ObserveReplicaStateUseCase
import ir.sayda.yara.hub.core.domain.usecase.RunSynchronizationCycleUseCase
import ir.sayda.yara.hub.core.domain.usecase.StartSynchronizationUseCase
import ir.sayda.yara.hub.core.result.AppResult
import ir.sayda.yara.hub.core.sync.OutboxOperationType
import ir.sayda.yara.hub.core.sync.SyncDirection
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject

class ObserveHomeSnapshotUseCaseImpl @Inject constructor(
    private val homeRepository: HomeRepository,
) : ObserveHomeSnapshotUseCase {
    override fun invoke(): Flow<HomeRuntimeSnapshot> = homeRepository.observeHomeSnapshot()
}

class ObserveReplicaStateUseCaseImpl @Inject constructor(
    private val replicaMetadataRepository: ReplicaMetadataRepository,
) : ObserveReplicaStateUseCase {
    override fun invoke(): Flow<ReplicaState?> = replicaMetadataRepository.observeReplicaState()
}

class ObserveHubIdentityUseCaseImpl @Inject constructor(
    private val authRepository: AuthRepository,
) : ObserveHubIdentityUseCase {
    override fun invoke(): Flow<HubIdentity?> = authRepository.observeIdentity()
}

class ObserveReminderPresentationUseCaseImpl @Inject constructor(
    private val reminderRepository: ReminderRepository,
) : ObserveReminderPresentationUseCase {
    override suspend fun invoke(executionId: String) = reminderRepository.loadPresentation(executionId)
}

class StartSynchronizationUseCaseImpl @Inject constructor(
    private val runSynchronizationCycleUseCase: RunSynchronizationCycleUseCase,
    private val outboxRepository: OutboxRepository,
    private val connectivityRepository: ConnectivityRepository,
) : StartSynchronizationUseCase {
    override suspend fun invoke(direction: SyncDirection, idempotencyKey: String): AppResult<Unit> {
        if (!connectivityRepository.isOnline()) {
            outboxRepository.enqueue(
                operationType = OutboxOperationType.SUBMIT_DELTA,
                payloadJson = """{"direction":"${direction.name}","idempotency_key":"$idempotencyKey"}""",
                idempotencyKey = idempotencyKey,
            )
            return AppResult.Success(Unit)
        }
        return when (val result = runSynchronizationCycleUseCase(idempotencyKey)) {
            is AppResult.Success -> AppResult.Success(Unit)
            is AppResult.Error -> result
        }
    }
}
