package ir.sayda.yara.hub.sync

import ir.sayda.yara.hub.core.domain.repository.AuthRepository
import ir.sayda.yara.hub.core.domain.repository.IntegrationRuntimeRepository
import ir.sayda.yara.hub.core.domain.repository.OutboxRepository
import ir.sayda.yara.hub.core.domain.repository.PendingEvidenceRepository
import ir.sayda.yara.hub.core.domain.repository.SynchronizationRepository
import ir.sayda.yara.hub.core.result.AppResult
import ir.sayda.yara.hub.core.sync.ActiveSynchronizationSession
import ir.sayda.yara.hub.core.sync.OutboxEntryStatus
import ir.sayda.yara.hub.core.sync.OutboxOperationType
import ir.sayda.yara.hub.core.sync.SyncDirection
import ir.sayda.yara.hub.core.sync.SyncSessionStatus
import ir.sayda.yara.hub.core.sync.SynchronizationClient
import org.json.JSONObject
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class SynchronizationClientImpl @Inject constructor(
    private val synchronizationRepository: SynchronizationRepository,
    private val outboxRepository: OutboxRepository,
    private val pendingEvidenceRepository: PendingEvidenceRepository,
    private val integrationRuntimeRepository: IntegrationRuntimeRepository,
    private val authRepository: AuthRepository,
) : SynchronizationClient {

    private var activeSession: ActiveSynchronizationSession? = null

    override suspend fun beginSession(
        direction: SyncDirection,
        idempotencyKey: String,
    ): AppResult<ActiveSynchronizationSession> {
        authRepository.refreshTokenIfNeeded()
        return when (val result = synchronizationRepository.startSession(direction, idempotencyKey)) {
            is AppResult.Success -> {
                val session = ActiveSynchronizationSession(
                    sessionId = result.data.sessionId,
                    direction = direction,
                    status = SyncSessionStatus.SESSION_STARTED,
                )
                activeSession = session
                AppResult.Success(session)
            }
            is AppResult.Error -> result
        }
    }

    override suspend fun upload(limit: Int): AppResult<Int> {
        val session = activeSession ?: return AppResult.Error(IllegalStateException("No active synchronization session"))
        if (session.direction != SyncDirection.UPLOAD) {
            return AppResult.Error(IllegalStateException("Active session is not an upload session"))
        }

        val pending = outboxRepository.getPendingEntries(limit)
        var processed = 0
        for (entry in pending) {
            outboxRepository.markInFlight(entry.id)
            val success = dispatchOutboxEntry(entry.operationType, entry.payloadJson, entry.idempotencyKey)
            if (success) {
                outboxRepository.markCompleted(entry.id)
                processed++
            } else {
                outboxRepository.markFailed(entry.id, lastError = "Upload dispatch failed")
            }
        }
        return AppResult.Success(processed)
    }

    override suspend fun download(): AppResult<Unit> {
        // Download semantics are deferred; the public contract is fixed for Sprint II-B.
        return AppResult.Error(UnsupportedOperationException("Download synchronization is not implemented yet"))
    }

    override suspend fun complete(): AppResult<Unit> {
        activeSession = activeSession?.copy(status = SyncSessionStatus.SESSION_COMPLETED)
        return AppResult.Success(Unit)
    }

    override suspend fun cancel(): AppResult<Unit> {
        activeSession = activeSession?.copy(status = SyncSessionStatus.SESSION_CANCELLED)
        activeSession = null
        return AppResult.Success(Unit)
    }

    override suspend fun resume(): AppResult<ActiveSynchronizationSession> {
        val session = activeSession ?: return AppResult.Error(IllegalStateException("No session to resume"))
        return AppResult.Success(session)
    }

    override suspend fun flushPendingEvidence(limit: Int): AppResult<Int> {
        val pending = pendingEvidenceRepository.getPending(limit)
        var processed = 0
        for (evidence in pending) {
            val result = integrationRuntimeRepository.submitHubConfirmation(
                workflowExecutionId = evidence.workflowExecutionId,
                interactionReference = evidence.interactionReference,
                evidenceType = evidence.evidenceType,
            )
            if (result is AppResult.Success) {
                pendingEvidenceRepository.markSubmitted(evidence.id)
                processed++
            } else {
                val message = (result as? AppResult.Error)?.exception?.message ?: "Evidence submission failed"
                pendingEvidenceRepository.markFailed(evidence.id, lastError = message)
            }
        }
        return AppResult.Success(processed)
    }

    private suspend fun dispatchOutboxEntry(operationType: String, payloadJson: String, idempotencyKey: String): Boolean {
        return when (OutboxOperationType.valueOf(operationType)) {
            OutboxOperationType.RUNTIME_PROCESS -> {
                integrationRuntimeRepository.processRuntimeCycle() is AppResult.Success
            }
            OutboxOperationType.HUB_CONFIRMATION -> {
                val payload = JSONObject(payloadJson)
                integrationRuntimeRepository.submitHubConfirmation(
                    workflowExecutionId = payload.getString("workflow_execution_id"),
                    interactionReference = payload.getString("interaction_reference"),
                    evidenceType = payload.optString("evidence_type", "HUB_CONFIRMATION"),
                ) is AppResult.Success
            }
            OutboxOperationType.SUBMIT_DELTA,
            OutboxOperationType.SUBMIT_SNAPSHOT,
            -> {
                val payload = JSONObject(payloadJson)
                val direction = payload.optString("direction", SyncDirection.UPLOAD.name)
                synchronizationRepository.startSession(
                    SyncDirection.valueOf(direction),
                    idempotencyKey,
                ) is AppResult.Success
            }
            else -> false
        }
    }
}
