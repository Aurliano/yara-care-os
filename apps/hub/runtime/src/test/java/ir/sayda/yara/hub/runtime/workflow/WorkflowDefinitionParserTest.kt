package ir.sayda.yara.hub.runtime.workflow

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class WorkflowDefinitionParserTest {

    @Test
    fun parsesInitialActionAndTimeout() {
        val json = """
            {
              "step_timeout_seconds": 7200,
              "initial_action": {
                "type": "SHOW_REMINDER",
                "title": "Reminder"
              }
            }
        """.trimIndent()

        assertEquals("SHOW_REMINDER", WorkflowDefinitionParser.initialActionType(json))
        assertEquals(7200L, WorkflowDefinitionParser.stepTimeoutSeconds(json))
        assertTrue(WorkflowDefinitionParser.initialActionJson(json).contains("SHOW_REMINDER"))
    }
}
