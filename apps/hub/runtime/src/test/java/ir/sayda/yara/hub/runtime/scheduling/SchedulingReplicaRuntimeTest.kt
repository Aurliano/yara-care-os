package ir.sayda.yara.hub.runtime.scheduling

import ir.sayda.yara.hub.core.scheduling.OccurrenceStatus
import ir.sayda.yara.hub.runtime.event.RuntimeEventBusImpl
import ir.sayda.yara.hub.runtime.support.InMemorySchedulingRepository
import ir.sayda.yara.hub.runtime.support.sampleSchedule
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
        val runtime = SchedulingReplicaRuntime(schedulingRepository, eventBus)

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
        val runtime = SchedulingReplicaRuntime(schedulingRepository, RuntimeEventBusImpl())

        runtime.hydrateAndEvaluate(now)
        val firstId = schedulingRepository.allOccurrences().single().id
        runtime.hydrateAndEvaluate(now + 1_000L)
        val secondId = schedulingRepository.allOccurrences().single().id

        assertEquals(firstId, secondId)
    }
}
