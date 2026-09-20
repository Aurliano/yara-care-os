package ir.sayda.yara.hub.identity

import dagger.Lazy
import io.mockk.mockk
import ir.sayda.yara.hub.core.domain.model.ConnectivityState
import ir.sayda.yara.hub.core.domain.model.HomeRuntimeSnapshot
import ir.sayda.yara.hub.core.domain.model.HubIdentity
import ir.sayda.yara.hub.core.domain.model.ProvisioningState
import ir.sayda.yara.hub.core.domain.repository.ProvisioningRepository
import ir.sayda.yara.hub.core.provisioning.HubDeviceCredentialsProvider
import ir.sayda.yara.hub.core.provisioning.ProvisionCredential
import ir.sayda.yara.hub.core.result.AppResult
import ir.sayda.yara.hub.data.identity.AuthRepositoryImpl
import ir.sayda.yara.hub.data.identity.DataStoreReplicaIdentityProvider
import ir.sayda.yara.hub.data.identity.HubIdentityStore
import ir.sayda.yara.hub.data.identity.HubTokenRefreshCoordinator
import ir.sayda.yara.hub.data.identity.IdentitySnapshotHolder
import ir.sayda.yara.hub.data.identity.SecureHubIdentityStore
import ir.sayda.yara.hub.data.provisioning.ProvisioningRepositoryImpl
import ir.sayda.yara.hub.data.provisioning.ProvisioningStateMachine
import ir.sayda.yara.hub.data.provisioning.RuntimeProvisioningGateImpl
import ir.sayda.yara.hub.feature.home.presentation.needsCaregiverLogin
import ir.sayda.yara.hub.network.api.AuthApi
import ir.sayda.yara.hub.network.api.ProvisioningApi
import ir.sayda.yara.hub.network.dto.TokenRefreshRequestDto
import ir.sayda.yara.hub.network.dto.TokenResponseDto
import ir.sayda.yara.hub.network.identity.CorrelationIdProvider
import ir.sayda.yara.hub.sync.ReplicaStateInitializer
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import java.net.ConnectException

class OfflineTokenRefreshIntegrationTest {

    private val snapshotHolder = IdentitySnapshotHolder()
    private val fakeSecureStore = FakeIdentityStore()
    private val identityStore = DataStoreReplicaIdentityProvider(fakeSecureStore, snapshotHolder)
    private val fakeAuthApi = FakeAuthApi()
    private val correlationIdProvider = object : CorrelationIdProvider {
        override fun next(): String = "test-corr-id"
    }

    private val tokenRefreshCoordinator = HubTokenRefreshCoordinator(
        identityStore = identityStore,
        authApi = fakeAuthApi,
        correlationIdProvider = correlationIdProvider,
    )

    private val stateMachine = ProvisioningStateMachine()
    private val credentialsProvider = object : HubDeviceCredentialsProvider {
        override fun credentials(): ProvisionCredential = ProvisionCredential("09121111111", "pass123")
    }

    private val provisioningApi = mockk<ProvisioningApi>(relaxed = true)
    private val replicaStateInitializer = mockk<ReplicaStateInitializer>(relaxed = true)
    private val mockSecureIdentityStore = mockk<SecureHubIdentityStore>(relaxed = true)

    private lateinit var authRepository: AuthRepositoryImpl
    private lateinit var provisioningRepository: ProvisioningRepositoryImpl

    private val provisioningRepositoryLazy = Lazy<ProvisioningRepository> { provisioningRepository }

    init {
        provisioningRepository = ProvisioningRepositoryImpl(
            provisioningApi = provisioningApi,
            authRepository = object : ir.sayda.yara.hub.core.domain.repository.AuthRepository {
                override suspend fun getIdentity(): HubIdentity? = authRepository.getIdentity()
                override suspend fun saveIdentity(identity: HubIdentity) = authRepository.saveIdentity(identity)
                override suspend fun clearIdentity() = authRepository.clearIdentity()
                override suspend fun login(phone: String, password: String): AppResult<HubIdentity> = authRepository.login(phone, password)
                override suspend fun logout(): AppResult<Unit> = authRepository.logout()
                override suspend fun refreshToken(): AppResult<HubIdentity> = authRepository.refreshToken()
                override suspend fun refreshTokenIfNeeded(): AppResult<HubIdentity> = authRepository.refreshTokenIfNeeded()
                override fun observeIdentity() = authRepository.observeIdentity()
            },
            identityStore = mockSecureIdentityStore,
            stateMachine = stateMachine,
            correlationIdProvider = correlationIdProvider,
            backendUrl = "http://localhost:8000/api/v1/",
            replicaStateInitializer = replicaStateInitializer,
        )

        authRepository = AuthRepositoryImpl(
            identityStore = identityStore,
            authApi = fakeAuthApi,
            stateMachine = stateMachine,
            tokenRefreshCoordinator = tokenRefreshCoordinator,
            provisioningRepository = provisioningRepositoryLazy,
            deviceCredentialsProvider = credentialsProvider,
        )
    }

    private val provisioningGate by lazy {
        RuntimeProvisioningGateImpl(
            stateMachine = stateMachine,
            authRepository = authRepository,
        )
    }

