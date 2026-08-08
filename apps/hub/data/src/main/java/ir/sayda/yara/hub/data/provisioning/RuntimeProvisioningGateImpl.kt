package ir.sayda.yara.hub.data.provisioning

import ir.sayda.yara.hub.core.domain.model.ProvisioningState
import ir.sayda.yara.hub.core.domain.repository.AuthRepository
import ir.sayda.yara.hub.core.provisioning.RuntimeProvisioningGate
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class RuntimeProvisioningGateImpl @Inject constructor(
    private val stateMachine: ProvisioningStateMachine,
    private val authRepository: AuthRepository,
) : RuntimeProvisioningGate {

    override fun isRuntimeAllowed(): Boolean =
        stateMachine.currentState() == ProvisioningState.READY

    override suspend fun requireRuntimeReady(): Boolean {
        if (stateMachine.currentState() != ProvisioningState.READY) {
            return false
        }
        val identity = authRepository.getIdentity() ?: return false
        return identity.provisioningState == ProvisioningState.READY &&
            identity.deviceId.isNotBlank() &&
            identity.replicaId.isNotBlank() &&
            identity.accessToken.isNotBlank()
    }

    override fun observeRuntimeAllowed(): Flow<Boolean> =
        combine(
            stateMachine.observeState(),
            authRepository.observeIdentity(),
        ) { state, identity ->
            state == ProvisioningState.READY &&
                identity != null &&
                identity.provisioningState == ProvisioningState.READY &&
                identity.deviceId.isNotBlank() &&
                identity.replicaId.isNotBlank() &&
                identity.accessToken.isNotBlank()
        }.distinctUntilChanged()
}
