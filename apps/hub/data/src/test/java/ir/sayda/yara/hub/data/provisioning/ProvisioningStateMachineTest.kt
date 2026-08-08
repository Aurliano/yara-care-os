package ir.sayda.yara.hub.data.provisioning

import ir.sayda.yara.hub.core.domain.model.ProvisioningState
import org.junit.Assert.assertEquals
import org.junit.Test

class ProvisioningStateMachineTest {
    @Test
    fun transitionsFollowBackendDrivenStates() {
        val machine = ProvisioningStateMachine()
        machine.transitionTo(ProvisioningState.REGISTERING)
        machine.transitionTo(ProvisioningState.REGISTERED)
        machine.transitionTo(ProvisioningState.AUTHENTICATING)
        machine.transitionTo(ProvisioningState.READY)
        assertEquals(ProvisioningState.READY, machine.currentState())
    }

    @Test
    fun errorStatePreservesMessage() {
        val machine = ProvisioningStateMachine()
        machine.transitionTo(ProvisioningState.ERROR, "Network unavailable")
        assertEquals("Network unavailable", machine.currentError())
    }

    @Test
    fun restoreRecoversPersistedState() {
        val machine = ProvisioningStateMachine()
        machine.restore(ProvisioningState.REGISTERED)
        assertEquals(ProvisioningState.REGISTERED, machine.currentState())
    }
}