    @org.junit.Before
    fun setUp() {
        io.mockk.mockkObject(ir.sayda.yara.hub.network.logging.HubNetworkLogger)
        io.mockk.every { ir.sayda.yara.hub.network.logging.HubNetworkLogger.authenticationRefresh(any(), any()) } returns Unit
    }

    @org.junit.After
    fun tearDown() {
        io.mockk.unmockkObject(ir.sayda.yara.hub.network.logging.HubNetworkLogger)
    }

    @Test
    fun testEndToEnd_offlineTokenExpiry_preservesReadyState_keepsGateOpen_andRefreshesOnReconnect() = runTest {
        val now = System.currentTimeMillis()
        val expiredTime = now - 60_000L

        // 1. Initial State: Device is provisioned and in READY state
        val initialIdentity = HubIdentity(
            deviceId = "dev-abc-123",
            replicaId = "replica-xyz-456",
            elderId = "elder-789",
            accessToken = "expired-jwt-access-token",
            refreshToken = "valid-jwt-refresh-token",
            tokenExpiresAtEpochMillis = expiredTime,
            backendUrl = "http://10.254.230.230:8000/api/v1/",
            provisionedAtEpochMillis = now - 86400000L,
            lastAuthenticatedAtEpochMillis = now - 86400000L,
            provisioningState = ProvisioningState.READY,
            elderDisplayName = "مادر جان",
        )
        fakeSecureStore.write(initialIdentity)
        identityStore.writeIdentity(initialIdentity)
        stateMachine.transitionTo(ProvisioningState.READY)

        // Verify pre-conditions
        assertEquals(ProvisioningState.READY, stateMachine.currentState())
        assertTrue(provisioningGate.requireRuntimeReady())

        // 2. Offline Event: Network is down (ConnectException)
        fakeAuthApi.throwException = ConnectException("Failed to connect to /10.254.230.230:8000")

        // 3. Trigger: refreshTokenIfNeeded() runs (e.g. from background worker or startup)
        val refreshResult = authRepository.refreshTokenIfNeeded()

        // 4. Assert: Local offline resilience (Conditions 1 & 3)
        assertTrue("refreshTokenIfNeeded must succeed with current identity offline", refreshResult is AppResult.Success)
        assertEquals("State machine must NOT be poisoned into ERROR state", ProvisioningState.READY, stateMachine.currentState())
        assertTrue("Runtime gate must remain OPEN so offline medication reminders can fire", provisioningGate.requireRuntimeReady())

        // Check presentation layer:
        val homeSnapshot = HomeRuntimeSnapshot(
            elderDisplayName = "مادر جان",
            activeExecutions = emptyList(),
            todayReminders = emptyList(),
            priorityContacts = emptyList(),
            replicaHealth = "HEALTHY",
            runtimeHealth = "RUNNING",
            lastSyncEpochMillis = null,
            isOnline = false,
            provisioningState = stateMachine.currentState(),
            connectivityState = ConnectivityState.DISCONNECTED,
            deviceId = initialIdentity.deviceId,
            replicaId = initialIdentity.replicaId,
            isAuthenticated = true,
        )
        assertFalse("Elder screen must NOT show Caregiver Login while offline", homeSnapshot.needsCaregiverLogin())

        // 5. Post-Reconnect Verification (Condition 2)
        // Network connection is restored:
        fakeAuthApi.throwException = null

        val reconnectRefreshResult = authRepository.refreshTokenIfNeeded()

        assertTrue(reconnectRefreshResult is AppResult.Success)
        val updatedIdentity = (reconnectRefreshResult as AppResult.Success).data
        assertEquals("new-access-1", updatedIdentity.accessToken)
        assertTrue("Token expiry must be updated into the future upon reconnect", updatedIdentity.tokenExpiresAtEpochMillis > now)
        assertEquals(ProvisioningState.READY, stateMachine.currentState())
        assertTrue(provisioningGate.requireRuntimeReady())
    }

    private class FakeIdentityStore : HubIdentityStore {
        private var stored: HubIdentityStore.StoredHubIdentity? = null

        override fun read(): HubIdentityStore.StoredHubIdentity? = stored

        override fun readProvisioning(): HubIdentityStore.StoredProvisioning? {
            val s = stored ?: return null
            return HubIdentityStore.StoredProvisioning(
                deviceId = s.deviceId,
                replicaId = s.replicaId,
                elderId = s.elderId,
                backendUrl = s.backendUrl,
                provisionedAtEpochMillis = s.provisionedAtEpochMillis,
                lastAuthenticatedAtEpochMillis = s.lastAuthenticatedAtEpochMillis,
                provisioningState = s.provisioningState,
                elderDisplayName = "مادر جان",
            )
        }

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
                elderDisplayName = identity.elderDisplayName,
            )
        }

        override fun clear() {
            stored = null
        }
    }

    private class FakeAuthApi : AuthApi {
        var refreshCount = 0
        var throwException: Exception? = null

        override suspend fun obtainToken(body: ir.sayda.yara.hub.network.dto.TokenRequestDto): TokenResponseDto {
            throw NotImplementedError()
        }

        override suspend fun refreshToken(body: TokenRefreshRequestDto): TokenResponseDto {
            throwException?.let { throw it }
            refreshCount++
            return TokenResponseDto(
                access = "new-access-$refreshCount",
                refresh = "new-refresh-$refreshCount"
            )
        }
    }
}
