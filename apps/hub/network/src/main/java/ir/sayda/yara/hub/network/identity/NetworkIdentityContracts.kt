package ir.sayda.yara.hub.network.identity

import kotlinx.coroutines.flow.Flow

interface ReplicaIdentityProvider {
    fun correlationId(): String
    fun replicaId(): String?
    fun deviceId(): String?
    fun accessToken(): String?
    fun refreshToken(): String?
    suspend fun updateTokens(access: String, refresh: String, expiresAtEpochMillis: Long)
    suspend fun clear()
    fun observeReplicaId(): Flow<String?>
}

interface CorrelationIdProvider {
    fun next(): String
}
