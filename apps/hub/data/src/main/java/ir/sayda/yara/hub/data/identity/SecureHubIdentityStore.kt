package ir.sayda.yara.hub.data.identity

import android.content.Context
import android.content.SharedPreferences
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import dagger.hilt.android.qualifiers.ApplicationContext
import ir.sayda.yara.hub.core.domain.model.HubIdentity
import ir.sayda.yara.hub.core.domain.model.ProvisioningState
import ir.sayda.yara.hub.core.provisioning.ProvisionCredential
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class SecureHubIdentityStore @Inject constructor(
    @ApplicationContext context: Context,
) {
    private val masterKey = MasterKey.Builder(context)
        .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
        .build()

    private val prefs: SharedPreferences = EncryptedSharedPreferences.create(
        context,
        PREFS_NAME,
        masterKey,
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM,
    )

    private fun readProvisioningState(): ProvisioningState {
        val raw = prefs.getString(Keys.PROVISIONING_STATE, ProvisioningState.UNPROVISIONED.name)
            ?: ProvisioningState.UNPROVISIONED.name
        return runCatching { ProvisioningState.valueOf(raw) }
            .getOrDefault(ProvisioningState.UNPROVISIONED)
    }

    fun readProvisioning(): StoredProvisioning? {
        val deviceId = prefs.getString(Keys.DEVICE_ID, null) ?: return null
        return StoredProvisioning(
            deviceId = deviceId,
            replicaId = prefs.getString(Keys.REPLICA_ID, null),
            elderId = prefs.getString(Keys.ELDER_ID, null),
            backendUrl = prefs.getString(Keys.BACKEND_URL, "") ?: "",
            provisionedAtEpochMillis = prefs.getLong(Keys.PROVISIONED_AT, 0L),
            lastAuthenticatedAtEpochMillis = prefs.getLong(Keys.LAST_AUTHENTICATED_AT, 0L),
            provisioningState = readProvisioningState(),
        )
    }

    fun read(): StoredHubIdentity? {
        val deviceId = prefs.getString(Keys.DEVICE_ID, null) ?: return null
        val replicaId = prefs.getString(Keys.REPLICA_ID, null) ?: return null
        val accessToken = prefs.getString(Keys.ACCESS_TOKEN, null) ?: return null
        val refreshToken = prefs.getString(Keys.REFRESH_TOKEN, null) ?: return null
        return StoredHubIdentity(
            deviceId = deviceId,
            replicaId = replicaId,
            elderId = prefs.getString(Keys.ELDER_ID, null),
            accessToken = accessToken,
            refreshToken = refreshToken,
            tokenExpiresAtEpochMillis = prefs.getLong(Keys.TOKEN_EXPIRES_AT, 0L),
            backendUrl = prefs.getString(Keys.BACKEND_URL, "") ?: "",
            provisionedAtEpochMillis = prefs.getLong(Keys.PROVISIONED_AT, 0L),
            lastAuthenticatedAtEpochMillis = prefs.getLong(Keys.LAST_AUTHENTICATED_AT, 0L),
            provisioningState = readProvisioningState(),
        )
    }

    fun write(identity: HubIdentity) {
        prefs.edit()
            .putString(Keys.DEVICE_ID, identity.deviceId)
            .putString(Keys.REPLICA_ID, identity.replicaId)
            .putString(Keys.ELDER_ID, identity.elderId)
            .putString(Keys.ACCESS_TOKEN, identity.accessToken)
            .putString(Keys.REFRESH_TOKEN, identity.refreshToken)
            .putLong(Keys.TOKEN_EXPIRES_AT, identity.tokenExpiresAtEpochMillis)
            .putString(Keys.BACKEND_URL, identity.backendUrl)
            .putLong(Keys.PROVISIONED_AT, identity.provisionedAtEpochMillis)
            .putLong(Keys.LAST_AUTHENTICATED_AT, identity.lastAuthenticatedAtEpochMillis)
            .putString(Keys.PROVISIONING_STATE, identity.provisioningState.name)
            .apply()
    }

    fun writePartial(
        deviceId: String? = null,
        replicaId: String? = null,
        elderId: String? = null,
        backendUrl: String? = null,
        provisionedAtEpochMillis: Long? = null,
        lastAuthenticatedAtEpochMillis: Long? = null,
        provisioningState: ProvisioningState? = null,
    ) {
        val editor = prefs.edit()
        deviceId?.let { editor.putString(Keys.DEVICE_ID, it) }
        replicaId?.let { editor.putString(Keys.REPLICA_ID, it) }
        elderId?.let { editor.putString(Keys.ELDER_ID, it) }
        backendUrl?.let { editor.putString(Keys.BACKEND_URL, it) }
        provisionedAtEpochMillis?.let { editor.putLong(Keys.PROVISIONED_AT, it) }
        lastAuthenticatedAtEpochMillis?.let { editor.putLong(Keys.LAST_AUTHENTICATED_AT, it) }
        provisioningState?.let { editor.putString(Keys.PROVISIONING_STATE, it.name) }
        editor.apply()
    }

    fun readCaregiverCredentials(): ProvisionCredential? {
        val phone = prefs.getString(Keys.CAREGIVER_PHONE, null)?.takeIf { it.isNotBlank() } ?: return null
        val password = prefs.getString(Keys.CAREGIVER_PASSWORD, null)?.takeIf { it.isNotBlank() } ?: return null
        return ProvisionCredential(phone = phone, password = password)
    }

    fun writeCaregiverCredentials(credential: ProvisionCredential) {
        prefs.edit()
            .putString(Keys.CAREGIVER_PHONE, credential.phone)
            .putString(Keys.CAREGIVER_PASSWORD, credential.password)
            .apply()
    }

    fun clearCaregiverCredentials() {
        prefs.edit()
            .remove(Keys.CAREGIVER_PHONE)
            .remove(Keys.CAREGIVER_PASSWORD)
            .apply()
    }

    fun clear() {
        prefs.edit().clear().apply()
    }

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

    private object Keys {
        const val DEVICE_ID = "device_id"
        const val REPLICA_ID = "replica_id"
        const val ELDER_ID = "elder_id"
        const val ACCESS_TOKEN = "access_token"
        const val REFRESH_TOKEN = "refresh_token"
        const val TOKEN_EXPIRES_AT = "token_expires_at"
        const val BACKEND_URL = "backend_url"
        const val PROVISIONED_AT = "provisioned_at"
        const val LAST_AUTHENTICATED_AT = "last_authenticated_at"
        const val PROVISIONING_STATE = "provisioning_state"
        const val CAREGIVER_PHONE = "caregiver_phone"
        const val CAREGIVER_PASSWORD = "caregiver_password"
    }

    companion object {
        private const val PREFS_NAME = "hub_identity_secure"
    }
}
