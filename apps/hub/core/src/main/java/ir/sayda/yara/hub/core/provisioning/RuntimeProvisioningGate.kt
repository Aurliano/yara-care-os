package ir.sayda.yara.hub.core.provisioning

import kotlinx.coroutines.flow.Flow

/**
 * Defense-in-depth gate: runtime, sync, and integration must not run until provisioning is READY.
 */
interface RuntimeProvisioningGate {
    /** Fast check based on persisted provisioning state (safe from network callbacks). */
    fun isRuntimeAllowed(): Boolean

    /** Strict check: READY state plus device, replica, and JWT present. */
    suspend fun requireRuntimeReady(): Boolean

    fun observeRuntimeAllowed(): Flow<Boolean>
}
