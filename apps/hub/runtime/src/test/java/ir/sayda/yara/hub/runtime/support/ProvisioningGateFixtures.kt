package ir.sayda.yara.hub.runtime.support

import ir.sayda.yara.hub.core.provisioning.RuntimeProvisioningGate
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flowOf

internal class AlwaysAllowedProvisioningGate : RuntimeProvisioningGate {
    override fun isRuntimeAllowed(): Boolean = true
    override suspend fun requireRuntimeReady(): Boolean = true
    override fun observeRuntimeAllowed(): Flow<Boolean> = flowOf(true)
}

internal class DeniedProvisioningGate : RuntimeProvisioningGate {
    override fun isRuntimeAllowed(): Boolean = false
    override suspend fun requireRuntimeReady(): Boolean = false
    override fun observeRuntimeAllowed(): Flow<Boolean> = flowOf(false)
}
