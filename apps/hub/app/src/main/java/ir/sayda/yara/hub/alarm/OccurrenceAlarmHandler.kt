package ir.sayda.yara.hub.alarm

import ir.sayda.yara.hub.core.di.ApplicationScope
import ir.sayda.yara.hub.core.domain.repository.SchedulingReplicaRepository
import ir.sayda.yara.hub.core.domain.usecase.RecoverRuntimeUseCase
import ir.sayda.yara.hub.core.domain.usecase.RunIntegrationCycleUseCase
import ir.sayda.yara.hub.core.runtime.RuntimeEvent
import ir.sayda.yara.hub.core.runtime.RuntimeEventBus
import ir.sayda.yara.hub.core.runtime.RuntimeOccurrenceDue
import ir.sayda.yara.hub.core.runtime.RuntimeScheduler
import ir.sayda.yara.hub.core.scheduling.OccurrenceStatus
import ir.sayda.yara.hub.runtime.alarm.RuntimeAlarmCoordinator
import ir.sayda.yara.hub.runtime.bootstrap.HubWorkflowBootstrap
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

@Singleton
class OccurrenceAlarmHandler @Inject constructor(
    private val schedulingRepository: SchedulingReplicaRepository,
    private val runtimeAlarmCoordinator: RuntimeAlarmCoordinator,
    private val recoverRuntimeUseCase: RecoverRuntimeUseCase,
    private val runIntegrationCycleUseCase: RunIntegrationCycleUseCase,
    private val hubWorkflowBootstrap: HubWorkflowBootstrap,
    private val runtimeScheduler: RuntimeScheduler,
    private val eventBus: RuntimeEventBus,
    @ApplicationScope private val applicationScope: CoroutineScope,
) {
    fun onOccurrenceAlarm(occurrenceId: String, onComplete: (() -> Unit)? = null) {
        applicationScope.launch(Dispatchers.IO) {
            try {
                hubWorkflowBootstrap.ensureWorkflowDefinitionsForCareActivities()
                val occurrence = schedulingRepository.getOccurrence(occurrenceId)
                if (occurrence != null && occurrence.status == OccurrenceStatus.SCHEDULED.name) {
                    val now = System.currentTimeMillis()
                    val dueOccurrence = occurrence.copy(
                        status = OccurrenceStatus.DUE.name,
                        updatedAtEpochMillis = now,
                    )
                    schedulingRepository.upsertOccurrence(dueOccurrence)
                    runtimeAlarmCoordinator.cancelAlarmForOccurrence(occurrence.id)
                    eventBus.publish(
                        RuntimeEvent.OccurrenceDue(
                            RuntimeOccurrenceDue(
                                occurrenceId = dueOccurrence.id,
                                scheduleDefinitionId = dueOccurrence.scheduleDefinitionId,
                                scheduledForEpochMillis = dueOccurrence.scheduledForEpochMillis,
                            ),
                        ),
                    )
                }
                recoverRuntimeUseCase()
                runIntegrationCycleUseCase()
            } finally {
                onComplete?.invoke()
            }
        }
        runtimeScheduler.scheduleOneTimeRuntimeWork(occurrenceId)
    }
}
