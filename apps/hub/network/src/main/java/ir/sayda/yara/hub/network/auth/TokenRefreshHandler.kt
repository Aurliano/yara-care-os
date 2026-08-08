package ir.sayda.yara.hub.network.auth

interface TokenRefreshHandler {
    suspend fun refreshAccessToken(): Boolean
}
