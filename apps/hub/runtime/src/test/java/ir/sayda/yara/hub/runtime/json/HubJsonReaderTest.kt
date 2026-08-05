package ir.sayda.yara.hub.runtime.json

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class HubJsonReaderTest {

    @Test
    fun readsNestedFieldsAndBuildsObjects() {
        val definition = """
            {
              "step_timeout_seconds": 3600,
              "initial_action": {
                "type": "SHOW_REMINDER",
                "title": "Reminder"
              }
            }
        """.trimIndent()

        assertEquals("SHOW_REMINDER", HubJsonReader.nestedRequireString(definition, "initial_action", "type"))
        assertEquals(3600L, HubJsonReader.longField(definition, "step_timeout_seconds"))
        assertTrue(HubJsonReader.nestedObjectString(definition, "initial_action").contains("SHOW_REMINDER"))

        val payload = HubJsonReader.buildObject("execution_id" to "exec-1", "occurrence_id" to "occ-1")
        assertEquals("exec-1", HubJsonReader.optString(payload, "execution_id"))
        assertEquals("occ-1", HubJsonReader.requireString(payload, "occurrence_id"))
    }
}
