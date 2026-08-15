package ir.sayda.yara.hub.core.debug

import android.util.Log
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.Executors

/** Development-only trace helper. Logs to Logcat and optionally forwards to the local debug ingest server. */
object DebugTrace {
    private const val TAG = "YARA_DEBUG"
    private const val SESSION_ID = "9a611b"
    private const val ENDPOINT = "http://127.0.0.1:7922/ingest/a01bab23-aeb4-42ab-b441-b2e6e2af9278"

    private val executor = Executors.newSingleThreadExecutor { runnable ->
        Thread(runnable, "yara-debug-trace").apply { isDaemon = true }
    }

    fun log(
        hypothesisId: String,
        location: String,
        message: String,
        data: Map<String, Any?> = emptyMap(),
    ) {
        val payload = buildString {
            append("{\"sessionId\":\"").append(SESSION_ID).append("\"")
            append(",\"hypothesisId\":\"").append(hypothesisId).append("\"")
            append(",\"location\":\"").append(escape(location)).append("\"")
            append(",\"message\":\"").append(escape(message)).append("\"")
            append(",\"timestamp\":").append(System.currentTimeMillis())
            append(",\"data\":{")
            data.entries.forEachIndexed { index, entry ->
                if (index > 0) append(",")
                append("\"").append(escape(entry.key)).append("\":").append(jsonValue(entry.value))
            }
            append("}}")
        }
        Log.i(TAG, payload)
        runCatching { executor.execute { post(payload) } }
    }

    private fun post(payload: String) {
        runCatching {
            val connection = URL(ENDPOINT).openConnection() as HttpURLConnection
            connection.requestMethod = "POST"
            connection.connectTimeout = 1500
            connection.readTimeout = 1500
            connection.doOutput = true
            connection.setRequestProperty("Content-Type", "application/json")
            connection.setRequestProperty("X-Debug-Session-Id", SESSION_ID)
            connection.outputStream.use { it.write(payload.toByteArray(Charsets.UTF_8)) }
            connection.responseCode
            connection.disconnect()
        }
    }

    private fun jsonValue(value: Any?): String = when (value) {
        null -> "null"
        is Number, is Boolean -> value.toString()
        else -> "\"" + escape(value.toString()) + "\""
    }

    private fun escape(value: String): String = buildString {
        value.forEach { char ->
            when (char) {
                '"' -> append("\\\"")
                '\\' -> append("\\\\")
                '\n' -> append("\\n")
                '\r' -> append("\\r")
                '\t' -> append("\\t")
                else -> if (char.code < 0x20) append("?") else append(char)
            }
        }
    }
}
