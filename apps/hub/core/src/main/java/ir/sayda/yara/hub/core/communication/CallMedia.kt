package ir.sayda.yara.hub.core.communication

import kotlinx.coroutines.flow.Flow

enum class CallDirection {
    Outgoing,
    Incoming,
}

sealed class CallMediaEvent {
    data class Joined(val sessionId: String? = null) : CallMediaEvent()
    data class Left(val sessionId: String? = null) : CallMediaEvent()
    data class ConnectionLost(val sessionId: String? = null) : CallMediaEvent()
    data class ConnectionRestored(val sessionId: String? = null) : CallMediaEvent()
}

/**
 * Vendor media adapter. CommunicationRuntime owns call policy.
 * Implementations must not call vendor REST APIs or hold an API key.
 */
interface CallMediaEngine {
    suspend fun join(loginUrl: String)
    suspend fun leave()
    suspend fun mute()
    suspend fun unmute()
    suspend fun cameraOn()
    suspend fun cameraOff()
    suspend fun speaker()
    fun observeEvents(): Flow<CallMediaEvent>
}

/** Thin Skyroom client used only to consume a Backend-issued login URL. */
interface SkyroomClient {
    suspend fun join(loginUrl: String)
    suspend fun leave()
    suspend fun mute()
    suspend fun unmute()
    suspend fun cameraOn()
    suspend fun cameraOff()
    suspend fun speaker()
    fun observeEvents(): Flow<CallMediaEvent>
}

/** LiveKit client used to consume a Backend-issued LiveKit JWT token. */
interface LivekitClient {
    suspend fun join(loginUrl: String)
    suspend fun leave()
    suspend fun mute()
    suspend fun unmute()
    suspend fun cameraOn()
    suspend fun cameraOff()
    suspend fun speaker()
    fun observeEvents(): Flow<CallMediaEvent>
}

