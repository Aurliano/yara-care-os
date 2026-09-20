package ir.sayda.yara.hub.runtime.scheduling

import ir.sayda.yara.hub.runtime.identity.computeOccurrenceId
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Test
import java.util.Calendar
import java.util.Date
import java.util.SimpleTimeZone
import java.util.TimeZone

class TimezoneForensicsTest {

    @Test
    fun demonstrateIsoUtcFormatMismatch() {
        val scheduleId = "0bce2c6c-6efa-40de-b60f-c3c41552ef4c"
        // Python instant.isoformat() for UTC:
        val pythonIso = "2026-09-19T04:30:00+00:00"
        // Java SimpleDateFormat with XXX for UTC produces:
        val javaIso = "2026-09-19T04:30:00Z"

        val pythonDerivedId = computeOccurrenceId(scheduleId, pythonIso)
        val javaDerivedId = computeOccurrenceId(scheduleId, javaIso)

        // They do NOT match because of the trailing Z vs +00:00
        assertNotEquals(pythonDerivedId, javaDerivedId)
    }

    @Test
    fun demonstrateLegacyTzdataOffsetVersusModernPost2022IranLaw() {
        // Post-2022 Iran Standard Time: UTC+03:30 (12,600,000 ms) year-round (no DST)
        val modernIranZone = SimpleTimeZone(12_600_000, "Asia/Tehran")
        
        val cal = Calendar.getInstance(modernIranZone).apply {
            set(2026, Calendar.SEPTEMBER, 19, 8, 0, 0)
            set(Calendar.MILLISECOND, 0)
        }
        
        // 08:00 AM Iran Standard Time (+03:30) must be 04:30:00 UTC
        val expectedUtcEpoch = 1789792200000L // 2026-09-19 04:30:00 UTC
        assertEquals(expectedUtcEpoch, cal.timeInMillis)
    }

    @Test
    fun testRecurrenceSlotMatchesBackendDeterministically() {
        val scheduleId = "0bce2c6c-6efa-40de-b60f-c3c41552ef4c"
        // 2026-09-19 08:00 Tehran:
        val slots = RecurrenceEvaluator.iterRecurrenceSlots(
            recurrenceDefinitionJson = """{"type":"daily","time":"08:00"}""",
            timezoneName = "Asia/Tehran",
            startAtEpochMillis = 1789792200000L,
            endAtEpochMillis = 1789792200000L + 1000L,
            rangeStartEpochMillis = 1789792200000L,
            rangeEndEpochMillis = 1789792200000L + 1000L,
        )
        assertEquals(1, slots.size)
        val slot = slots[0]
        assertEquals(1789792200000L, slot.originalTimeEpochMillis)
        assertEquals("2026-09-19T04:30:00+00:00", slot.originalTimeIsoUtc)

        val occurrenceId = computeOccurrenceId(scheduleId, slot.originalTimeIsoUtc)
        // Must match Python uuid.uuid5(ns, "0bce2c6c-6efa-40de-b60f-c3c41552ef4c:2026-09-19T04:30:00+00:00")
        assertEquals("879c8dfb-946e-582c-9079-ddef3bdaaa5b", occurrenceId)
    }
}
