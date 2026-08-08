package ir.sayda.yara.hub.data.provisioning

import ir.sayda.yara.hub.core.domain.model.ProvisioningState
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ProvisioningStateMachine @Inject constructor() {
    private val state = MutableStateFlow(ProvisioningState.UNPROVISIONED)
    private val lastError = MutableStateFlow<String?>(null)

    fun observeState(): Flow<ProvisioningState> = state.asStateFlow()

    fun observeError(): Flow<String?> = lastError.asStateFlow()

    fun currentState(): ProvisioningState = state.value

    fun currentError(): String? = lastError.value

    fun transitionTo(next: ProvisioningState, errorMessage: String? = null) {
        state.value = next
        lastError.value = errorMessage
    }

    fun restore(stateValue: ProvisioningState, errorMessage: String? = null) {
        state.update { stateValue }
        lastError.value = errorMessage
    }
}
