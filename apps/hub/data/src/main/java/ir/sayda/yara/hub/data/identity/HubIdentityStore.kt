package ir.sayda.yara.hub.data.identity

import ir.sayda.yara.hub.core.domain.model.HubIdentity
import ir.sayda.yara.hub.core.domain.model.ProvisioningState

/**
 * Abstraction over the encrypted identity persistence layer.
 * Allows unit-testing code that depends on identity storage
 * without requiring an Android Context for EncryptedSharedPreferences.
 */
interface HubIdentityStore {

    fun read(): StoredHubIdentity?

    fun readProvisioning(): StoredProvisioning?

    fun write(identity: HubIdentity)

    fun clear()

    data class StoredProvisioning(
        val deviceId: String,
        val replicaId: String?,
        val elderId: String?,
        val backendUrl: String,
        val provisionedAtEpochMillis: Long,
        val lastAuthenticatedAtEpochMillis: Long,
        val provisioningState: ProvisioningState,
    )

    data class StoredHubIdentity(
        val deviceId: String,
        val replicaId: String,
        val elderId: String?,
        val accessToken: String,
        val refreshToken: String,
        val tokenExpiresAtEpochMillis: Long,
        val backendUrl: String,
        val provisionedAtEpochMillis: Long,
        val lastAuthenticatedAtEpochMillis: Long,
        val provisioningState: ProvisioningState,
    ) {
        fun toHubIdentity(): HubIdentity = HubIdentity(
            deviceId = deviceId,
            replicaId = replicaId,
            elderId = elderId,
            accessToken = accessToken,
            refreshToken = refreshToken,
            tokenExpiresAtEpochMillis = tokenExpiresAtEpochMillis,
            backendUrl = backendUrl,
            provisionedAtEpochMillis = provisionedAtEpochMillis,
            lastAuthenticatedAtEpochMillis = lastAuthenticatedAtEpochMillis,
            provisioningState = provisioningState,
        )
    }
}
