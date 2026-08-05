package ir.sayda.yara.hub.runtime.dispatcher

import ir.sayda.yara.hub.core.runtime.AppDispatchResult
import ir.sayda.yara.hub.core.runtime.RuntimeActionHandler
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ActionDispatcherTest {

    private val reminderHandler = object : RuntimeActionHandler {
        override val actionType = "SHOW_REMINDER"
        override val targetComponentId = "reminder_ui"
        override suspend fun handle(actionPayload: String, executionId: String) =
            AppDispatchResult(accepted = true, routedTo = targetComponentId)
    }

    @Test
    fun dispatchesThroughRegistry() = runBlocking {
        val registry = DefaultActionRegistry(setOf(reminderHandler))
        val dispatcher = ActionDispatcher(registry)

        val result = dispatcher.dispatch("SHOW_REMINDER", "{}", "exec-1")
        assertTrue(result.accepted)
        assertEquals("reminder_ui", result.routedTo)
    }

    @Test
    fun rejectsUnknownActionTypes() = runBlocking {
        val registry = DefaultActionRegistry(setOf(reminderHandler))
        val dispatcher = ActionDispatcher(registry)

        val result = dispatcher.dispatch("UNKNOWN", "{}", "exec-1")
        assertFalse(result.accepted)
    }
}
