package ir.sayda.yara.hub.core.runtime

import org.junit.Assert.assertEquals
import org.junit.Test

class AlarmRegistrationPlannerTest {

    @Test
    fun dedupeKeepsLatestTriggerForSameOccurrence() {
        val specs = listOf(
            OccurrenceAlarmSpec("occ-1", 100L),
            OccurrenceAlarmSpec("occ-1", 200L),
            OccurrenceAlarmSpec("occ-2", 150L),
        )
        val deduped = AlarmRegistrationPlanner.dedupeByOccurrenceId(specs)
        assertEquals(2, deduped.size)
        assertEquals(200L, deduped.first { it.occurrenceId == "occ-1" }.triggerAtEpochMillis)
    }

    @Test
    fun filterFutureAlarmsDropsPastTriggers() {
        val specs = listOf(
            OccurrenceAlarmSpec("occ-1", 100L),
            OccurrenceAlarmSpec("occ-2", 300L),
        )
        val future = AlarmRegistrationPlanner.filterFutureAlarms(specs, nowEpochMillis = 200L)
        assertEquals(listOf("occ-2"), future.map { it.occurrenceId })
    }
}
