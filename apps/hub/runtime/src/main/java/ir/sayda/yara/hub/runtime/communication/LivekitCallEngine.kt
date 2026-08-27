package ir.sayda.yara.hub.runtime.communication

import ir.sayda.yara.hub.core.communication.CallMediaEngine
import ir.sayda.yara.hub.core.communication.CallMediaEvent
import ir.sayda.yara.hub.core.communication.LivekitClient
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Thin LiveKit adapter conforming to [CallMediaEngine].
 * No session policy, no Backend calls, no REST.
 * [join] consumes the Backend-issued LiveKit JWT join token.
 */
@Singleton
class LivekitCallEngine @Inject constructor(
    private val client: LivekitClient,
) : CallMediaEngine {
    override suspend fun join(loginUrl: String) {
        require(loginUrl.isNotBlank()) { "joinToken is required" }
        client.join(loginUrl)
    }

    override suspend fun leave() = client.leave()

    override suspend fun mute() = client.mute()

    override suspend fun unmute() = client.unmute()

    override suspend fun cameraOn() = client.cameraOn()

    override suspend fun cameraOff() = client.cameraOff()

    override suspend fun speaker() = client.speaker()

    override fun observeEvents(): Flow<CallMediaEvent> = client.observeEvents()
}
