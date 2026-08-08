package ir.sayda.yara.hub.data.identity

import ir.sayda.yara.hub.core.domain.model.HubIdentity
import ir.sayda.yara.hub.core.domain.model.ProvisioningState
import ir.sayda.yara.hub.core.domain.repository.AuthRepository
import ir.sayda.yara.hub.core.result.AppResult
import ir.sayda.yara.hub.data.provisioning.JwtExpiryParser
import ir.sayda.yara.hub.data.provisioning.ProvisioningStateMachine
import ir.sayda.yara.hub.network.api.AuthApi
import ir.sayda.yara.hub.network.dto.TokenRefreshRequestDto
import ir.sayda.yara.hub.network.dto.TokenRequestDto
import ir.sayda.yara.hub.network.identity.CorrelationIdProvider
import ir.sayda.yara.hub.network.logging.HubNetworkLogger
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AuthRepositoryImpl @Inject constructor(
    private val identityStore: DataStoreReplicaIdentityProvider,
    private val authApi: AuthApi,
    private val stateMachine: ProvisioningStateMachine,
    private val correlationIdProvider: CorrelationIdProvider,
) : AuthRepository {

    override suspend fun getIdentity(): HubIdentity? = identityStore.readIdentity()

    override suspend fun saveIdentity(identity: HubIdentity) {
        identityStore.writeIdentity(identity)
        stateMachine.transitionTo(identity.provisioningState)
    }

    override suspend fun clearIdentity() {
        identityStore.clear()
        stateMachine.transitionTo(ProvisioningState.UNPROVISIONED)
    }

    override suspend fun login(phone: String, password: String): AppResult<HubIdentity> {
        return try {
            val response = authApi.obtainToken(TokenRequestDto(phone = phone, password = password))
            val current = identityStore.readIdentity()
                ?: return AppResult.Error(IllegalStateException("Device must be registered before login"))
            val now = System.currentTimeMillis()
            val identity = current.copy(
                accessToken = response.access,
                refreshToken = response.refresh,
                tokenExpiresAtEpochMillis = JwtExpiryParser.expiresAtEpochMillis(response.access, now),
                lastAuthenticatedAtEpochMillis = now,
                provisioningState = ProvisioningState.READY,
            )
            saveIdentity(identity)
            AppResult.Success(identity)
        } catch (exception: Exception) {
            AppResult.Error(exception)
        }
    }

    override suspend fun logout(): AppResult<Unit> {
        clearIdentity()
        return AppResult.Success(Unit)
    }

    override suspend fun refreshTokenIfNeeded(): AppResult<HubIdentity> {
        val current = identityStore.readIdentity()
            ?: return AppResult.Error(IllegalStateException("No hub identity configured"))
        if (System.currentTimeMillis() < current.tokenExpiresAtEpochMillis - TOKEN_REFRESH_SKEW_MS) {
            return AppResult.Success(current)
        }
        return refreshToken()
    }

    override suspend fun refreshToken(): AppResult<HubIdentity> {
        return try {
            val current = identityStore.readIdentity()
                ?: return AppResult.Error(IllegalStateException("No hub identity configured"))
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
            AppResult.Success(refreshed)
        } catch (exception: Exception) {
            AppResult.Error(exception)
        }
    }

    override fun observeIdentity(): Flow<HubIdentity?> = identityStore.observeIdentity()

    companion object {
        private const val TOKEN_REFRESH_SKEW_MS = 60_000L
    }
}
