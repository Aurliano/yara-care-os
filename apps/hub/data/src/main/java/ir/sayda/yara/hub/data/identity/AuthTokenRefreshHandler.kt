package ir.sayda.yara.hub.data.identity

import ir.sayda.yara.hub.network.api.AuthApi
import ir.sayda.yara.hub.network.auth.TokenRefreshHandler
import ir.sayda.yara.hub.network.dto.TokenRefreshRequestDto
import ir.sayda.yara.hub.network.identity.CorrelationIdProvider
import ir.sayda.yara.hub.network.logging.HubNetworkLogger
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AuthTokenRefreshHandler @Inject constructor(
    private val identityStore: DataStoreReplicaIdentityProvider,
    private val authApi: AuthApi,
    private val correlationIdProvider: CorrelationIdProvider,
) : TokenRefreshHandler {
    override suspend fun refreshAccessToken(): Boolean {
        val current = identityStore.readIdentity() ?: return false
        return runCatching {
            val correlationId = correlationIdProvider.next()
            val response = authApi.refreshToken(TokenRefreshRequestDto(refresh = current.refreshToken))
            val refreshed = current.copy(
                accessToken = response.access,
                refreshToken = response.refresh,
                tokenExpiresAtEpochMillis = ir.sayda.yara.hub.data.provisioning.JwtExpiryParser
                    .expiresAtEpochMillis(response.access, System.currentTimeMillis()),
            )
            identityStore.writeIdentity(refreshed)
            HubNetworkLogger.authenticationRefresh(current.deviceId, correlationId)
            true
        }.getOrDefault(false)
    }
}
