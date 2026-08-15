package ir.sayda.yara.hub.sync



import ir.sayda.yara.hub.core.domain.repository.AuthRepository

import ir.sayda.yara.hub.core.domain.repository.ReplicaMetadataRepository

import ir.sayda.yara.hub.core.domain.repository.SynchronizationRepository

import ir.sayda.yara.hub.core.domain.repository.SyncSessionLocalRepository

import ir.sayda.yara.hub.core.provisioning.RuntimeProvisioningGate

import ir.sayda.yara.hub.core.result.AppResult

import ir.sayda.yara.hub.core.runtime.RuntimeRefreshPort

import ir.sayda.yara.hub.core.sync.ActiveSynchronizationSession

import ir.sayda.yara.hub.core.sync.ApplySummary

import ir.sayda.yara.hub.core.sync.SyncApplyTransaction
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

    private val replicaMetadataRepository: ReplicaMetadataRepository,

    private val syncSessionStore: SyncSessionStore,

    private val syncSessionLocalRepository: SyncSessionLocalRepository,

    private val uploadSessionRunner: UploadSessionRunner,

    private val downloadSessionRunner: DownloadSessionRunner,

    private val replicaChangeApplier: ReplicaChangeApplier,

    private val checkpointCoordinator: CheckpointCoordinator,

    private val runtimeRefreshPort: RuntimeRefreshPort,

    private val provisioningGate: RuntimeProvisioningGate,

    private val replicaStateInitializer: ReplicaStateInitializer,

    private val syncApplyTransaction: SyncApplyTransaction,

) : SynchronizationClient {



    override suspend fun beginDownloadSession(idempotencyKey: String): AppResult<ActiveSynchronizationSession> =

        beginSession(SyncDirection.DOWNLOAD, idempotencyKey)



    override suspend fun beginUploadSession(idempotencyKey: String): AppResult<ActiveSynchronizationSession> =

        beginSession(SyncDirection.UPLOAD, idempotencyKey)



    private suspend fun beginSession(

        direction: SyncDirection,

        idempotencyKey: String,

    ): AppResult<ActiveSynchronizationSession> {

        val refresh = authRepository.refreshTokenIfNeeded()
        when (refresh) {
            is AppResult.Error -> return refresh
            is AppResult.Success -> Unit
        }

        val startResult = synchronizationRepository.startSession(direction, idempotencyKey)

        return when (val result = startResult) {

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

        val gateReady = provisioningGate.requireRuntimeReady()

        if (!gateReady) {

            return AppResult.Success(emptySummary())

        }

        replicaStateInitializer.ensureInitialized()

        when (val refresh = authRepository.refreshTokenIfNeeded()) {
            is AppResult.Error -> return refresh.mapError()
            is AppResult.Success -> Unit
        }

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



        val localCheckpoint = replicaMetadataRepository.getReplicaState()?.checkpointSequence ?: 0L

        val isFirstSync = localCheckpoint == 0L



        val snapshots = if (isFirstSync) {

            when (val snaps = downloadSnapshot()) {

                is AppResult.Success -> snaps.data

                is AppResult.Error -> return snaps.mapError()

            }

        } else {

            emptyList()

        }



        val deltas = if (!isFirstSync) {

            when (val changes = downloadChanges()) {

                is AppResult.Success -> changes.data

                is AppResult.Error -> return changes.mapError()

            }

        } else {

            emptyList()

        }



        val operations = snapshots + deltas

        val token = syncSessionStore.getCached()?.synchronizationToken



        if (operations.isEmpty()) {

            when (val advanced = advanceCheckpoint(token)) {

                is AppResult.Error -> return advanced.mapError()

                is AppResult.Success -> Unit

            }

            replicaMetadataRepository.touchLastSuccessfulSync()

            when (val completed = downloadSessionRunner.complete()) {

                is AppResult.Error -> return completed.mapError()

                is AppResult.Success -> Unit

            }

            return AppResult.Success(emptySummary())

        }



        val summary = try {

            val nextCheckpoint = localCheckpoint + 1

            syncApplyTransaction.withReplicaMutation(nextCheckpoint, token) {

                when (val applied = downloadSessionRunner.applyAndFinalize(operations)) {

                    is AppResult.Success -> applied.data

                    is AppResult.Error -> throw applied.exception

                }

            }

        } catch (exception: Exception) {

            return AppResult.Error(exception)

        }



        when (val completed = downloadSessionRunner.complete()) {

            is AppResult.Error -> return completed.mapError()

            is AppResult.Success -> Unit

        }

        when (val advanced = advanceCheckpoint(token)) {

            is AppResult.Error -> return advanced.mapError()

            is AppResult.Success -> Unit

        }

        markReplicaHealthyIfNeeded(summary.appliedCount)

        val refreshScope = if (snapshots.isNotEmpty()) {

            SyncRefreshScope.full()

        } else {

            SyncRefreshScope.fromDomains(summary.affectedReplicaDomains)

        }

        if (!refreshScope.isEmpty) {

            runtimeRefreshPort.refreshAfterSync(refreshScope)

        }



        return AppResult.Success(summary)

    }



    private fun emptySummary() = ApplySummary(

        appliedCount = 0,

        skippedCount = 0,

        conflictCount = 0,

        affectedReplicaDomains = emptySet(),

    )

    private suspend fun markReplicaHealthyIfNeeded(appliedCount: Int) {
        if (appliedCount <= 0) return
        val current = replicaMetadataRepository.getReplicaState() ?: return
        if (current.health.equals("HEALTHY", ignoreCase = true)) return
        replicaMetadataRepository.upsertReplicaState(current.copy(health = "HEALTHY"))
    }

    private fun <T> AppResult<T>.mapError(): AppResult<ApplySummary> =

        AppResult.Error((this as AppResult.Error).exception)

}

