package ir.sayda.yara.hub.runtime.scheduling

import ir.sayda.yara.hub.core.domain.model.Occurrence
import ir.sayda.yara.hub.core.domain.model.ScheduleDefinition
import ir.sayda.yara.hub.core.domain.repository.SchedulingReplicaRepository
import ir.sayda.yara.hub.core.runtime.RuntimeEvent
import ir.sayda.yara.hub.core.runtime.RuntimeEventBus
import ir.sayda.yara.hub.core.runtime.RuntimeOccurrenceDue
import ir.sayda.yara.hub.core.scheduling.OccurrenceStatus
import ir.sayda.yara.hub.core.scheduling.ScheduleStatus
import ir.sayda.yara.hub.runtime.alarm.RuntimeAlarmCoordinator
import ir.sayda.yara.hub.runtime.identity.computeOccurrenceId
import kotlinx.coroutines.flow.first
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class SchedulingReplicaRuntime @Inject constructor(
    private val schedulingRepository: SchedulingReplicaRepository,
    private val eventBus: RuntimeEventBus,
    private val runtimeAlarmCoordinator: RuntimeAlarmCoordinator,
) {

    suspend fun hydrateAndEvaluate(nowEpochMillis: Long = System.currentTimeMillis()): SchedulingCycleResult {
        val activeSchedules = schedulingRepository.observeScheduleDefinitions()
            .first()
            .filter { it.status == ScheduleStatus.ACTIVE.name }

        var generated = 0
        activeSchedules.forEach { schedule ->
            generated += generateOccurrencesForSchedule(schedule, nowEpochMillis)
        }

        var markedDue = 0
        val dueCandidates = schedulingRepository.getScheduledOccurrencesDueBefore(nowEpochMillis)
        for (occurrence in dueCandidates) {
            if (occurrence.status != OccurrenceStatus.SCHEDULED.name) continue
            val updated = occurrence.copy(
                status = OccurrenceStatus.DUE.name,
                updatedAtEpochMillis = nowEpochMillis,
            )
            schedulingRepository.upsertOccurrence(updated)
            runtimeAlarmCoordinator.cancelAlarmForOccurrence(updated.id)
            eventBus.publish(
                RuntimeEvent.OccurrenceDue(
                    RuntimeOccurrenceDue(
                        occurrenceId = updated.id,
                        scheduleDefinitionId = updated.scheduleDefinitionId,
                        scheduledForEpochMillis = updated.scheduledForEpochMillis,
                    ),
                ),
            )
            markedDue++
        }

        return SchedulingCycleResult(
            schedulesObserved = activeSchedules.size,
            occurrencesGenerated = generated,
            occurrencesMarkedDue = markedDue,
        )
    }

    private suspend fun generateOccurrencesForSchedule(
        schedule: ScheduleDefinition,
        nowEpochMillis: Long,
    ): Int {
        val horizonEnd = nowEpochMillis + DEFAULT_HORIZON_MILLIS
        val slots = RecurrenceEvaluator.iterRecurrenceSlots(
            recurrenceDefinitionJson = schedule.recurrenceDefinitionJson,
            timezoneName = schedule.timezone,
            startAtEpochMillis = schedule.startAtEpochMillis,
            endAtEpochMillis = schedule.endAtEpochMillis,
            rangeStartEpochMillis = schedule.startAtEpochMillis,
            rangeEndEpochMillis = horizonEnd,
        )
        var created = 0
        for (slot in slots) {
            val occurrenceId = computeOccurrenceId(schedule.id, slot.originalTimeIsoUtc)
            if (schedulingRepository.getOccurrence(occurrenceId) != null) continue
            schedulingRepository.upsertOccurrence(
                Occurrence(
                    id = occurrenceId,
                    scheduleDefinitionId = schedule.id,
                    scheduledForEpochMillis = slot.originalTimeEpochMillis,
                    status = OccurrenceStatus.SCHEDULED.name,
                    updatedAtEpochMillis = nowEpochMillis,
                ),
            )
            runtimeAlarmCoordinator.registerAlarmForOccurrence(
                occurrenceId = occurrenceId,
                triggerAtEpochMillis = slot.originalTimeEpochMillis,
                nowEpochMillis = nowEpochMillis,
            )
            created++
        }
        return created
    }

    companion object {
        private const val DEFAULT_HORIZON_MILLIS = 90L * 24 * 60 * 60 * 1000
    }
}

data class SchedulingCycleResult(
    val schedulesObserved: Int,
    val occurrencesGenerated: Int,
    val occurrencesMarkedDue: Int,
)
