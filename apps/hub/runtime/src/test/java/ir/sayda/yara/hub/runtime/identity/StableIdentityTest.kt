package ir.sayda.yara.hub.runtime.identity

import org.junit.Assert.assertEquals
import org.junit.Test
import java.util.UUID

class StableIdentityTest {

    @Test
    fun occurrenceIdMatchesBackendNamespace() {
        val scheduleId = "6ba7b811-9dad-11d1-80b4-00c04fd430c8"
        val iso = "2026-08-05T08:00:00+00:00"
        val actual = computeOccurrenceId(scheduleId, iso)
        val expected = uuid5(
            UUID.fromString("6ba7b811-9dad-11d1-80b4-00c04fd430c8"),
            "$scheduleId:$iso",
        ).toString()
        assertEquals(expected, actual)
    }

    @Test
    fun executionIdIsDeterministic() {
        val occurrenceId = computeOccurrenceId(
            "11111111-1111-1111-1111-111111111111",
            "2026-08-05T08:00:00+00:00",
        )
        assertEquals(computeExecutionId(occurrenceId), computeExecutionId(occurrenceId))
    }
}
