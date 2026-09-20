package ir.sayda.yara.hub.provisioning

import android.content.Context
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.every
import io.mockk.mockk
import ir.sayda.yara.hub.core.domain.model.ConnectivitySnapshot
import ir.sayda.yara.hub.core.domain.model.ConnectivityState
import ir.sayda.yara.hub.core.domain.model.HubIdentity
import ir.sayda.yara.hub.core.domain.model.ProvisioningState
import ir.sayda.yara.hub.core.domain.model.ProvisioningStatus
import ir.sayda.yara.hub.core.domain.repository.AuthRepository
import ir.sayda.yara.hub.core.domain.repository.ConnectivityRepository
import ir.sayda.yara.hub.core.domain.repository.ProvisioningRepository
import ir.sayda.yara.hub.core.provisioning.HubDeviceCredentialsProvider
import ir.sayda.yara.hub.core.provisioning.ProvisionCredential
import ir.sayda.yara.hub.core.result.AppResult
import ir.sayda.yara.hub.data.identity.HubIdentityStore
import ir.sayda.yara.hub.data.identity.SecureHubIdentityStore
import ir.sayda.yara.hub.data.provisioning.ProvisioningStateMachine
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Before
import org.junit.Test

class HubProvisioningCoordinatorTest {

    private val context: Context = mockk(relaxed = true)
    private val provisioningRepository: ProvisioningRepository = mockk(relaxed = true)
    private val authRepository: AuthRepository = mockk(relaxed = true)
    private val connectivityRepository: ConnectivityRepository = mockk(relaxed = true)
    private val identityStore: SecureHubIdentityStore = mockk(relaxed = true)
    private val stateMachine = ProvisioningStateMachine()
    private val credentialsProvider: HubDeviceCredentialsProvider = mockk(relaxed = true)
    private val deviceModelCode = object : HubDeviceModelCode {
        override val value: String = "YARA-HUB-TEST"
    }

    private lateinit var coordinator: HubProvisioningCoordinator

    private val storedProvisioning = HubIdentityStore.StoredProvisioning(
        deviceId = "dev-123",
        replicaId = "rep-123",
        elderId = "elder-123",
        backendUrl = "http://backend.test",
        provisionedAtEpochMillis = 1000L,
        lastAuthenticatedAtEpochMillis = 1000L,
        provisioningState = ProvisioningState.ERROR,
    )

    private val dummyIdentity = HubIdentity(
        deviceId = "dev-123",
        replicaId = "rep-123",
        elderId = "elder-123",
        accessToken = "access",
        refreshToken = "refresh",
        tokenExpiresAtEpochMillis = 9999999L,
        backendUrl = "http://backend.test",
        provisionedAtEpochMillis = 1000L,
        lastAuthenticatedAtEpochMillis = 2000L,
        provisioningState = ProvisioningState.READY,
    )

    @Before
    fun setup() {
        every { connectivityRepository.observeConnectivity() } returns flowOf(
            ConnectivitySnapshot(state = ConnectivityState.CONNECTED, isBackendReachable = true)
        )
        every { identityStore.readProvisioning() } returns storedProvisioning

        coordinator = HubProvisioningCoordinator(
            context = context,
            provisioningRepository = provisioningRepository,
            authRepository = authRepository,
            connectivityRepository = connectivityRepository,
            identityStore = identityStore,
            stateMachine = stateMachine,
            credentialsProvider = credentialsProvider,
            deviceModelCode = deviceModelCode,
        )
    }

    @Test
    fun startupFlow_inErrorState_automaticallyAuthenticatesWhenCredentialsExist() = runBlocking {
        stateMachine.transitionTo(ProvisioningState.ERROR)
        every { credentialsProvider.credentials() } returns ProvisionCredential(phone = "09120000000", password = "password123")
        coEvery { provisioningRepository.restoreProvisioning() } returns AppResult.Success(
            ProvisioningStatus(state = ProvisioningState.ERROR, deviceId = "dev-123")
        )
        coEvery { provisioningRepository.authenticate("dev-123", "09120000000", "password123") } coAnswers {
            stateMachine.transitionTo(ProvisioningState.READY)
            AppResult.Success(dummyIdentity)
        }

        coordinator.runStartupFlow()

        coVerify(exactly = 1) {
            provisioningRepository.authenticate("dev-123", "09120000000", "password123")
        }
        assertEquals(ProvisioningState.READY, stateMachine.currentState())
    }

