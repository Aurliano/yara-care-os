package ir.sayda.yara.hub.data.repository

import ir.sayda.yara.hub.core.domain.model.OutboxEntry
import ir.sayda.yara.hub.core.domain.model.PendingEvidence
import ir.sayda.yara.hub.core.domain.model.ReplicaState
import ir.sayda.yara.hub.core.domain.model.RuntimeStateRecord
import ir.sayda.yara.hub.core.domain.model.SyncSession
import ir.sayda.yara.hub.core.domain.repository.OutboxRepository
import ir.sayda.yara.hub.core.domain.repository.PendingEvidenceRepository
import ir.sayda.yara.hub.core.domain.repository.ReplicaMetadataRepository
import ir.sayda.yara.hub.core.domain.repository.RuntimeStateRepository
import ir.sayda.yara.hub.core.domain.repository.SynchronizationRepository
import ir.sayda.yara.hub.core.domain.repository.IntegrationRuntimeRepository
import ir.sayda.yara.hub.core.result.AppResult
import ir.sayda.yara.hub.core.sync.OutboxEntryStatus
import ir.sayda.yara.hub.core.sync.OutboxOperationType
import ir.sayda.yara.hub.core.sync.PendingEvidenceStatus
import ir.sayda.yara.hub.core.sync.SyncDirection
import ir.sayda.yara.hub.database.HubDatabase
import ir.sayda.yara.hub.core.runtime.RUNTIME_KERNEL_COMPONENT_ID
import ir.sayda.yara.hub.database.mapper.toDomain
import ir.sayda.yara.hub.database.mapper.toEntity
import ir.sayda.yara.hub.core.domain.repository.ReplicaCheckpoint
import ir.sayda.yara.hub.core.sync.SyncOperation
import ir.sayda.yara.hub.core.sync.SyncOperationType
import ir.sayda.yara.hub.network.api.HubIntegrationApi
import ir.sayda.yara.hub.network.api.SynchronizationDomainApi
import ir.sayda.yara.hub.network.dto.HubConfirmationRequestDto
import ir.sayda.yara.hub.network.dto.HubSyncPayloadRequestDto
import ir.sayda.yara.hub.network.dto.HubSyncStartRequestDto
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ReplicaMetadataRepositoryImpl @Inject constructor(
    database: HubDatabase,
) : ReplicaMetadataRepository {
    private val dao = database.replicaStateDao()

    override suspend fun getReplicaState(): ReplicaState? = dao.get()?.toDomain()

    override suspend fun upsertReplicaState(state: ReplicaState) {
        dao.upsert(state.toEntity())
    }

    override suspend fun advanceCheckpoint(sequence: Long, token: String?) {
        val current = dao.get() ?: return
        if (sequence <= current.checkpointSequence) return
        dao.upsert(
            current.copy(
                checkpointSequence = sequence,
                checkpointToken = token,
                lastSuccessfulSyncEpochMillis = System.currentTimeMillis(),
            ),
        )
    }

    override suspend fun touchLastSuccessfulSync() {
        val current = dao.get() ?: return
        dao.upsert(
            current.copy(
                lastSuccessfulSyncEpochMillis = System.currentTimeMillis(),
            ),
        )
    }

    override fun observeReplicaState(): Flow<ReplicaState?> =
        dao.observe().map { it?.toDomain() }
}

