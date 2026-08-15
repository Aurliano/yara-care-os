package ir.sayda.yara.hub.data.identity

import ir.sayda.yara.hub.core.domain.model.HubIdentity
import ir.sayda.yara.hub.network.identity.CorrelationIdProvider
import ir.sayda.yara.hub.network.identity.ReplicaIdentityProvider
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.map
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class DataStoreReplicaIdentityProvider @Inject constructor(
    private val secureStore: SecureHubIdentityStore,
    private val snapshotHolder: IdentitySnapshotHolder,
) : ReplicaIdentityProvider, CorrelationIdProvider {

    private val identityFlow = MutableStateFlow<HubIdentity?>(null)

    override fun correlationId(): String = next()

    override fun next(): String = UUID.randomUUID().toString()

    override fun replicaId(): String? = effectiveSnapshot().replicaId

    override fun deviceId(): String? = effectiveSnapshot().deviceId

    override fun accessToken(): String? = effectiveSnapshot().accessToken

    override fun refreshToken(): String? = effectiveSnapshot().refreshToken

    fun peekAccessToken(): String? = accessToken()

    /**
     * OkHttp interceptors run on worker threads before [hydrateFromStore] may finish.
     * Fall back to encrypted prefs so authenticated calls are not sent without a token.
     */
    private fun effectiveSnapshot(): IdentitySnapshot {
        val cached = snapshotHolder.get()
        val stored = secureStore.read()
        if (stored != null) {
            return IdentitySnapshot(
                deviceId = cached.deviceId ?: stored.deviceId,
                replicaId = cached.replicaId ?: stored.replicaId,
                accessToken = cached.accessToken?.takeIf { it.isNotBlank() }
                    ?: stored.accessToken?.takeIf { it.isNotBlank() },
                refreshToken = cached.refreshToken?.takeIf { it.isNotBlank() }
                    ?: stored.refreshToken?.takeIf { it.isNotBlank() },
                tokenExpiresAtEpochMillis = cached.tokenExpiresAtEpochMillis.takeIf { it > 0L }
                    ?: stored.tokenExpiresAtEpochMillis,
            )
        }
        val provisioning = secureStore.readProvisioning()
        return cached.copy(
            deviceId = cached.deviceId ?: provisioning?.deviceId,
            replicaId = cached.replicaId ?: provisioning?.replicaId,
        )
    }

    override suspend fun updateTokens(access: String, refresh: String, expiresAtEpochMillis: Long) {
        val current = secureStore.read()?.toHubIdentity() ?: return
        val updated = current.copy(
            accessToken = access,
            refreshToken = refresh,
            tokenExpiresAtEpochMillis = expiresAtEpochMillis,
        )
        writeIdentity(updated)
    }

    override suspend fun clear() {
        secureStore.clear()
        snapshotHolder.clear()
        identityFlow.value = null
    }

    override fun observeReplicaId(): Flow<String?> =
        identityFlow.map { it?.replicaId }

    fun observeIdentity(): Flow<HubIdentity?> = identityFlow.asStateFlow()

    suspend fun hydrateFromStore() {
        val identity = secureStore.read()?.toHubIdentity()
        identityFlow.value = identity
        if (identity != null) {
            snapshotHolder.set(
                IdentitySnapshot(
                    deviceId = identity.deviceId,
                    replicaId = identity.replicaId,
                    accessToken = identity.accessToken,
                    refreshToken = identity.refreshToken,
                    tokenExpiresAtEpochMillis = identity.tokenExpiresAtEpochMillis,
                ),
            )
        }
    }

    suspend fun readIdentity(): HubIdentity? = identityFlow.value ?: secureStore.read()?.toHubIdentity()

    suspend fun writeIdentity(identity: HubIdentity) {
        secureStore.write(identity)
        snapshotHolder.set(
            IdentitySnapshot(
                deviceId = identity.deviceId,
                replicaId = identity.replicaId,
                accessToken = identity.accessToken,
                refreshToken = identity.refreshToken,
                tokenExpiresAtEpochMillis = identity.tokenExpiresAtEpochMillis,
            ),
        )
        identityFlow.value = identity
    }
}
