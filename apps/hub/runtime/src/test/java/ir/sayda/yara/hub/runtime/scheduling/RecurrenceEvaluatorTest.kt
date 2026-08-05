package ir.sayda.yara.hub.runtime.scheduling

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.util.TimeZone

class RecurrenceEvaluatorTest {

    @Test
    fun dailyRecurrenceGeneratesSlots() {
        val zone = TimeZone.getTimeZone("UTC")
        val startAt = 1_704_067_200_000L // 2024-01-01T00:00:00Z approx - use fixed
        val json = """{"type":"daily","time":"08:00"}"""
        val slots = RecurrenceEvaluator.iterRecurrenceSlots(
            recurrenceDefinitionJson = json,
            timezoneName = zone.id,
            startAtEpochMillis = startAt,
            endAtEpochMillis = null,
            rangeStartEpochMillis = startAt,
            rangeEndEpochMillis = startAt + 3 * 24 * 60 * 60 * 1000L,
        )
        assertTrue(slots.size >= 3)
    }

    @Test
    fun onceRecurrenceProducesSingleSlot() {
        val startAt = 1_700_000_000_000L
        val json = """{"type":"once"}"""
        val slots = RecurrenceEvaluator.iterRecurrenceSlots(
            recurrenceDefinitionJson = json,
            timezoneName = "UTC",
            startAtEpochMillis = startAt,
            endAtEpochMillis = null,
            rangeStartEpochMillis = startAt,
            rangeEndEpochMillis = startAt + 1000,
        )
        assertEquals(1, slots.size)
    }
}
