package ir.sayda.yara.hub.runtime.dispatcher

import ir.sayda.yara.hub.core.runtime.AppDispatchResult
import ir.sayda.yara.hub.core.runtime.ReminderOpenRequest
import ir.sayda.yara.hub.core.runtime.ReminderPresentationGateway
import ir.sayda.yara.hub.core.runtime.RuntimeEvent
import ir.sayda.yara.hub.core.runtime.RuntimeEventBus
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class ShowReminderActionHandlerTest {

    @Test
    fun opensReminderUiAndPublishesEvent() = runTest {
        val gateway = RecordingGateway()
        val events = mutableListOf<RuntimeEvent>()
        val bus = object : RuntimeEventBus {
            override suspend fun publish(event: RuntimeEvent) {
                events += event
            }
            override fun observe(): Flow<RuntimeEvent> = MutableSharedFlow()
        }
        val handler = ShowReminderActionHandler(gateway, bus)
        val payload = """{"execution_id":"exec-1","occurrence_id":"occ-1"}"""
        val result = handler.handle(payload, "exec-1")
        assertTrue(result.accepted)
        assertEquals("reminder_ui", result.routedTo)
        assertEquals(ReminderOpenRequest("exec-1", "occ-1"), gateway.lastRequest)
        assertTrue(events.any { it is RuntimeEvent.ReminderDisplayed })
    }

    private class RecordingGateway : ReminderPresentationGateway {
        var lastRequest: ReminderOpenRequest? = null
        override suspend fun openReminder(executionId: String, occurrenceId: String) {
            lastRequest = ReminderOpenRequest(executionId, occurrenceId)
        }
        override fun observeOpenRequests(): Flow<ReminderOpenRequest> = MutableSharedFlow()
    }
}
