package ir.sayda.yara.hub.core.communication

import kotlinx.coroutines.flow.Flow

enum class CallDirection {
    Outgoing,
    Incoming,
}

sealed class CallMediaEvent {
    data object Joined : CallMediaEvent()
    data object Left : CallMediaEvent()
    data object ConnectionLost : CallMediaEvent()
    data object ConnectionRestored : CallMediaEvent()
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
