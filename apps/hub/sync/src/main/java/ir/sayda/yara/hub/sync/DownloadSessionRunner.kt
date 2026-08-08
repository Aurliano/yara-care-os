package ir.sayda.yara.hub.sync

import ir.sayda.yara.hub.core.domain.repository.SynchronizationRepository
import ir.sayda.yara.hub.core.result.AppResult
import ir.sayda.yara.hub.core.sync.ApplySummary
import ir.sayda.yara.hub.core.sync.SyncOperation
import ir.sayda.yara.hub.core.sync.SyncOperationType
import ir.sayda.yara.hub.core.sync.SyncSessionStatus
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class DownloadSessionRunner @Inject constructor(
    private val synchronizationRepository: SynchronizationRepository,
    private val replicaChangeApplier: ReplicaChangeApplier,
    private val checkpointCoordinator: CheckpointCoordinator,
    private val pendingEvidenceFinalizer: PendingEvidenceFinalizer,
    private val syncSessionStore: SyncSessionStore,
) {
    suspend fun downloadChanges(): AppResult<List<SyncOperation>> {
        val session = syncSessionStore.getCached()
            ?: return AppResult.Error(IllegalStateException("No active download session"))
        return synchronizationRepository.fetchPendingOperations(session.sessionId).map { operations ->
            operations.filter { it.operationType == SyncOperationType.DELTA }
        }
    }

    suspend fun downloadSnapshot(): AppResult<List<SyncOperation>> {
        val session = syncSessionStore.getCached()
            ?: return AppResult.Error(IllegalStateException("No active download session"))
        return synchronizationRepository.fetchPendingOperations(session.sessionId).map { operations ->
            operations.filter {
                it.operationType == SyncOperationType.SNAPSHOT || it.payloadType.endsWith(".snapshot")
            }
        }
    }

    suspend fun applyAndFinalize(operations: List<SyncOperation>): AppResult<ApplySummary> {
        val summary = replicaChangeApplier.apply(operations)
        pendingEvidenceFinalizer.finalizeConfirmedExecutions(summary.confirmedExecutionIds)
        return AppResult.Success(summary)
    }

    suspend fun advanceCheckpoint(token: String?): AppResult<Unit> =
        checkpointCoordinator.advanceFromRemote(token)

    suspend fun complete(): AppResult<Unit> {
        val session = syncSessionStore.getCached()
        if (session != null) {
            when (val result = synchronizationRepository.completeDownloadSession(session.sessionId)) {
                is AppResult.Error -> return result
                is AppResult.Success -> Unit
            }
        }
        syncSessionStore.completeAndRetain(SyncSessionStatus.SESSION_COMPLETED)
        return AppResult.Success(Unit)
    }
}

private inline fun <T> AppResult<T>.map(transform: (T) -> T): AppResult<T> = when (this) {
    is AppResult.Success -> AppResult.Success(transform(data))
    is AppResult.Error -> this
}