@Singleton
class OutboxRepositoryImpl @Inject constructor(
    database: HubDatabase,
) : OutboxRepository {
    private val dao = database.outboxDao()

    override suspend fun enqueue(
        operationType: OutboxOperationType,
        payloadJson: String,
        idempotencyKey: String,
        priority: Int,
    ): OutboxEntry {
        val now = System.currentTimeMillis()
        val entry = OutboxEntry(
            id = UUID.randomUUID().toString(),
            operationType = operationType.name,
            payloadJson = payloadJson,
            idempotencyKey = idempotencyKey,
            status = OutboxEntryStatus.PENDING.name,
            retryCount = 0,
            priority = priority,
            createdAtEpochMillis = now,
            updatedAtEpochMillis = now,
            lastAttemptAtEpochMillis = null,
            lastError = null,
        )
        dao.upsert(entry.toEntity())
        return entry
    }

    override suspend fun getPendingEntries(limit: Int): List<OutboxEntry> =
        dao.getPending(limit).map { it.toDomain() }

    override suspend fun markInFlight(entryId: String) {
        val entry = dao.getById(entryId) ?: return
        val now = System.currentTimeMillis()
        dao.updateStatus(
            id = entryId,
            status = OutboxEntryStatus.IN_FLIGHT.name,
            attemptAt = now,
            updatedAt = now,
            retryCount = entry.retryCount,
            lastError = entry.lastError,
        )
    }

    override suspend fun markCompleted(entryId: String) {
        val entry = dao.getById(entryId) ?: return
        val now = System.currentTimeMillis()
        dao.updateStatus(
            id = entryId,
            status = OutboxEntryStatus.COMPLETED.name,
            attemptAt = now,
            updatedAt = now,
            retryCount = entry.retryCount,
            lastError = null,
        )
    }

    override suspend fun markFailed(entryId: String, incrementRetry: Boolean, lastError: String?) {
        val entry = dao.getById(entryId) ?: return
        val retry = if (incrementRetry) entry.retryCount + 1 else entry.retryCount
        val now = System.currentTimeMillis()
        dao.updateStatus(
            id = entryId,
            status = OutboxEntryStatus.FAILED.name,
            attemptAt = now,
            updatedAt = now,
            retryCount = retry,
            lastError = lastError,
        )
    }
}

@Singleton
class PendingEvidenceRepositoryImpl @Inject constructor(
    database: HubDatabase,
) : PendingEvidenceRepository {
    private val dao = database.pendingEvidenceDao()

    override suspend fun enqueue(
        workflowExecutionId: String,
        evidenceType: String,
        interactionReference: String,
        payloadJson: String,
        correlationId: String,
        idempotencyKey: String,
    ): PendingEvidence {
        val now = System.currentTimeMillis()
        val evidence = PendingEvidence(
            id = UUID.randomUUID().toString(),
            workflowExecutionId = workflowExecutionId,
            evidenceType = evidenceType,
            interactionReference = interactionReference,
            payloadJson = payloadJson,
            status = PendingEvidenceStatus.PENDING.name,
            correlationId = correlationId,
            idempotencyKey = idempotencyKey,
            retryCount = 0,
            createdAtEpochMillis = now,
            updatedAtEpochMillis = now,
            lastAttemptAtEpochMillis = null,
            lastError = null,
        )
        dao.upsert(evidence.toEntity())
        return evidence
    }

    override suspend fun getPending(limit: Int): List<PendingEvidence> =
        dao.getPending(limit).map { it.toDomain() }

    override suspend fun findHubConfirmationEvidence(workflowExecutionId: String): PendingEvidence? =
        dao.getHubConfirmationByExecution(workflowExecutionId)?.toDomain()

    override fun observeHubConfirmationEvidence(): kotlinx.coroutines.flow.Flow<List<PendingEvidence>> =
        dao.observeHubConfirmationEvidence().map { entities -> entities.map { it.toDomain() } }

    override fun observePendingCount(): Flow<Int> = dao.observePendingCount()

    override suspend fun markSubmitted(id: String) {
        val evidence = dao.getById(id) ?: return
        val now = System.currentTimeMillis()
        dao.updateStatus(
            id = id,
            status = PendingEvidenceStatus.SUBMITTED.name,
            attemptAt = now,
            updatedAt = now,
            retryCount = evidence.retryCount,
            lastError = null,
        )
    }

    override suspend fun markInFlight(id: String) {
        val evidence = dao.getById(id) ?: return
        val now = System.currentTimeMillis()
        dao.updateStatus(
            id = id,
            status = PendingEvidenceStatus.IN_FLIGHT.name,
            attemptAt = now,
            updatedAt = now,
            retryCount = evidence.retryCount,
            lastError = null,
        )
    }

    override suspend fun revertToPending(id: String) {
        val evidence = dao.getById(id) ?: return
        val now = System.currentTimeMillis()
        dao.updateStatus(
            id = id,
            status = PendingEvidenceStatus.PENDING.name,
            attemptAt = now,
            updatedAt = now,
            retryCount = evidence.retryCount,
            lastError = evidence.lastError,
        )
    }

    override suspend fun markFailed(id: String, incrementRetry: Boolean, lastError: String?) {
        val evidence = dao.getById(id) ?: return
        val now = System.currentTimeMillis()
        val retry = if (incrementRetry) evidence.retryCount + 1 else evidence.retryCount
        dao.updateStatus(
            id = id,
            status = PendingEvidenceStatus.FAILED.name,
            attemptAt = now,
            updatedAt = now,
            retryCount = retry,
            lastError = lastError,
        )
    }
}

