package ir.sayda.yara.hub.runtime.workflow

import ir.sayda.yara.hub.runtime.json.HubJsonReader
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive

object WorkflowDefinitionParser {

    data class PostponePolicy(
        val allowed: Boolean,
        val maxCount: Int,
        val delaySeconds: Long,
    )

    fun initialActionType(definitionJson: String): String =
        HubJsonReader.nestedRequireString(definitionJson, "initial_action", "type")

    fun initialActionJson(definitionJson: String): String =
        HubJsonReader.nestedObjectString(definitionJson, "initial_action")

    fun stepTimeoutSeconds(definitionJson: String): Long =
        HubJsonReader.longField(definitionJson, "step_timeout_seconds")

    fun postponePolicy(definitionJson: String): PostponePolicy {
        val parent = runCatching { HubJsonReader.parseObject(definitionJson)["postpone"]?.jsonObject }
            .getOrNull() ?: return PostponePolicy(allowed = false, maxCount = 0, delaySeconds = 0)
        val allowed = parent["allowed"]?.jsonPrimitive?.content?.toBooleanStrictOrNull() ?: false
        val maxCount = parent["max_count"]?.jsonPrimitive?.content?.toIntOrNull() ?: 0
        val delaySeconds = parent["delay_seconds"]?.jsonPrimitive?.content?.toLongOrNull() ?: 0L
        return PostponePolicy(allowed = allowed, maxCount = maxCount, delaySeconds = delaySeconds)
    }
}
