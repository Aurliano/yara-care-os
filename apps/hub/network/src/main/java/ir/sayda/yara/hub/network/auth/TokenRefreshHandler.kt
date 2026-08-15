package ir.sayda.yara.hub.network.auth

interface TokenRefreshHandler {
    suspend fun refreshAccessToken(): Boolean

    /** Refreshes when needed and returns the access token suitable for retrying a failed request. */
    suspend fun refreshAndGetAccessToken(): String?
}
