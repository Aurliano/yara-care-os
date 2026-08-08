package ir.sayda.yara.hub.data.provisioning

import io.mockk.coEvery
import io.mockk.every
import io.mockk.mockk
import ir.sayda.yara.hub.core.domain.model.HubIdentity
import ir.sayda.yara.hub.core.domain.model.ProvisioningState
import ir.sayda.yara.hub.core.domain.repository.AuthRepository
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class RuntimeProvisioningGateImplTest {
    private val stateMachine = ProvisioningStateMachine()
    private val authRepository = mockk<AuthRepository>()

    @Test
    fun requireRuntimeReady_falseWhenStateNotReady() = runTest {
        stateMachine.transitionTo(ProvisioningState.REGISTERED)
        val gate = RuntimeProvisioningGateImpl(stateMachine, authRepository)

        assertFalse(gate.requireRuntimeReady())
    }

    @Test
    fun requireRuntimeReady_trueWhenReadyWithIdentity() = runTest {
        stateMachine.transitionTo(ProvisioningState.READY)
        every { authRepository.observeIdentity() } returns flowOf(sampleIdentity())
        coEvery { authRepository.getIdentity() } returns sampleIdentity()
        val gate = RuntimeProvisioningGateImpl(stateMachine, authRepository)

        assertTrue(gate.requireRuntimeReady())
    }

    private fun sampleIdentity() = HubIdentity(
        deviceId = "device-1",
        replicaId = "replica-1",
        elderId = null,
        accessToken = "access",
        refreshToken = "refresh",
        tokenExpiresAtEpochMillis = 9_999_999L,
        backendUrl = "http://localhost/api/v1/",
        provisionedAtEpochMillis = 1L,
        lastAuthenticatedAtEpochMillis = 1L,
        provisioningState = ProvisioningState.READY,
    )
}
