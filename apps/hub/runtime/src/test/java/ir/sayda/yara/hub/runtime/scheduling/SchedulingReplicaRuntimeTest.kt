package ir.sayda.yara.hub.runtime.scheduling

import ir.sayda.yara.hub.core.scheduling.OccurrenceStatus
import ir.sayda.yara.hub.runtime.event.RuntimeEventBusImpl
import ir.sayda.yara.hub.runtime.support.InMemoryOccurrenceAlarmRegistry
import ir.sayda.yara.hub.runtime.support.InMemorySchedulingRepository
import ir.sayda.yara.hub.runtime.support.sampleSchedule
import ir.sayda.yara.hub.runtime.alarm.RuntimeAlarmCoordinator
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Test

class SchedulingReplicaRuntimeTest {

    @Test
    fun generatesOccurrenceAndMarksDue() = runTest {
        val now = 1_700_000_000_000L
        val scheduleStart = now - 60_000L
        val schedulingRepository = InMemorySchedulingRepository()
        schedulingRepository.seedSchedule(sampleSchedule(startAtEpochMillis = scheduleStart))
        val eventBus = RuntimeEventBusImpl()
        val alarmRegistry = InMemoryOccurrenceAlarmRegistry()
        val alarmCoordinator = RuntimeAlarmCoordinator(schedulingRepository, alarmRegistry)
        val runtime = SchedulingReplicaRuntime(schedulingRepository, eventBus, alarmCoordinator)

        val result = runtime.hydrateAndEvaluate(now)

        assertEquals(1, result.schedulesObserved)
        assertEquals(1, result.occurrencesGenerated)
        assertEquals(1, result.occurrencesMarkedDue)
        val occurrence = schedulingRepository.allOccurrences().single()
        assertEquals(OccurrenceStatus.DUE.name, occurrence.status)
    }

    @Test
    fun preservesOccurrenceIdentityOnRegeneration() = runTest {
        val now = 1_700_000_000_000L
        val scheduleStart = now - 60_000L
        val schedulingRepository = InMemorySchedulingRepository()
        schedulingRepository.seedSchedule(sampleSchedule(startAtEpochMillis = scheduleStart))
        val alarmCoordinator = RuntimeAlarmCoordinator(
            schedulingRepository,
            InMemoryOccurrenceAlarmRegistry(),
        )
        val runtime = SchedulingReplicaRuntime(
            schedulingRepository,
            RuntimeEventBusImpl(),
            alarmCoordinator,
        )

        runtime.hydrateAndEvaluate(now)
        val firstId = schedulingRepository.allOccurrences().single().id
        runtime.hydrateAndEvaluate(now + 1_000L)
        val secondId = schedulingRepository.allOccurrences().single().id

        assertEquals(firstId, secondId)
    }
}
