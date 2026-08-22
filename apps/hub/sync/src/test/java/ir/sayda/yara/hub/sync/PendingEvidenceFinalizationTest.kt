package ir.sayda.yara.hub.sync

import ir.sayda.yara.hub.core.domain.repository.PendingEvidenceRepository
import ir.sayda.yara.hub.core.domain.model.PendingEvidence
import ir.sayda.yara.hub.core.sync.PendingEvidenceStatus
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Test

class PendingEvidenceFinalizationTest {

    @Test
    fun uploadAckDoesNotSubmitUntilConfirmedReplicaApplied() = runTest {
        val repository = TrackingPendingEvidenceRepository()
        val evidence = repository.enqueue(
            workflowExecutionId = "exec-1",
            evidenceType = "HUB_CONFIRMATION",
            interactionReference = "tap-1",
            payloadJson = "{}",
            correlationId = "corr",
            idempotencyKey = "key-1",
        )
        repository.markInFlight(evidence.id)
        assertEquals(PendingEvidenceStatus.IN_FLIGHT.name, repository.lastStatus(evidence.id))

        PendingEvidenceFinalizer(repository).finalizeConfirmedExecutions(emptySet())
        assertEquals(PendingEvidenceStatus.IN_FLIGHT.name, repository.lastStatus(evidence.id))

        PendingEvidenceFinalizer(repository).finalizeConfirmedExecutions(setOf("exec-1"))
        assertEquals(PendingEvidenceStatus.SUBMITTED.name, repository.lastStatus(evidence.id))
    }

    private class TrackingPendingEvidenceRepository : PendingEvidenceRepository {
        private val items = mutableMapOf<String, PendingEvidence>()

        override suspend fun enqueue(
            workflowExecutionId: String,
            evidenceType: String,
            interactionReference: String,
            payloadJson: String,
            correlationId: String,
            idempotencyKey: String,
        ): PendingEvidence {
            val evidence = PendingEvidence(
                id = "evidence-1",
                workflowExecutionId = workflowExecutionId,
                evidenceType = evidenceType,
                interactionReference = interactionReference,
                payloadJson = payloadJson,
                status = PendingEvidenceStatus.PENDING.name,
                correlationId = correlationId,
                idempotencyKey = idempotencyKey,
                retryCount = 0,
                createdAtEpochMillis = 0L,
                updatedAtEpochMillis = 0L,
                lastAttemptAtEpochMillis = null,
                lastError = null,
            )
            items[evidence.id] = evidence
            return evidence
        }

        fun lastStatus(id: String) = items[id]?.status

        override suspend fun getPending(limit: Int): List<PendingEvidence> {
            val now = System.currentTimeMillis()
            return items.values
                .filter {
                    ir.sayda.yara.hub.core.sync.UploadRetryPolicy.isReady(
                        status = it.status,
                        retryCount = it.retryCount,
                        lastAttemptAtEpochMillis = it.lastAttemptAtEpochMillis,
                        nowEpochMillis = now,
                    )
                }
                .take(limit)
        }

        override suspend fun findHubConfirmationEvidence(workflowExecutionId: String): PendingEvidence? =
            items.values.lastOrNull { it.workflowExecutionId == workflowExecutionId }

        override fun observeHubConfirmationEvidence(): Flow<List<PendingEvidence>> = flowOf(emptyList())
        override fun observePendingCount(): Flow<Int> = flowOf(0)
        override suspend fun markSubmitted(id: String) { update(id, PendingEvidenceStatus.SUBMITTED.name) }
        override suspend fun markInFlight(id: String) { update(id, PendingEvidenceStatus.IN_FLIGHT.name) }
        override suspend fun revertToPending(id: String) { update(id, PendingEvidenceStatus.PENDING.name) }
        override suspend fun markFailed(id: String, incrementRetry: Boolean, lastError: String?) {
            update(id, PendingEvidenceStatus.FAILED.name)
        }

        private fun update(id: String, status: String) {
            items[id]?.let { items[id] = it.copy(status = status) }
        }
    }
}
