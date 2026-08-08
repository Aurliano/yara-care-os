package ir.sayda.yara.hub.core.domain.model

enum class ProvisioningState {
    UNPROVISIONED,
    REGISTERING,
    REGISTERED,
    AUTHENTICATING,
    READY,
    ERROR,
}

enum class ConnectivityState {
    DISCONNECTED,
    CONNECTING,
    CONNECTED,
    AUTHENTICATED,
    PROVISIONED,
}

data class ProvisioningStatus(
    val state: ProvisioningState,
    val deviceId: String? = null,
    val replicaId: String? = null,
    val elderId: String? = null,
    val backendUrl: String? = null,
    val provisionedAtEpochMillis: Long? = null,
    val lastAuthenticatedAtEpochMillis: Long? = null,
    val lastErrorMessage: String? = null,
)

data class ConnectivitySnapshot(
    val state: ConnectivityState,
    val connectionType: String = "UNKNOWN",
    val isBackendReachable: Boolean = false,
)
