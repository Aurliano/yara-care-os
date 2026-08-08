package ir.sayda.yara.hub.sync.usecase

import ir.sayda.yara.hub.core.domain.usecase.RunSynchronizationCycleUseCase
import ir.sayda.yara.hub.core.provisioning.RuntimeProvisioningGate
import ir.sayda.yara.hub.core.result.AppResult
import ir.sayda.yara.hub.core.sync.ApplySummary
import ir.sayda.yara.hub.core.sync.SynchronizationClient
import javax.inject.Inject

class RunSynchronizationCycleUseCaseImpl @Inject constructor(
    private val synchronizationClient: SynchronizationClient,
    private val provisioningGate: RuntimeProvisioningGate,
) : RunSynchronizationCycleUseCase {
    override suspend fun invoke(idempotencyKey: String): AppResult<ApplySummary> {
        if (!provisioningGate.requireRuntimeReady()) {
            return AppResult.Success(SKIPPED_NOT_READY)
        }
        return synchronizationClient.runSynchronizationCycle(idempotencyKey)
    }

    companion object {
        private val SKIPPED_NOT_READY = ApplySummary(
            appliedCount = 0,
            skippedCount = 0,
            conflictCount = 0,
            affectedReplicaDomains = emptySet(),
        )
    }
}
