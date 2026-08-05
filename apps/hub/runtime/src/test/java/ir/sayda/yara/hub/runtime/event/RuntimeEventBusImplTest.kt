package ir.sayda.yara.hub.runtime.event

import ir.sayda.yara.hub.core.runtime.RuntimeEvent
import ir.sayda.yara.hub.core.runtime.RuntimeOccurrenceDue
import kotlinx.coroutines.async
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertTrue
import org.junit.Test

class RuntimeEventBusImplTest {

    @Test
    fun publishesAndObservesEvents() = runTest {
        val bus = RuntimeEventBusImpl()
        val payload = RuntimeOccurrenceDue("occ-1", "schedule-1", 100L)
        val received = async { bus.observe().first() }
        advanceUntilIdle()
        bus.publish(RuntimeEvent.OccurrenceDue(payload))
        assertTrue(received.await() is RuntimeEvent.OccurrenceDue)
    }
}
