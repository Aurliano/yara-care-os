package ir.sayda.yara.hub.core.domain.model

enum class CallRuntimeState {
    Idle,
    Connecting,
    Connected,
    ConnectionLost,
    Reconnecting,
    Finished,
}

fun CallRuntimeState.isActive(): Boolean =
    this == CallRuntimeState.Connecting ||
        this == CallRuntimeState.Connected ||
        this == CallRuntimeState.ConnectionLost ||
        this == CallRuntimeState.Reconnecting

data class CallSession(
    val sessionId: String,
    val elderId: String,
    val channel: String,
    val recipientContactId: String,
    val runtimeState: CallRuntimeState,
    val joinToken: String,
    val expiresAtEpochMillis: Long,
    val updatedAtEpochMillis: Long,
    val direction: ir.sayda.yara.hub.core.communication.CallDirection =
        ir.sayda.yara.hub.core.communication.CallDirection.Outgoing,
)
