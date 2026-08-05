package ir.sayda.yara.hub.runtime.alarm

import ir.sayda.yara.hub.core.domain.model.Occurrence
import ir.sayda.yara.hub.core.runtime.OccurrenceAlarmSpec
import ir.sayda.yara.hub.core.scheduling.OccurrenceStatus
import ir.sayda.yara.hub.runtime.support.InMemoryOccurrenceAlarmRegistry
import ir.sayda.yara.hub.runtime.support.InMemorySchedulingRepository
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class RuntimeAlarmCoordinatorTest {

    @Test
    fun syncAlarmsRegistersFutureOccurrencesOnce() = runTest {
        val schedulingRepository = InMemorySchedulingRepository()
        val alarmRegistry = InMemoryOccurrenceAlarmRegistry()
        val coordinator = RuntimeAlarmCoordinator(schedulingRepository, alarmRegistry)
        val now = 1_700_000_000_000L
        schedulingRepository.upsertOccurrence(
            Occurrence(
                id = "occ-1",
                scheduleDefinitionId = "schedule-1",
                scheduledForEpochMillis = now + 60_000L,
                status = OccurrenceStatus.SCHEDULED.name,
                updatedAtEpochMillis = now,
            ),
        )

        coordinator.syncAlarmsFromReplicas(nowEpochMillis = now)
        coordinator.syncAlarmsFromReplicas(nowEpochMillis = now)

        assertEquals(1, alarmRegistry.queryRegisteredOccurrenceIds().size)
        assertTrue(alarmRegistry.isOccurrenceAlarmRegistered("occ-1"))
    }

    @Test
    fun registerAlarmForOccurrenceIsIdempotent() = runTest {
        val schedulingRepository = InMemorySchedulingRepository()
        val alarmRegistry = InMemoryOccurrenceAlarmRegistry()
        val coordinator = RuntimeAlarmCoordinator(schedulingRepository, alarmRegistry)
        val now = 1_700_000_000_000L
        val triggerAt = now + 120_000L

        coordinator.registerAlarmForOccurrence("occ-1", triggerAt, now)
        coordinator.registerAlarmForOccurrence("occ-1", triggerAt, now)

        assertEquals(1, alarmRegistry.registered.size)
        assertEquals(triggerAt, alarmRegistry.registered["occ-1"]?.triggerAtEpochMillis)
    }

    @Test
    fun restoreAlarmsRemovesStaleRegistrations() = runTest {
        val schedulingRepository = InMemorySchedulingRepository()
        val alarmRegistry = InMemoryOccurrenceAlarmRegistry()
        val coordinator = RuntimeAlarmCoordinator(schedulingRepository, alarmRegistry)
        val now = 1_700_000_000_000L
        alarmRegistry.registered["stale"] = OccurrenceAlarmSpec("stale", now + 60_000L)
        schedulingRepository.upsertOccurrence(
            Occurrence(
                id = "occ-1",
                scheduleDefinitionId = "schedule-1",
                scheduledForEpochMillis = now + 60_000L,
                status = OccurrenceStatus.SCHEDULED.name,
                updatedAtEpochMillis = now,
            ),
        )

        coordinator.syncAlarmsFromReplicas(nowEpochMillis = now)

        assertFalse(alarmRegistry.isOccurrenceAlarmRegistered("stale"))
        assertTrue(alarmRegistry.isOccurrenceAlarmRegistered("occ-1"))
    }
}
