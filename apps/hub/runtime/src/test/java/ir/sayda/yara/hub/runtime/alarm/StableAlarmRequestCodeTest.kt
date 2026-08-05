package ir.sayda.yara.hub.runtime.alarm

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.util.UUID

class StableAlarmRequestCodeTest {

    @Test
    fun requestCodeIsStableForSameOccurrenceId() {
        val occurrenceId = "550e8400-e29b-41d4-a716-446655440000"
        assertEquals(
            stableAlarmRequestCode(occurrenceId),
            stableAlarmRequestCode(occurrenceId),
        )
    }

    @Test
    fun requestCodeIsNonNegative() {
        val occurrenceId = UUID.randomUUID().toString()
        assertTrue(stableAlarmRequestCode(occurrenceId) >= 0)
    }

    @Test
    fun requestCodeDiffersForDifferentOccurrences() {
        val first = stableAlarmRequestCode(UUID.randomUUID().toString())
        val second = stableAlarmRequestCode(UUID.randomUUID().toString())
        assertTrue(first != second)
    }
}
