package ir.sayda.yara.hub.data.provisioning

import android.util.Base64
import org.json.JSONObject

internal object JwtExpiryParser {
    fun expiresAtEpochMillis(accessToken: String, fallbackNow: Long): Long {
        return runCatching {
            val payload = accessToken.split(".").getOrNull(1) ?: return fallbackNow + DEFAULT_TTL_MS
            val decoded = String(Base64.decode(payload, Base64.URL_SAFE or Base64.NO_PADDING or Base64.NO_WRAP))
            val expSeconds = JSONObject(decoded).optLong("exp", 0L)
            if (expSeconds <= 0L) fallbackNow + DEFAULT_TTL_MS else expSeconds * 1000L
        }.getOrDefault(fallbackNow + DEFAULT_TTL_MS)
    }

    private const val DEFAULT_TTL_MS = 3_600_000L
}
