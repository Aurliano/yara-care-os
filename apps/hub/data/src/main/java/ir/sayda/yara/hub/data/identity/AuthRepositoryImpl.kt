package ir.sayda.yara.hub.data.identity

import ir.sayda.yara.hub.core.domain.model.HubIdentity
import ir.sayda.yara.hub.core.domain.repository.AuthRepository
import ir.sayda.yara.hub.core.result.AppResult
import ir.sayda.yara.hub.network.api.AuthApi
import ir.sayda.yara.hub.network.dto.TokenRefreshRequestDto
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AuthRepositoryImpl @Inject constructor(
    private val identityStore: DataStoreReplicaIdentityProvider,
    private val authApi: AuthApi,
) : AuthRepository {

    override suspend fun getIdentity(): HubIdentity? = identityStore.readIdentity()

    override suspend fun saveIdentity(identity: HubIdentity) {
        identityStore.writeIdentity(identity)
    }

    override suspend fun clearIdentity() {
        identityStore.clear()
    }

    override suspend fun refreshTokenIfNeeded(): AppResult<HubIdentity> {
        return try {
            val current = identityStore.readIdentity()
                ?: return AppResult.Error(IllegalStateException("No hub identity configured"))
            if (System.currentTimeMillis() < current.tokenExpiresAtEpochMillis - TOKEN_REFRESH_SKEW_MS) {
                return AppResult.Success(current)
            }
            val response = authApi.refreshToken(TokenRefreshRequestDto(refresh = current.refreshToken))
            val refreshed = current.copy(
                accessToken = response.access,
                refreshToken = response.refresh,
                tokenExpiresAtEpochMillis = System.currentTimeMillis() + DEFAULT_TOKEN_TTL_MS,
            )
            identityStore.writeIdentity(refreshed)
            AppResult.Success(refreshed)
        } catch (exception: Exception) {
            AppResult.Error(exception)
        }
    }

    override fun observeIdentity(): Flow<HubIdentity?> = identityStore.observeIdentity()

    companion object {
        private const val TOKEN_REFRESH_SKEW_MS = 60_000L
        private const val DEFAULT_TOKEN_TTL_MS = 3_600_000L
    }
}