@Singleton
class RuntimeStateRepositoryImpl @Inject constructor(
    database: HubDatabase,
) : RuntimeStateRepository {
    private val dao = database.runtimeStateDao()

    override suspend fun upsert(record: RuntimeStateRecord) {
        dao.upsert(record.toEntity())
    }

    override suspend fun get(componentId: String): RuntimeStateRecord? =
        dao.get(componentId)?.toDomain()

    override suspend fun getAll(): List<RuntimeStateRecord> =
        dao.getAll().map { it.toDomain() }

    override fun observeKernelState(): kotlinx.coroutines.flow.Flow<RuntimeStateRecord?> =
        dao.observe(RUNTIME_KERNEL_COMPONENT_ID).map { it?.toDomain() }
}

@Singleton
class SynchronizationRepositoryImpl @Inject constructor(
    private val hubIntegrationApi: HubIntegrationApi,
    private val synchronizationDomainApi: SynchronizationDomainApi,
    private val database: HubDatabase,
    private val json: Json,
) : SynchronizationRepository {
    private val syncSessionDao = database.syncSessionLocalDao()

    override suspend fun fetchPendingOperations(sessionId: String): AppResult<List<SyncOperation>> {
        return try {
            val operations = synchronizationDomainApi.getPendingOperations(sessionId).map { dto ->
                SyncOperation(
                    id = dto.id,
                    operationType = SyncOperationType.valueOf(dto.operationType),
                    aggregateReference = dto.aggregateReference,
                    aggregateVersion = dto.aggregateVersion,
                    payloadType = dto.payloadType,
                    payloadHash = dto.payloadHash,
                    payloadJson = dto.payload?.toString() ?: "{}",
                    status = dto.status,
                )
            }
            AppResult.Success(operations)
        } catch (exception: Exception) {
            AppResult.Error(exception)
        }
    }

    override suspend fun resumeSession(sessionId: String): AppResult<SyncSession> {
        return try {
            val response = synchronizationDomainApi.resumeSession(sessionId)
            val session = SyncSession(
                sessionId = response.id,
                direction = response.direction,
                status = response.status,
                synchronizationToken = response.synchronizationToken,
                startedAtEpochMillis = System.currentTimeMillis(),
            )
            syncSessionDao.upsert(session.toEntity())
            AppResult.Success(session)
        } catch (exception: Exception) {
            AppResult.Error(exception)
        }
    }

    override suspend fun cancelSession(sessionId: String): AppResult<Unit> {
        return try {
            synchronizationDomainApi.cancelSession(sessionId)
            syncSessionDao.delete(sessionId)
            AppResult.Success(Unit)
        } catch (exception: Exception) {
            AppResult.Error(exception)
        }
    }

    override suspend fun fetchCheckpoint(replicaId: String): AppResult<ReplicaCheckpoint> {
        return try {
            val response = synchronizationDomainApi.getCheckpoint(replicaId)
            AppResult.Success(
                ReplicaCheckpoint(
                    replicaIdentifier = response.replicaIdentifier,
                    checkpointSequence = response.checkpointSequence,
                    checkpointToken = response.checkpointToken,
                ),
            )
        } catch (exception: Exception) {
            AppResult.Error(exception)
        }
    }

    override suspend fun completeDownloadSession(sessionId: String): AppResult<Unit> {
        return try {
            hubIntegrationApi.completeDownloadSession(sessionId)
            AppResult.Success(Unit)
        } catch (exception: Exception) {
            AppResult.Error(exception)
        }
    }

    override suspend fun startSession(direction: SyncDirection, idempotencyKey: String): AppResult<SyncSession> {
        return try {
            val response = hubIntegrationApi.startSync(
                HubSyncStartRequestDto(
                    direction = direction.name,
                    idempotencyKey = idempotencyKey,
                ),
            )
            val session = SyncSession(
                sessionId = response.sessionId,
                direction = direction.name,
                status = response.status,
                synchronizationToken = response.synchronizationToken,
                startedAtEpochMillis = System.currentTimeMillis(),
            )
            syncSessionDao.upsert(session.toEntity())
            AppResult.Success(session)
        } catch (exception: Exception) {
            AppResult.Error(exception)
        }
    }

    override suspend fun submitDelta(
        sessionId: String,
        aggregateReference: String,
        aggregateVersion: String,
        payloadJson: String,
        payloadType: String,
        payloadHash: String,
        idempotencyKey: String,
    ): AppResult<Unit> = submitPayload(sessionId, aggregateReference, aggregateVersion, payloadJson, payloadType, payloadHash, idempotencyKey, delta = true)

    override suspend fun submitSnapshot(
        sessionId: String,
        aggregateReference: String,
        aggregateVersion: String,
        payloadJson: String,
        payloadType: String,
        payloadHash: String,
        idempotencyKey: String,
    ): AppResult<Unit> = submitPayload(sessionId, aggregateReference, aggregateVersion, payloadJson, payloadType, payloadHash, idempotencyKey, delta = false)

    private suspend fun submitPayload(
        sessionId: String,
        aggregateReference: String,
        aggregateVersion: String,
        payloadJson: String,
        payloadType: String,
        payloadHash: String,
        idempotencyKey: String,
        delta: Boolean,
    ): AppResult<Unit> {
        return try {
            val payloadObject = json.parseToJsonElement(payloadJson) as JsonObject
            val request = HubSyncPayloadRequestDto(
                aggregateReference = aggregateReference,
                aggregateVersion = aggregateVersion,
                payload = payloadObject,
                payloadType = payloadType,
                payloadHash = payloadHash,
                idempotencyKey = idempotencyKey,
            )
            if (delta) {
                hubIntegrationApi.submitDelta(sessionId, request)
            } else {
                hubIntegrationApi.submitSnapshot(sessionId, request)
            }
            AppResult.Success(Unit)
        } catch (exception: Exception) {
            AppResult.Error(exception)
        }
    }
}

