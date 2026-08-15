package ir.sayda.yara.hub.alarm

import ir.sayda.yara.hub.core.di.ApplicationScope
import ir.sayda.yara.hub.core.domain.usecase.RecoverRuntimeUseCase
import ir.sayda.yara.hub.core.domain.usecase.RunIntegrationCycleUseCase
import ir.sayda.yara.hub.core.runtime.RuntimeScheduler
import ir.sayda.yara.hub.runtime.bootstrap.HubWorkflowBootstrap
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

@Singleton
class OccurrenceAlarmHandler @Inject constructor(
    private val recoverRuntimeUseCase: RecoverRuntimeUseCase,
    private val runIntegrationCycleUseCase: RunIntegrationCycleUseCase,
    private val hubWorkflowBootstrap: HubWorkflowBootstrap,
    private val runtimeScheduler: RuntimeScheduler,
    @ApplicationScope private val applicationScope: CoroutineScope,
) {
    fun onOccurrenceAlarm(occurrenceId: String, onComplete: (() -> Unit)? = null) {
        applicationScope.launch(Dispatchers.IO) {
            try {
                hubWorkflowBootstrap.ensureWorkflowDefinitionsForCareActivities()
                recoverRuntimeUseCase()
                runIntegrationCycleUseCase()
            } finally {
                onComplete?.invoke()
            }
        }
        runtimeScheduler.scheduleOneTimeRuntimeWork(occurrenceId)
    }
}