    @Test
    fun startupFlow_inErrorState_transitionsToRegisteredWhenNoCredentialsExist() = runBlocking {
        stateMachine.transitionTo(ProvisioningState.ERROR)
        every { credentialsProvider.credentials() } returns null
        coEvery { provisioningRepository.restoreProvisioning() } returns AppResult.Success(
            ProvisioningStatus(state = ProvisioningState.ERROR, deviceId = "dev-123")
        )

        coordinator.runStartupFlow()

        coVerify(exactly = 0) {
            provisioningRepository.authenticate(any(), any(), any())
        }
        assertEquals(ProvisioningState.REGISTERED, stateMachine.currentState())
    }

    @Test
    fun startupFlow_inRegisteredState_automaticallyAuthenticatesIfCredentialsPresent() = runBlocking {
        stateMachine.transitionTo(ProvisioningState.REGISTERED)
        every { credentialsProvider.credentials() } returns ProvisionCredential(phone = "09120000000", password = "password123")
        coEvery { provisioningRepository.restoreProvisioning() } returns AppResult.Success(
            ProvisioningStatus(state = ProvisioningState.REGISTERED, deviceId = "dev-123")
        )
        coEvery { provisioningRepository.authenticate("dev-123", "09120000000", "password123") } coAnswers {
            stateMachine.transitionTo(ProvisioningState.READY)
            AppResult.Success(dummyIdentity)
        }

        coordinator.runStartupFlow()

        coVerify(exactly = 1) {
            provisioningRepository.authenticate("dev-123", "09120000000", "password123")
        }
        assertEquals(ProvisioningState.READY, stateMachine.currentState())
    }

    @Test
    fun concurrentStartupAndErrorRecovery_serializedWithoutOverlappingCalls() = runBlocking {
        stateMachine.transitionTo(ProvisioningState.ERROR)
        every { credentialsProvider.credentials() } returns ProvisionCredential(phone = "09120000000", password = "password123")
        coEvery { provisioningRepository.restoreProvisioning() } coAnswers {
            kotlinx.coroutines.delay(50)
            ProvisioningStatus(state = ProvisioningState.ERROR, deviceId = "dev-123").let { AppResult.Success(it) }
        }
        coEvery { provisioningRepository.authenticate(any(), any(), any()) } coAnswers {
            kotlinx.coroutines.delay(50)
            stateMachine.transitionTo(ProvisioningState.READY)
            AppResult.Success(dummyIdentity)
        }

        coroutineScope {
            val job1 = async { coordinator.runStartupFlow() }
            val job2 = async {
                delay(10)
                coordinator.runStartupFlow()
            }
            awaitAll(job1, job2)
        }

        coVerify(exactly = 1) {
            provisioningRepository.authenticate("dev-123", "09120000000", "password123")
        }
        assertEquals(ProvisioningState.READY, stateMachine.currentState())
    }

    @OptIn(kotlinx.coroutines.ExperimentalCoroutinesApi::class)
    @Test
    fun periodicBackstop_inErrorStateWithoutConnectivityChange_recoversWhenBackendOnline() = kotlinx.coroutines.test.runTest {
        stateMachine.transitionTo(ProvisioningState.ERROR)
        every { credentialsProvider.credentials() } returns ProvisionCredential(phone = "09120000000", password = "password123")
        coEvery { provisioningRepository.restoreProvisioning() } returns AppResult.Success(
            ProvisioningStatus(state = ProvisioningState.ERROR, deviceId = "dev-123")
        )

        var attempts = 0
        coEvery { provisioningRepository.authenticate(any(), any(), any()) } coAnswers {
            attempts++
            if (attempts < 2) {
                // Outage: authentication fails, state stays ERROR
                stateMachine.transitionTo(ProvisioningState.ERROR)
                AppResult.Error(RuntimeException("Backend unreachable"))
            } else {
                // Backend comes online: authentication succeeds, state becomes READY
                stateMachine.transitionTo(ProvisioningState.READY)
                AppResult.Success(dummyIdentity)
            }
        }

        coordinator.start(backgroundScope)

        // At startup, runStartupFlow attempts authenticate -> fails (attempt 1)
        testScheduler.advanceTimeBy(100L)
        assertEquals(1, attempts)
        assertEquals(ProvisioningState.ERROR, stateMachine.currentState())

        // Connectivity does NOT flap. Wait for periodic backstop interval (60s)
        testScheduler.advanceTimeBy(60_500L)

        // The periodic backstop fires, authenticates successfully, and state transitions to READY
        assertEquals(2, attempts)
        assertEquals(ProvisioningState.READY, stateMachine.currentState())
    }
}
