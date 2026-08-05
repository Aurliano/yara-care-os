package ir.sayda.yara.hub.runtime.usecase

import ir.sayda.yara.hub.core.domain.usecase.RecoverRuntimeUseCase
import ir.sayda.yara.hub.core.domain.usecase.RunIntegrationCycleUseCase
import ir.sayda.yara.hub.core.result.AppResult
import ir.sayda.yara.hub.runtime.HubRuntimeOrchestrator
import javax.inject.Inject

class RunIntegrationCycleUseCaseImpl @Inject constructor(
    private val orchestrator: HubRuntimeOrchestrator,
) : RunIntegrationCycleUseCase {
    override suspend fun invoke(): AppResult<Map<String, Int>> = orchestrator.runCycle()
}

class RecoverRuntimeUseCaseImpl @Inject constructor(
    private val orchestrator: HubRuntimeOrchestrator,
) : RecoverRuntimeUseCase {
    override suspend fun invoke(): AppResult<Unit> = orchestrator.recover()
}
