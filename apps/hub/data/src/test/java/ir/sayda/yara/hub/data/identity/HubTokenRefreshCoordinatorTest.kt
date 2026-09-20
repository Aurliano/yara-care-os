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
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.ResponseBody.Companion.toResponseBody
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import retrofit2.HttpException
import retrofit2.Response
import java.net.ConnectException

import io.mockk.every
import io.mockk.mockkObject
import io.mockk.unmockkObject
import ir.sayda.yara.hub.network.logging.HubNetworkLogger
import org.junit.After
import org.junit.Before

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

    @Before
    fun setUp() {
        mockkObject(HubNetworkLogger)
        every { HubNetworkLogger.authenticationRefresh(any(), any()) } returns Unit
    }

    @After
    fun tearDown() {
        unmockkObject(HubNetworkLogger)
    }

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

    @Test
    fun `pure transport failure produces PureTransportFailure and preserves expired token in store`() = runTest {
        val expiredTime = System.currentTimeMillis() - 10_000L
        val identity = HubIdentity(
            deviceId = "dev", elderId = "elder", replicaId = "replica-1",
            accessToken = "expired-token", refreshToken = "refresh-123",
            tokenExpiresAtEpochMillis = expiredTime,
            backendUrl = "http://localhost",
            provisionedAtEpochMillis = 0L,
            lastAuthenticatedAtEpochMillis = 0L,
            provisioningState = ProvisioningState.READY,
        )
        identityStore.writeIdentity(identity)

        fakeAuthApi.throwException = ConnectException("Failed to connect to /10.254.230.230:8000")

        val result = coordinator.refreshIfNeededDetailed()
        assertTrue(result is HubTokenRefreshCoordinator.RefreshResult.PureTransportFailure)

        // Store must NOT be overwritten with fake timestamps; token remains expired
        val inStore = identityStore.readIdentity()
        assertEquals(expiredTime, inStore?.tokenExpiresAtEpochMillis)
        assertEquals("expired-token", inStore?.accessToken)
    }

    @Test
    fun `HTTP 401 error produces AuthenticationFailure`() = runTest {
        val identity = HubIdentity(
            deviceId = "dev", elderId = "elder", replicaId = "replica-1",
            accessToken = "expired-token", refreshToken = "bad-refresh",
            tokenExpiresAtEpochMillis = System.currentTimeMillis() - 10_000L,
            backendUrl = "http://localhost",
            provisionedAtEpochMillis = 0L,
            lastAuthenticatedAtEpochMillis = 0L,
            provisioningState = ProvisioningState.READY,
        )
        identityStore.writeIdentity(identity)

        val errorBody = """{"detail": "Token is invalid or expired"}""".toResponseBody("application/json".toMediaType())
        fakeAuthApi.throwException = HttpException(Response.error<Unit>(401, errorBody))

        val result = coordinator.refreshIfNeededDetailed()
        assertTrue(result is HubTokenRefreshCoordinator.RefreshResult.AuthenticationFailure)
    }

    @Test
    fun `reconnect lifecycle - offline fails with transport error, restored connection succeeds`() = runTest {
        // Step 1: Token is expired while offline
        val expiredTime = System.currentTimeMillis() - 10_000L
        val identity = HubIdentity(
            deviceId = "dev", elderId = "elder", replicaId = "replica-1",
            accessToken = "old-access", refreshToken = "valid-refresh",
            tokenExpiresAtEpochMillis = expiredTime,
            backendUrl = "http://localhost",
            provisionedAtEpochMillis = 0L,
            lastAuthenticatedAtEpochMillis = 0L,
            provisioningState = ProvisioningState.READY,
        )
        identityStore.writeIdentity(identity)

        fakeAuthApi.throwException = ConnectException("Network unreachable")

        // Offline attempt
        val offlineResult = coordinator.refreshIfNeededDetailed()
        assertTrue(offlineResult is HubTokenRefreshCoordinator.RefreshResult.PureTransportFailure)
        assertEquals("old-access", identityStore.readIdentity()?.accessToken)

        // Step 2: Connection restored (clear exception)
        fakeAuthApi.throwException = null

        val onlineResult = coordinator.refreshIfNeededDetailed()
        assertEquals(HubTokenRefreshCoordinator.RefreshResult.Success, onlineResult)

        // Token must now be legitimately refreshed from server
        assertEquals("new-access-1", identityStore.readIdentity()?.accessToken)
        assertTrue((identityStore.readIdentity()?.tokenExpiresAtEpochMillis ?: 0L) > System.currentTimeMillis())
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
        var throwException: Exception? = null

        override suspend fun obtainToken(body: ir.sayda.yara.hub.network.dto.TokenRequestDto): TokenResponseDto {
            throw NotImplementedError()
        }

        override suspend fun refreshToken(body: TokenRefreshRequestDto): TokenResponseDto {
            throwException?.let { throw it }
            refreshCount++
            delay(10)
            return TokenResponseDto(
                access = "new-access-$refreshCount",
                refresh = "new-refresh-$refreshCount"
            )
        }
    }
}
