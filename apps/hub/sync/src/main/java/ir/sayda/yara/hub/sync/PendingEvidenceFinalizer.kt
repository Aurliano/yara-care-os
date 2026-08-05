package ir.sayda.yara.hub.sync

import ir.sayda.yara.hub.core.domain.repository.PendingEvidenceRepository
import ir.sayda.yara.hub.core.sync.PendingEvidenceStatus
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class PendingEvidenceFinalizer @Inject constructor(
    private val pendingEvidenceRepository: PendingEvidenceRepository,
) {
    suspend fun finalizeConfirmedExecutions(confirmedExecutionIds: Set<String>) {
        for (executionId in confirmedExecutionIds) {
            val evidence = pendingEvidenceRepository.findHubConfirmationEvidence(executionId) ?: continue
            if (evidence.status == PendingEvidenceStatus.SUBMITTED.name) continue
            if (evidence.status == PendingEvidenceStatus.IN_FLIGHT.name ||
                evidence.status == PendingEvidenceStatus.PENDING.name
            ) {
                pendingEvidenceRepository.markSubmitted(evidence.id)
            }
        }
    }
}
