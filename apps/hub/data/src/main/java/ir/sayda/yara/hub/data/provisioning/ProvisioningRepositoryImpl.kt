package ir.sayda.yara.hub.data.provisioning

import ir.sayda.yara.hub.core.di.HubBaseUrl
import ir.sayda.yara.hub.core.domain.model.HubIdentity
import ir.sayda.yara.hub.core.domain.model.ProvisioningState
import ir.sayda.yara.hub.core.domain.model.ProvisioningStatus
import ir.sayda.yara.hub.core.domain.repository.AuthRepository
import ir.sayda.yara.hub.core.domain.repository.ProvisioningRepository
import ir.sayda.yara.hub.core.result.AppResult
import ir.sayda.yara.hub.data.identity.SecureHubIdentityStore
import ir.sayda.yara.hub.network.api.ProvisioningApi
import ir.sayda.yara.hub.network.dto.HubProvisionAuthenticateRequestDto
import ir.sayda.yara.hub.network.dto.HubProvisionRegisterRequestDto
import ir.sayda.yara.hub.network.dto.HubProvisionRevokeRequestDto
import ir.sayda.yara.hub.network.identity.CorrelationIdProvider
import ir.sayda.yara.hub.network.logging.HubNetworkLogger
import ir.sayda.yara.hub.sync.ReplicaStateInitializer
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.distinctUntilChanged
import java.io.IOException
import java.time.Instant
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ProvisioningRepositoryImpl @Inject constructor(
    private val provisioningApi: ProvisioningApi,
    private val authRepository: AuthRepository,
    private val identityStore: SecureHubIdentityStore,
    private val stateMachine: ProvisioningStateMachine,
    private val correlationIdProvider: CorrelationIdProvider,
    @HubBaseUrl private val backendUrl: String,
    private val replicaStateInitializer: ReplicaStateInitializer,
) : ProvisioningRepository {

    override suspend fun registerDevice(
        serialNumber: String,
        deviceModelCode: String,
    ): AppResult<ProvisioningStatus> {
        val correlationId = correlationIdProvider.next()
        return try {
            stateMachine.transitionTo(ProvisioningState.REGISTERING)
            HubNetworkLogger.provisioningStarted(correlationId)
            val response = provisioningApi.register(
                HubProvisionRegisterRequestDto(
                    serialNumber = serialNumber,
                    deviceModelCode = deviceModelCode,
                ),
            )
            val provisionedAt = parseIsoEpoch(response.provisionedAt)
            identityStore.writePartial(
                deviceId = response.deviceId,
                replicaId = response.replicaIdentifier,
                elderId = response.elderId,
                backendUrl = backendUrl,
                provisionedAtEpochMillis = provisionedAt,
                provisioningState = ProvisioningState.REGISTERED,
            )
            stateMachine.transitionTo(ProvisioningState.REGISTERED)
            HubNetworkLogger.provisioningCompleted(response.deviceId, correlationId)
            AppResult.Success(toStatus(ProvisioningState.REGISTERED))
        } catch (exception: Exception) {
            val message = mapException(exception)
            stateMachine.transitionTo(ProvisioningState.ERROR, message)
            HubNetworkLogger.backendUnavailable(message, correlationId)
            AppResult.Error(exception)
        }
    }

    override suspend fun authenticate(
        deviceId: String,
        phone: String,
        password: String,
    ): AppResult<HubIdentity> {
        val correlationId = correlationIdProvider.next()
        return try {
            stateMachine.transitionTo(ProvisioningState.AUTHENTICATING)
            val response = provisioningApi.authenticate(
                HubProvisionAuthenticateRequestDto(
                    deviceId = deviceId,
                    phone = phone,
                    password = password,
                ),
            )
            val now = System.currentTimeMillis()
            val identity = HubIdentity(
                deviceId = response.deviceId,
                replicaId = response.replicaIdentifier,
                elderId = response.elderId,
                accessToken = response.access,
                refreshToken = response.refresh,
                tokenExpiresAtEpochMillis = JwtExpiryParser.expiresAtEpochMillis(response.access, now),
                backendUrl = backendUrl,
                provisionedAtEpochMillis = parseIsoEpoch(response.provisionedAt),
                lastAuthenticatedAtEpochMillis = response.authenticatedAt?.let(::parseIsoEpoch) ?: now,
                provisioningState = ProvisioningState.READY,
            )
            authRepository.saveIdentity(identity)
            stateMachine.transitionTo(ProvisioningState.READY)
            replicaStateInitializer.ensureInitialized()
            HubNetworkLogger.authenticationSuccess(deviceId, correlationId)
            AppResult.Success(identity)
        } catch (exception: Exception) {
            val message = mapException(exception)
            stateMachine.transitionTo(ProvisioningState.ERROR, message)
            HubNetworkLogger.authenticationFailed(message, correlationId)
            AppResult.Error(exception)
        }
    }

    override suspend fun restoreProvisioning(): AppResult<ProvisioningStatus> {
        val stored = identityStore.readProvisioning()
        if (stored == null) {
            stateMachine.transitionTo(ProvisioningState.UNPROVISIONED)
            return AppResult.Success(toStatus(ProvisioningState.UNPROVISIONED))
        }
        stateMachine.restore(stored.provisioningState)
        return try {
            val status = provisioningApi.status(deviceId = stored.deviceId)
            val restoredState = mapBackendState(status.provisioningState)
            identityStore.writePartial(
                deviceId = status.deviceId,
                replicaId = status.replicaIdentifier,
                elderId = status.elderId,
                provisionedAtEpochMillis = status.provisionedAt?.let(::parseIsoEpoch),
                lastAuthenticatedAtEpochMillis = status.authenticatedAt?.let(::parseIsoEpoch),
                provisioningState = restoredState,
            )
            stateMachine.transitionTo(restoredState)
            AppResult.Success(toStatus(restoredState))
        } catch (exception: Exception) {
            AppResult.Success(toStatus(stored.provisioningState))
        }
    }

    override suspend fun revokeProvisioning(): AppResult<Unit> {
        val deviceId = identityStore.readProvisioning()?.deviceId ?: return AppResult.Error(IllegalStateException("No device"))
        return try {
            provisioningApi.revoke(HubProvisionRevokeRequestDto(deviceId = deviceId))
            authRepository.clearIdentity()
            stateMachine.transitionTo(ProvisioningState.UNPROVISIONED)
            AppResult.Success(Unit)
        } catch (exception: Exception) {
            AppResult.Error(exception)
        }
    }

    override suspend fun getStatus(): ProvisioningStatus = toStatus(stateMachine.currentState())

    override fun observeProvisioningStatus(): Flow<ProvisioningStatus> =
        combine(stateMachine.observeState(), stateMachine.observeError()) { state, error ->
            toStatus(state, error)
        }.distinctUntilChanged()

    override suspend fun setProvisioningState(state: ProvisioningState, errorMessage: String?) {
        stateMachine.transitionTo(state, errorMessage)
        identityStore.writePartial(provisioningState = state)
    }

    private fun toStatus(
        state: ProvisioningState,
        errorMessage: String? = stateMachine.currentError(),
    ): ProvisioningStatus {
        val stored = identityStore.readProvisioning()
        return ProvisioningStatus(
            state = state,
            deviceId = stored?.deviceId,
            replicaId = stored?.replicaId,
            elderId = stored?.elderId,
            backendUrl = stored?.backendUrl ?: backendUrl,
            provisionedAtEpochMillis = stored?.provisionedAtEpochMillis,
            lastAuthenticatedAtEpochMillis = stored?.lastAuthenticatedAtEpochMillis,
            lastErrorMessage = errorMessage,
        )
    }

    private fun mapBackendState(raw: String): ProvisioningState =
        when (raw.uppercase()) {
            "READY" -> ProvisioningState.READY
            "REGISTERED" -> ProvisioningState.REGISTERED
            "REVOKED" -> ProvisioningState.UNPROVISIONED
            else -> ProvisioningState.ERROR
        }

    private fun mapException(exception: Exception): String = when (exception) {
        is IOException -> "Network unavailable"
        else -> {
            val message = exception.message.orEmpty()
            when {
                message.contains("401") -> "Authentication failed"
                message.contains("403") -> "Access denied"
                message.contains("404") -> "Resource not found"
                message.contains("409") -> "Conflict"
                else -> message.ifBlank { "Unknown error" }
            }
        }
    }

    private fun parseIsoEpoch(value: String): Long =
        runCatching { Instant.parse(value).toEpochMilli() }.getOrDefault(System.currentTimeMillis())
}
