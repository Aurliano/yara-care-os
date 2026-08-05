package ir.sayda.yara.hub.runtime.json

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive

object HubJsonReader {
    private val json = Json { ignoreUnknownKeys = true }

    fun parseObject(jsonString: String): JsonObject =
        json.parseToJsonElement(jsonString).jsonObject

    fun requireString(jsonString: String, key: String): String {
        val element = parseObject(jsonString)[key] ?: error("Missing key: $key")
        return element.jsonPrimitive.content
    }

    fun optString(jsonString: String, key: String, default: String = ""): String =
        parseObject(jsonString)[key]?.jsonPrimitive?.content ?: default

    fun longField(jsonString: String, key: String): Long =
        requireString(jsonString, key).toLong()

    fun nestedRequireString(jsonString: String, parentKey: String, childKey: String): String {
        val parent = parseObject(jsonString)[parentKey]?.jsonObject ?: error("Missing object: $parentKey")
        return parent[childKey]?.jsonPrimitive?.content ?: error("Missing key: $childKey")
    }

    fun nestedObjectString(jsonString: String, parentKey: String): String {
        val parent = parseObject(jsonString)[parentKey]?.jsonObject ?: error("Missing object: $parentKey")
        return parent.toString()
    }

    fun stringArray(jsonObject: JsonObject, key: String): List<String> {
        val array = jsonObject[key]?.jsonArray ?: error("Missing array: $key")
        return array.map { it.jsonPrimitive.content }
    }

    fun intField(jsonObject: JsonObject, key: String): Int =
        jsonObject[key]?.jsonPrimitive?.content?.toInt() ?: error("Missing key: $key")

    fun buildObject(vararg pairs: Pair<String, String>): String {
        val map = pairs.toMap().mapValues { JsonPrimitive(it.value) }
        return JsonObject(map).toString()
    }
}
