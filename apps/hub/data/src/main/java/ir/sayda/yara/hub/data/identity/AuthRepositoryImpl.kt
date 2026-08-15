package ir.sayda.yara.hub.data.identity

import dagger.Lazy
import ir.sayda.yara.hub.core.di.UnauthenticatedAuth
import ir.sayda.yara.hub.core.domain.model.HubIdentity
import ir.sayda.yara.hub.core.domain.model.ProvisioningState
import ir.sayda.yara.hub.core.domain.repository.AuthRepository
import ir.sayda.yara.hub.core.domain.repository.ProvisioningRepository
import ir.sayda.yara.hub.core.provisioning.HubDeviceCredentialsProvider
import ir.sayda.yara.hub.core.result.AppResult
import ir.sayda.yara.hub.data.provisioning.JwtExpiryParser
import ir.sayda.yara.hub.data.provisioning.ProvisioningStateMachine
import ir.sayda.yara.hub.network.api.AuthApi
import ir.sayda.yara.hub.network.dto.TokenRequestDto
import ir.sayda.yara.hub.network.identity.CorrelationIdProvider
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AuthRepositoryImpl @Inject constructor(
    private val identityStore: DataStoreReplicaIdentityProvider,
    @UnauthenticatedAuth private val authApi: AuthApi,
    private val stateMachine: ProvisioningStateMachine,
    private val correlationIdProvider: CorrelationIdProvider,
    private val tokenRefreshCoordinator: HubTokenRefreshCoordinator,
    private val provisioningRepository: Lazy<ProvisioningRepository>,
    private val deviceCredentialsProvider: HubDeviceCredentialsProvider,
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
        if (tokenRefreshCoordinator.refreshIfNeeded()) {
            return identityStore.readIdentity()?.let { AppResult.Success(it) }
                ?: AppResult.Success(current)
        }
        return reauthenticateAfterRefreshFailure(current)
    }

    override suspend fun refreshToken(): AppResult<HubIdentity> {
        val current = identityStore.readIdentity()
            ?: return AppResult.Error(IllegalStateException("No hub identity configured"))
        if (tokenRefreshCoordinator.refresh(force = true)) {
            return identityStore.readIdentity()?.let { AppResult.Success(it) }
                ?: AppResult.Error(IllegalStateException("Identity missing after token refresh"))
        }
        return reauthenticateAfterRefreshFailure(current)
    }

    override fun observeIdentity(): Flow<HubIdentity?> = identityStore.observeIdentity()

    private suspend fun reauthenticateAfterRefreshFailure(current: HubIdentity): AppResult<HubIdentity> {
        val credentials = deviceCredentialsProvider.credentials()
            ?: return AppResult.Error(IllegalStateException("Failed to refresh access token"))
        return when (
            val result = provisioningRepository.get().authenticate(
                deviceId = current.deviceId,
                phone = credentials.phone,
                password = credentials.password,
            )
        ) {
            is AppResult.Success -> result
            is AppResult.Error -> AppResult.Error(
                IllegalStateException("Failed to refresh access token", result.exception),
            )
        }
    }
}
