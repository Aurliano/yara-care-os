package ir.sayda.yara.hub.data.workflow

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive

object WorkflowPostponePolicyReader {
    data class Policy(
        val allowed: Boolean,
        val maxCount: Int,
        val delaySeconds: Long,
    )

    fun read(definitionJson: String): Policy {
        return runCatching {
            val postpone = Json.parseToJsonElement(definitionJson).jsonObject["postpone"]?.jsonObject
                ?: return Policy(allowed = false, maxCount = 0, delaySeconds = 0)
            Policy(
                allowed = postpone["allowed"]?.jsonPrimitive?.content?.toBooleanStrictOrNull() ?: false,
                maxCount = postpone["max_count"]?.jsonPrimitive?.content?.toIntOrNull() ?: 0,
                delaySeconds = postpone["delay_seconds"]?.jsonPrimitive?.content?.toLongOrNull() ?: 0,
            )
        }.getOrDefault(Policy(allowed = false, maxCount = 0, delaySeconds = 0))
    }
}
