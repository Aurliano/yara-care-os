package ir.sayda.yara.hub.sync

import ir.sayda.yara.hub.core.domain.repository.AuthRepository
import ir.sayda.yara.hub.core.domain.repository.SynchronizationRepository
import ir.sayda.yara.hub.core.domain.repository.SyncSessionLocalRepository
import ir.sayda.yara.hub.core.result.AppResult
import ir.sayda.yara.hub.core.runtime.RuntimeRefreshPort
import ir.sayda.yara.hub.core.sync.ActiveSynchronizationSession
import ir.sayda.yara.hub.core.sync.ApplySummary
import ir.sayda.yara.hub.core.sync.SyncDirection
import ir.sayda.yara.hub.core.sync.SyncOperation
import ir.sayda.yara.hub.core.sync.SyncRefreshScope
import ir.sayda.yara.hub.core.sync.SyncSessionStatus
import ir.sayda.yara.hub.core.sync.SynchronizationClient
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class SynchronizationClientImpl @Inject constructor(
    private val synchronizationRepository: SynchronizationRepository,
    private val authRepository: AuthRepository,
    private val syncSessionStore: SyncSessionStore,
    private val syncSessionLocalRepository: SyncSessionLocalRepository,
    private val uploadSessionRunner: UploadSessionRunner,
    private val downloadSessionRunner: DownloadSessionRunner,
    private val replicaChangeApplier: ReplicaChangeApplier,
    private val checkpointCoordinator: CheckpointCoordinator,
    private val runtimeRefreshPort: RuntimeRefreshPort,
) : SynchronizationClient {

    override suspend fun beginDownloadSession(idempotencyKey: String): AppResult<ActiveSynchronizationSession> =
        beginSession(SyncDirection.DOWNLOAD, idempotencyKey)

    override suspend fun beginUploadSession(idempotencyKey: String): AppResult<ActiveSynchronizationSession> =
        beginSession(SyncDirection.UPLOAD, idempotencyKey)

    private suspend fun beginSession(
        direction: SyncDirection,
        idempotencyKey: String,
    ): AppResult<ActiveSynchronizationSession> {
        authRepository.refreshTokenIfNeeded()
        return when (val result = synchronizationRepository.startSession(direction, idempotencyKey)) {
            is AppResult.Success -> {
                val active = ActiveSynchronizationSession(
                    sessionId = result.data.sessionId,
                    direction = direction,
                    status = SyncSessionStatus.SESSION_STARTED,
                    synchronizationToken = result.data.synchronizationToken,
                )
                syncSessionStore.persist(result.data, SyncSessionStatus.SESSION_STARTED)
                AppResult.Success(active)
            }
            is AppResult.Error -> result
        }
    }

    override suspend fun downloadChanges(): AppResult<List<SyncOperation>> =
        downloadSessionRunner.downloadChanges()

    override suspend fun downloadSnapshot(): AppResult<List<SyncOperation>> =
        downloadSessionRunner.downloadSnapshot()

    override suspend fun applyChanges(operations: List<SyncOperation>): AppResult<ApplySummary> =
        replicaChangeApplier.apply(operations).let { AppResult.Success(it) }

    override suspend fun advanceCheckpoint(token: String?): AppResult<Unit> =
        checkpointCoordinator.advanceFromRemote(token)

    override suspend fun uploadPendingEvidence(limit: Int): AppResult<Int> =
        uploadSessionRunner.uploadPendingEvidence(limit)

    override suspend fun uploadOutbox(limit: Int): AppResult<Int> =
        uploadSessionRunner.uploadOutbox(limit)

    override suspend fun resume(): AppResult<ActiveSynchronizationSession> {
        val cached = syncSessionStore.restoreActive()
            ?: syncSessionLocalRepository.getActive()?.let {
                syncSessionStore.restoreActive()
            }
        if (cached != null) return AppResult.Success(cached)

        val persisted = syncSessionLocalRepository.getActive()
            ?: return AppResult.Error(IllegalStateException("No session to resume"))
        return when (val result = synchronizationRepository.resumeSession(persisted.sessionId)) {
            is AppResult.Success -> {
                syncSessionStore.persist(result.data, SyncSessionStatus.SESSION_STARTED)
                AppResult.Success(
                    ActiveSynchronizationSession(
                        sessionId = result.data.sessionId,
                        direction = SyncDirection.valueOf(result.data.direction),
                        status = SyncSessionStatus.SESSION_STARTED,
                        synchronizationToken = result.data.synchronizationToken,
                    ),
                )
            }
            is AppResult.Error -> result
        }
    }

    override suspend fun cancel(): AppResult<Unit> {
        val sessionId = syncSessionStore.getCached()?.sessionId
            ?: syncSessionLocalRepository.getActive()?.sessionId
        if (sessionId != null) {
            synchronizationRepository.cancelSession(sessionId)
        }
        syncSessionStore.clear()
        return AppResult.Success(Unit)
    }

    override suspend fun complete(): AppResult<Unit> {
        val session = syncSessionStore.getCached()
        return if (session?.direction == SyncDirection.UPLOAD) {
            uploadSessionRunner.complete()
        } else {
            downloadSessionRunner.complete()
        }
    }

    override suspend fun runSynchronizationCycle(idempotencyKey: String): AppResult<ApplySummary> {
        authRepository.refreshTokenIfNeeded()

        when (val uploadBegin = beginUploadSession(idempotencyKey)) {
            is AppResult.Error -> return uploadBegin.mapError()
            is AppResult.Success -> Unit
        }
        uploadPendingEvidence()
        uploadOutbox()
        complete()

        when (val downloadBegin = beginDownloadSession("$idempotencyKey:download")) {
            is AppResult.Error -> return downloadBegin.mapError()
            is AppResult.Success -> Unit
        }

        val deltas = when (val changes = downloadChanges()) {
            is AppResult.Success -> changes.data
            is AppResult.Error -> return changes.mapError()
        }
        val snapshots = when (val snaps = downloadSnapshot()) {
            is AppResult.Success -> snaps.data
            is AppResult.Error -> return snaps.mapError()
        }
        val operations = deltas + snapshots
        val summary = when (val applied = downloadSessionRunner.applyAndFinalize(operations)) {
            is AppResult.Success -> applied.data
            is AppResult.Error -> return applied.mapError()
        }

        val token = syncSessionStore.getCached()?.synchronizationToken
        advanceCheckpoint(token)
        complete()

        if (summary.hasAppliedChanges) {
            runtimeRefreshPort.refreshAfterSync(SyncRefreshScope.fromDomains(summary.affectedReplicaDomains))
        }

        return AppResult.Success(summary)
    }

    private fun <T> AppResult<T>.mapError(): AppResult<ApplySummary> =
        AppResult.Error((this as AppResult.Error).exception)
}
