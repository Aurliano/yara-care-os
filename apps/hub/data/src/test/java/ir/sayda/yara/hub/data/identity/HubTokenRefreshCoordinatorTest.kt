package ir.sayda.yara.hub.data.identity

import ir.sayda.yara.hub.core.domain.model.HubIdentity
import ir.sayda.yara.hub.core.domain.model.ProvisioningState
import ir.sayda.yara.hub.network.api.AuthApi
import ir.sayda.yara.hub.network.dto.TokenRefreshRequestDto
import ir.sayda.yara.hub.network.dto.TokenResponseDto
import ir.sayda.yara.hub.network.identity.CorrelationIdProvider
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class HubTokenRefreshCoordinatorTest {

    private val snapshotHolder = IdentitySnapshotHolder()
    private val fakeSecureStore = FakeSecureStore()
    private val identityStore = DataStoreReplicaIdentityProvider(fakeSecureStore, snapshotHolder)
    private val fakeAuthApi = FakeAuthApi()
    private val fakeCorrelationIdProvider = object : CorrelationIdProvider {
        override fun next(): String = "corr-id"
    }

    private val coordinator = HubTokenRefreshCoordinator(
        identityStore = identityStore,
        authApi = fakeAuthApi,
        correlationIdProvider = fakeCorrelationIdProvider,
    )

    @Test
    fun `refreshIfNeeded does not refresh if not expired`() = runTest {
        val identity = HubIdentity(
            deviceId = "dev", elderId = "elder", replicaId = "replica-1",
            accessToken = "access", refreshToken = "refresh",
            tokenExpiresAtEpochMillis = System.currentTimeMillis() + 100000L,
            backendUrl = "http://localhost",
            provisionedAtEpochMillis = 0L,
            lastAuthenticatedAtEpochMillis = 0L,
            provisioningState = ProvisioningState.READY,
        )
        identityStore.writeIdentity(identity)

        val result = coordinator.refreshIfNeeded()
        assertTrue(result)
        assertEquals(0, fakeAuthApi.refreshCount)
    }

    @Test
    fun `concurrent refreshes only trigger one network call with double checked locking`() = runTest {
        val identity = HubIdentity(
            deviceId = "dev", elderId = "elder", replicaId = "replica-1",
            accessToken = "access-failed", refreshToken = "refresh",
            tokenExpiresAtEpochMillis = System.currentTimeMillis() + 100000L,
            backendUrl = "http://localhost",
            provisionedAtEpochMillis = 0L,
            lastAuthenticatedAtEpochMillis = 0L,
            provisioningState = ProvisioningState.READY,
        )
        identityStore.writeIdentity(identity)

        coroutineScope {
            val jobs = (1..5).map {
                async {
                    coordinator.refresh(failedAccessToken = "access-failed", force = true)
                }
            }
            jobs.awaitAll()
        }

        assertEquals(1, fakeAuthApi.refreshCount)
        assertEquals("new-access-1", identityStore.readIdentity()?.accessToken)
    }

    /**
     * In-memory [HubIdentityStore] replacement.
     */
    private class FakeSecureStore : HubIdentityStore {
        private var stored: HubIdentityStore.StoredHubIdentity? = null

        override fun read(): HubIdentityStore.StoredHubIdentity? = stored

        override fun readProvisioning(): HubIdentityStore.StoredProvisioning? = null

        override fun write(identity: HubIdentity) {
            stored = HubIdentityStore.StoredHubIdentity(
                deviceId = identity.deviceId,
                replicaId = identity.replicaId,
                elderId = identity.elderId,
                accessToken = identity.accessToken,
                refreshToken = identity.refreshToken,
                tokenExpiresAtEpochMillis = identity.tokenExpiresAtEpochMillis,
                backendUrl = identity.backendUrl,
                provisionedAtEpochMillis = identity.provisionedAtEpochMillis,
                lastAuthenticatedAtEpochMillis = identity.lastAuthenticatedAtEpochMillis,
                provisioningState = identity.provisioningState,
            )
        }

        override fun clear() {
            stored = null
        }
    }

    class FakeAuthApi : AuthApi {
        var refreshCount = 0

        override suspend fun obtainToken(body: ir.sayda.yara.hub.network.dto.TokenRequestDto): TokenResponseDto {
            throw NotImplementedError()
        }

        override suspend fun refreshToken(body: TokenRefreshRequestDto): TokenResponseDto {
            refreshCount++
            delay(100)
            return TokenResponseDto(
                access = "new-access-$refreshCount",
                refresh = "new-refresh-$refreshCount"
            )
        }
    }
}

