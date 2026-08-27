package ir.sayda.yara.hub.runtime.communication

import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class LivekitCallEngineTest {

    @Test
    fun joinForwardsTokenAndDoesNotCallRest() = runTest {
        val client = FakeLivekitClient()
        val engine = LivekitCallEngine(client)

        val sampleJwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.token"
        engine.join(sampleJwt)
        engine.mute()
        engine.unmute()
        engine.cameraOn()
        engine.cameraOff()
        engine.speaker()
        engine.leave()

        assertEquals(listOf(sampleJwt), client.joinedTokens)
        assertEquals(
            listOf("join", "mute", "unmute", "cameraOn", "cameraOff", "speaker", "leave"),
            client.commands,
        )
        assertTrue(client.joinedTokens.none { it.contains("skyroom/api") })
        assertTrue(client.joinedTokens.none { it.contains("apikey") })
    }

    @Test
    fun joinRejectsBlankToken() = runTest {
        val thrown = runCatching { LivekitCallEngine(FakeLivekitClient()).join("  ") }.exceptionOrNull()
        assertTrue(thrown is IllegalArgumentException)
    }
}
