package ir.sayda.yara.hub.runtime.communication

import ir.sayda.yara.hub.core.communication.CallMediaEvent
import ir.sayda.yara.hub.core.communication.SkyroomClient
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.asSharedFlow

internal class FakeSkyroomClient : SkyroomClient {
    val joinedUrls = mutableListOf<String>()
    val commands = mutableListOf<String>()
    private val events = MutableSharedFlow<CallMediaEvent>(replay = 1, extraBufferCapacity = 16)

    override suspend fun join(loginUrl: String) {
        joinedUrls += loginUrl
        commands += "join"
        events.tryEmit(CallMediaEvent.Joined)
    }

    override suspend fun leave() {
        commands += "leave"
        events.tryEmit(CallMediaEvent.Left)
    }

    override suspend fun mute() {
        commands += "mute"
    }

    override suspend fun unmute() {
        commands += "unmute"
    }

    override suspend fun cameraOn() {
        commands += "cameraOn"
    }

    override suspend fun cameraOff() {
        commands += "cameraOff"
    }

    override suspend fun speaker() {
        commands += "speaker"
    }

    override fun observeEvents(): Flow<CallMediaEvent> = events.asSharedFlow()

    fun emit(event: CallMediaEvent) {
        events.tryEmit(event)
    }
}
