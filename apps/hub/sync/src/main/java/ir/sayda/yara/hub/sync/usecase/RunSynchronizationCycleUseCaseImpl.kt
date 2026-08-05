package ir.sayda.yara.hub.sync.usecase

import ir.sayda.yara.hub.core.domain.usecase.RunSynchronizationCycleUseCase
import ir.sayda.yara.hub.core.result.AppResult
import ir.sayda.yara.hub.core.sync.ApplySummary
import ir.sayda.yara.hub.core.sync.SynchronizationClient
import javax.inject.Inject

class RunSynchronizationCycleUseCaseImpl @Inject constructor(
    private val synchronizationClient: SynchronizationClient,
) : RunSynchronizationCycleUseCase {
    override suspend fun invoke(idempotencyKey: String): AppResult<ApplySummary> =
        synchronizationClient.runSynchronizationCycle(idempotencyKey)
}