@Singleton
class IntegrationRuntimeRepositoryImpl @Inject constructor(
    private val hubIntegrationApi: HubIntegrationApi,
    private val outboxRepository: OutboxRepository,
) : IntegrationRuntimeRepository {

    override suspend fun processRuntimeCycle(): AppResult<Map<String, Int>> {
        return try {
            val response = hubIntegrationApi.processRuntime()
            AppResult.Success(
                mapOf(
                    "due_occurrences" to response.dueOccurrences,
                    "workflow_timeouts" to response.workflowTimeouts,
                    "events_processed" to response.eventsProcessed,
                ),
            )
        } catch (exception: Exception) {
            outboxRepository.enqueue(
                operationType = OutboxOperationType.RUNTIME_PROCESS,
                payloadJson = "{}",
                idempotencyKey = "runtime-process:${System.currentTimeMillis()}",
            )
            AppResult.Error(exception)
        }
    }

    override suspend fun submitHubConfirmation(
        workflowExecutionId: String,
        interactionReference: String,
        evidenceType: String,
    ): AppResult<Unit> {
        return try {
            hubIntegrationApi.submitConfirmation(
                HubConfirmationRequestDto(
                    workflowExecutionId = workflowExecutionId,
                    interactionReference = interactionReference,
                    evidenceType = evidenceType,
                ),
            )
            AppResult.Success(Unit)
        } catch (exception: Exception) {
            outboxRepository.enqueue(
                operationType = OutboxOperationType.HUB_CONFIRMATION,
                payloadJson = """
                    {"workflow_execution_id":"$workflowExecutionId","interaction_reference":"$interactionReference","evidence_type":"$evidenceType"}
                """.trimIndent(),
                idempotencyKey = "confirmation:$workflowExecutionId:$interactionReference",
            )
            AppResult.Error(exception)
        }
    }
}
