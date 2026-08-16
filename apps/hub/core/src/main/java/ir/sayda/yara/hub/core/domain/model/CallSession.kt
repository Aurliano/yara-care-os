package ir.sayda.yara.hub.core.domain.model

enum class CallRuntimeState {
    Idle,
    Connecting,
    Connected,
    Finished,
}

fun CallRuntimeState.isActive(): Boolean =
    this == CallRuntimeState.Connecting || this == CallRuntimeState.Connected

data class CallSession(
    val sessionId: String,
    val elderId: String,
    val channel: String,
    val recipientContactId: String,
    val runtimeState: CallRuntimeState,
    val joinToken: String,
    val expiresAtEpochMillis: Long,
    val updatedAtEpochMillis: Long,
)
