package ir.sayda.yara.hub.alarm

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import ir.sayda.yara.hub.core.runtime.OccurrenceAlarmSpec
import ir.sayda.yara.hub.runtime.alarm.stableAlarmRequestCode
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class AlarmRegistryInstrumentedTest {

    @Test
    fun registerAndQueryOccurrenceAlarmUsesStableRequestCode() {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        val registry = AlarmRegistry(context)
        val occurrenceId = "550e8400-e29b-41d4-a716-446655440000"
        val triggerAt = System.currentTimeMillis() + 60_000L

        runBlockingCompat {
            registry.registerOccurrenceAlarm(
                OccurrenceAlarmSpec(
                    occurrenceId = occurrenceId,
                    triggerAtEpochMillis = triggerAt,
                ),
            )
            val updatedTriggerAt = triggerAt + 30_000L
            registry.registerOccurrenceAlarm(
                OccurrenceAlarmSpec(
                    occurrenceId = occurrenceId,
                    triggerAtEpochMillis = updatedTriggerAt,
                ),
            )
        }

        assertTrue(registry.isOccurrenceAlarmRegistered(occurrenceId))
        assertEquals(
            stableAlarmRequestCode(occurrenceId),
            stableAlarmRequestCode(occurrenceId),
        )

        runBlockingCompat {
            registry.cancelOccurrenceAlarm(occurrenceId)
        }
        assertFalse(registry.isOccurrenceAlarmRegistered(occurrenceId))
    }

    private fun runBlockingCompat(block: suspend () -> Unit) {
        kotlinx.coroutines.runBlocking { block() }
    }
}
