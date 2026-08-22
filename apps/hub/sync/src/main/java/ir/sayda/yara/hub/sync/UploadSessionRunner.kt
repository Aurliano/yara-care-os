package ir.sayda.yara.hub.sync

import ir.sayda.yara.hub.core.domain.repository.IntegrationRuntimeRepository
import ir.sayda.yara.hub.core.domain.repository.OutboxRepository
import ir.sayda.yara.hub.core.domain.repository.PendingEvidenceRepository
import ir.sayda.yara.hub.core.domain.repository.SynchronizationRepository
import ir.sayda.yara.hub.core.domain.repository.WorkflowReplicaRepository
import ir.sayda.yara.hub.core.result.AppResult
import ir.sayda.yara.hub.core.sync.OutboxOperationType
import ir.sayda.yara.hub.core.sync.SyncDirection
import ir.sayda.yara.hub.core.sync.SyncSessionStatus
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class UploadSessionRunner @Inject constructor(
    private val synchronizationRepository: SynchronizationRepository,
    private val outboxRepository: OutboxRepository,
    private val pendingEvidenceRepository: PendingEvidenceRepository,
    private val integrationRuntimeRepository: IntegrationRuntimeRepository,
    private val workflowReplicaRepository: WorkflowReplicaRepository,
    private val syncSessionStore: SyncSessionStore,
) {
    private val json = Json { ignoreUnknownKeys = true }
    suspend fun uploadPendingEvidence(limit: Int): AppResult<Int> {
        val pending = pendingEvidenceRepository.getPending(limit)
        var processed = 0
        for (evidence in pending) {
            val occurrenceId = workflowReplicaRepository
                .getExecution(evidence.workflowExecutionId)
                ?.occurrenceId
            when (
                val result = integrationRuntimeRepository.submitHubConfirmation(
                    workflowExecutionId = evidence.workflowExecutionId,
                    interactionReference = evidence.interactionReference,
                    evidenceType = evidence.evidenceType,
                    occurrenceId = occurrenceId,
                )
            ) {
                is AppResult.Success -> {
                    pendingEvidenceRepository.markInFlight(evidence.id)
                    processed++
                }
                is AppResult.Error -> {
                    val message = result.exception.message ?: "Evidence submission failed"
                    pendingEvidenceRepository.markFailed(evidence.id, lastError = message)
                }
            }
        }
        return AppResult.Success(processed)
    }

    suspend fun uploadOutbox(limit: Int): AppResult<Int> {
        val session = syncSessionStore.getCached()
            ?: return AppResult.Error(IllegalStateException("No active upload session"))
        val pending = outboxRepository.getPendingEntries(limit)
        var processed = 0
        for (entry in pending) {
            outboxRepository.markInFlight(entry.id)
            val success = when (OutboxOperationType.valueOf(entry.operationType)) {
                OutboxOperationType.SUBMIT_DELTA -> dispatchSubmitDelta(entry.payloadJson, session.sessionId, entry.idempotencyKey)
                OutboxOperationType.SUBMIT_SNAPSHOT -> dispatchSubmitSnapshot(entry.payloadJson, session.sessionId, entry.idempotencyKey)
                OutboxOperationType.RUNTIME_PROCESS ->
                    integrationRuntimeRepository.processRuntimeCycle() is AppResult.Success
                OutboxOperationType.HUB_CONFIRMATION -> dispatchHubConfirmation(entry.payloadJson)
                else -> false
            }
            if (success) {
                outboxRepository.markCompleted(entry.id)
                processed++
            } else {
                outboxRepository.markFailed(entry.id, lastError = "Upload dispatch failed")
            }
        }
        return AppResult.Success(processed)
    }

    suspend fun complete(): AppResult<Unit> {
        syncSessionStore.updateStatus(SyncSessionStatus.SESSION_COMPLETED)
        syncSessionStore.clear()
        return AppResult.Success(Unit)
    }

    private suspend fun dispatchSubmitDelta(payloadJson: String, sessionId: String, idempotencyKey: String): Boolean {
        val payload = json.parseToJsonElement(payloadJson).jsonObject
        return synchronizationRepository.submitDelta(
            sessionId = payload.string("session_id") ?: sessionId,
            aggregateReference = payload.string("aggregate_reference") ?: return false,
            aggregateVersion = payload.string("aggregate_version") ?: return false,
            payloadJson = payload.string("payload_json") ?: payloadJson,
            payloadType = payload.string("payload_type") ?: return false,
            payloadHash = payload.string("payload_hash") ?: return false,
            idempotencyKey = payload.string("idempotency_key") ?: idempotencyKey,
        ) is AppResult.Success
    }

    private suspend fun dispatchSubmitSnapshot(payloadJson: String, sessionId: String, idempotencyKey: String): Boolean {
        val payload = json.parseToJsonElement(payloadJson).jsonObject
        return synchronizationRepository.submitSnapshot(
            sessionId = payload.string("session_id") ?: sessionId,
            aggregateReference = payload.string("aggregate_reference") ?: return false,
            aggregateVersion = payload.string("aggregate_version") ?: return false,
            payloadJson = payload.string("payload_json") ?: payloadJson,
            payloadType = payload.string("payload_type") ?: return false,
            payloadHash = payload.string("payload_hash") ?: return false,
            idempotencyKey = payload.string("idempotency_key") ?: idempotencyKey,
        ) is AppResult.Success
    }

    private suspend fun dispatchHubConfirmation(payloadJson: String): Boolean {
        val payload = json.parseToJsonElement(payloadJson).jsonObject
        return integrationRuntimeRepository.submitHubConfirmation(
            workflowExecutionId = payload.string("workflow_execution_id") ?: return false,
            interactionReference = payload.string("interaction_reference") ?: return false,
            evidenceType = payload.string("evidence_type") ?: "HUB_CONFIRMATION",
            occurrenceId = payload.string("occurrence_id"),
        ) is AppResult.Success
    }

    private fun kotlinx.serialization.json.JsonObject.string(key: String): String? =
        this[key]?.jsonPrimitive?.contentOrNull
}
