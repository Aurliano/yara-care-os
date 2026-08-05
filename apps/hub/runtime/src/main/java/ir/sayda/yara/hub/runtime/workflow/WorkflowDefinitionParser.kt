package ir.sayda.yara.hub.runtime.workflow

import ir.sayda.yara.hub.runtime.json.HubJsonReader

object WorkflowDefinitionParser {

    fun initialActionType(definitionJson: String): String =
        HubJsonReader.nestedRequireString(definitionJson, "initial_action", "type")

    fun initialActionJson(definitionJson: String): String =
        HubJsonReader.nestedObjectString(definitionJson, "initial_action")

    fun stepTimeoutSeconds(definitionJson: String): Long =
        HubJsonReader.longField(definitionJson, "step_timeout_seconds")
}
