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

    data class RetryPolicy(
        val allowed: Boolean,
        val maxRetries: Int,
        val timeoutSeconds: Long,
        val actionJson: String?,
    )

    data class EscalationStep(
        val actionType: String,
        val actionJson: String,
        val timeoutSeconds: Long,
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

    fun retryPolicy(definitionJson: String): RetryPolicy {
        val parent = runCatching { HubJsonReader.parseObject(definitionJson)["retry"]?.jsonObject }
            .getOrNull() ?: return RetryPolicy(allowed = false, maxRetries = 0, timeoutSeconds = 0L, actionJson = null)
        val maxRetries = parent["max_retries"]?.jsonPrimitive?.content?.toIntOrNull() ?: 0
        val timeoutSeconds = parent["timeout_seconds"]?.jsonPrimitive?.content?.toLongOrNull() ?: 0L
        val actionJson = parent["action"]?.jsonObject?.toString()
        return RetryPolicy(
            allowed = maxRetries > 0,
            maxRetries = maxRetries,
            timeoutSeconds = timeoutSeconds,
            actionJson = actionJson,
        )
    }

    fun escalationSteps(definitionJson: String): List<EscalationStep> {
        val root = runCatching { HubJsonReader.parseObject(definitionJson) }.getOrNull()
        val stepsArray = root?.get("escalation_steps")
        if (stepsArray !is kotlinx.serialization.json.JsonArray) return emptyList()
        return stepsArray.mapNotNull { element ->
            val obj = element as? kotlinx.serialization.json.JsonObject ?: return@mapNotNull null
            val action = obj["action"] as? kotlinx.serialization.json.JsonObject ?: return@mapNotNull null
            val actionType = action["type"]?.jsonPrimitive?.content ?: return@mapNotNull null
            val timeoutSeconds = obj["timeout_seconds"]?.jsonPrimitive?.content?.toLongOrNull() ?: 0L
            EscalationStep(
                actionType = actionType,
                actionJson = action.toString(),
                timeoutSeconds = timeoutSeconds,
            )
        }
    }
}
