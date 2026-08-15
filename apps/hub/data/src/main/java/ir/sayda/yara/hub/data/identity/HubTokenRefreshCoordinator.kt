package ir.sayda.yara.hub.data.identity

import ir.sayda.yara.hub.core.di.UnauthenticatedAuth
import ir.sayda.yara.hub.core.domain.model.HubIdentity
import ir.sayda.yara.hub.data.provisioning.JwtExpiryParser
import ir.sayda.yara.hub.network.api.AuthApi
import ir.sayda.yara.hub.network.dto.TokenRefreshRequestDto
import ir.sayda.yara.hub.network.identity.CorrelationIdProvider
import ir.sayda.yara.hub.network.logging.HubNetworkLogger
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock

@Singleton
class HubTokenRefreshCoordinator @Inject constructor(
    private val identityStore: DataStoreReplicaIdentityProvider,
    @UnauthenticatedAuth private val authApi: AuthApi,
    private val correlationIdProvider: CorrelationIdProvider,
) {
    private val mutex = Mutex()

    suspend fun refreshIfNeeded(): Boolean = refresh(force = false)

    suspend fun refresh(force: Boolean = true): Boolean {
        return mutex.withLock {
            val current = identityStore.readIdentity() ?: return false
            if (!force && !isExpired(current.tokenExpiresAtEpochMillis)) {
                return true
            }
            performRefresh(current)
        }
    }

    suspend fun refreshAndGetAccessToken(force: Boolean = true): String? {
        if (!refresh(force = force)) {
            return null
        }
        return identityStore.peekAccessToken()
    }

    private suspend fun performRefresh(current: HubIdentity): Boolean {
        return runCatching {
            val correlationId = correlationIdProvider.next()
            val response = authApi.refreshToken(TokenRefreshRequestDto(refresh = current.refreshToken))
            val refreshed = current.copy(
                accessToken = response.access,
                refreshToken = response.refresh,
                tokenExpiresAtEpochMillis = JwtExpiryParser.expiresAtEpochMillis(
                    response.access,
                    System.currentTimeMillis(),
                ),
            )
            identityStore.writeIdentity(refreshed)
            HubNetworkLogger.authenticationRefresh(current.deviceId, correlationId)
            true
        }.getOrDefault(false)
    }

    private fun isExpired(expiresAtEpochMillis: Long): Boolean =
        System.currentTimeMillis() >= expiresAtEpochMillis - TOKEN_REFRESH_SKEW_MS

    companion object {
        private const val TOKEN_REFRESH_SKEW_MS = 60_000L
    }
}
