package ir.sayda.yara.hub.data.identity

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.longPreferencesKey
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import dagger.hilt.android.qualifiers.ApplicationContext
import ir.sayda.yara.hub.core.domain.model.HubIdentity
import ir.sayda.yara.hub.network.identity.CorrelationIdProvider
import ir.sayda.yara.hub.network.identity.ReplicaIdentityProvider
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

private val Context.hubIdentityStore by preferencesDataStore(name = "hub_identity")

@Singleton
class DataStoreReplicaIdentityProvider @Inject constructor(
    @ApplicationContext private val context: Context,
    private val snapshotHolder: IdentitySnapshotHolder,
) : ReplicaIdentityProvider, CorrelationIdProvider {

    private val dataStore: DataStore<Preferences> = context.hubIdentityStore

    override fun correlationId(): String = next()

    override fun next(): String = UUID.randomUUID().toString()

    override fun replicaId(): String? = snapshotHolder.get().replicaId

    override fun deviceId(): String? = snapshotHolder.get().deviceId

    override fun accessToken(): String? = snapshotHolder.get().accessToken

    override fun refreshToken(): String? = snapshotHolder.get().refreshToken

    override suspend fun updateTokens(access: String, refresh: String, expiresAtEpochMillis: Long) {
        dataStore.edit { prefs ->
            prefs[Keys.ACCESS_TOKEN] = access
            prefs[Keys.REFRESH_TOKEN] = refresh
            prefs[Keys.TOKEN_EXPIRES_AT] = expiresAtEpochMillis
        }
        snapshotHolder.update {
            it.copy(
                accessToken = access,
                refreshToken = refresh,
                tokenExpiresAtEpochMillis = expiresAtEpochMillis,
            )
        }
    }

    override suspend fun clear() {
        dataStore.edit { it.clear() }
        snapshotHolder.clear()
    }

    override fun observeReplicaId(): Flow<String?> =
        dataStore.data.map { it[Keys.REPLICA_ID] }

    fun observeIdentity(): Flow<HubIdentity?> =
        dataStore.data.map { prefs -> prefs.toHubIdentity() }

    suspend fun hydrateFromStore() {
        val prefs = dataStore.data.first()
        snapshotHolder.set(
            IdentitySnapshot(
                deviceId = prefs[Keys.DEVICE_ID],
                replicaId = prefs[Keys.REPLICA_ID],
                accessToken = prefs[Keys.ACCESS_TOKEN],
                refreshToken = prefs[Keys.REFRESH_TOKEN],
                tokenExpiresAtEpochMillis = prefs[Keys.TOKEN_EXPIRES_AT] ?: 0L,
            ),
        )
    }

    suspend fun readIdentity(): HubIdentity? = dataStore.data.first().toHubIdentity()

    suspend fun writeIdentity(identity: HubIdentity) {
        dataStore.edit { prefs ->
            prefs[Keys.DEVICE_ID] = identity.deviceId
            prefs[Keys.REPLICA_ID] = identity.replicaId
            identity.elderId?.let { prefs[Keys.ELDER_ID] = it }
            prefs[Keys.ACCESS_TOKEN] = identity.accessToken
            prefs[Keys.REFRESH_TOKEN] = identity.refreshToken
            prefs[Keys.TOKEN_EXPIRES_AT] = identity.tokenExpiresAtEpochMillis
        }
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

    private fun Preferences.toHubIdentity(): HubIdentity? {
        val deviceId = this[Keys.DEVICE_ID] ?: return null
        val replicaId = this[Keys.REPLICA_ID] ?: return null
        val access = this[Keys.ACCESS_TOKEN] ?: return null
        val refresh = this[Keys.REFRESH_TOKEN] ?: return null
        return HubIdentity(
            deviceId = deviceId,
            replicaId = replicaId,
            elderId = this[Keys.ELDER_ID],
            accessToken = access,
            refreshToken = refresh,
            tokenExpiresAtEpochMillis = this[Keys.TOKEN_EXPIRES_AT] ?: 0L,
        )
    }

    private object Keys {
        val DEVICE_ID = stringPreferencesKey("device_id")
        val REPLICA_ID = stringPreferencesKey("replica_id")
        val ELDER_ID = stringPreferencesKey("elder_id")
        val ACCESS_TOKEN = stringPreferencesKey("access_token")
        val REFRESH_TOKEN = stringPreferencesKey("refresh_token")
        val TOKEN_EXPIRES_AT = longPreferencesKey("token_expires_at")
    }
}
