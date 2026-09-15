package ir.sayda.yara.hub.runtime.alarm

import ir.sayda.yara.hub.core.domain.repository.SchedulingReplicaRepository
import ir.sayda.yara.hub.core.runtime.AlarmRegistrationPlanner
import ir.sayda.yara.hub.core.runtime.OccurrenceAlarmRegistry
import ir.sayda.yara.hub.core.runtime.OccurrenceAlarmSpec
import ir.sayda.yara.hub.core.scheduling.OccurrenceStatus
import ir.sayda.yara.hub.core.scheduling.ScheduleStatus
import kotlinx.coroutines.flow.first
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class RuntimeAlarmCoordinator @Inject constructor(
    private val schedulingRepository: SchedulingReplicaRepository,
    private val alarmRegistry: OccurrenceAlarmRegistry,
) {

    suspend fun syncAlarmsFromReplicas(nowEpochMillis: Long = System.currentTimeMillis()): AlarmSyncResult {
        val inactiveScheduleIds = schedulingRepository.observeScheduleDefinitions()
            .first()
            .filter { it.status != ScheduleStatus.ACTIVE.name }
            .map { it.id }
            .toSet()

        val scheduled = schedulingRepository.getScheduledOccurrencesAfter(nowEpochMillis)
            .filterNot { it.scheduleDefinitionId in inactiveScheduleIds }

        val specs = AlarmRegistrationPlanner.dedupeByOccurrenceId(
            scheduled.map { occurrence ->
                OccurrenceAlarmSpec(
                    occurrenceId = occurrence.id,
                    triggerAtEpochMillis = occurrence.scheduledForEpochMillis,
                )
            },
        )
        alarmRegistry.restoreAlarms(specs)
        return AlarmSyncResult(
            scheduledOccurrencesObserved = scheduled.size,
            alarmsRegistered = specs.size,
            activeAlarms = alarmRegistry.queryRegisteredOccurrenceIds().size,
        )
    }

    suspend fun registerAlarmForOccurrence(
        occurrenceId: String,
        triggerAtEpochMillis: Long,
        nowEpochMillis: Long = System.currentTimeMillis(),
    ) {
        if (triggerAtEpochMillis <= nowEpochMillis) return
        alarmRegistry.registerOccurrenceAlarm(
            OccurrenceAlarmSpec(
                occurrenceId = occurrenceId,
                triggerAtEpochMillis = triggerAtEpochMillis,
            ),
        )
    }

    suspend fun cancelAlarmForOccurrence(occurrenceId: String) {
        alarmRegistry.cancelOccurrenceAlarm(occurrenceId)
    }

    suspend fun registerAlarmsForNewOccurrences(nowEpochMillis: Long) {
        val inactiveScheduleIds = schedulingRepository.observeScheduleDefinitions()
            .first()
            .filter { it.status != ScheduleStatus.ACTIVE.name }
            .map { it.id }
            .toSet()

        val scheduled = schedulingRepository.getScheduledOccurrencesAfter(nowEpochMillis)
            .filter { it.status == OccurrenceStatus.SCHEDULED.name && it.scheduleDefinitionId !in inactiveScheduleIds }
        scheduled.forEach { occurrence ->
            registerAlarmForOccurrence(
                occurrenceId = occurrence.id,
                triggerAtEpochMillis = occurrence.scheduledForEpochMillis,
                nowEpochMillis = nowEpochMillis,
            )
        }
    }
}

data class AlarmSyncResult(
    val scheduledOccurrencesObserved: Int,
    val alarmsRegistered: Int,
    val activeAlarms: Int,
)
