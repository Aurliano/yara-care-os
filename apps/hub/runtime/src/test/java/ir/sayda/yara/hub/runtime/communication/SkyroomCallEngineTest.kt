package ir.sayda.yara.hub.runtime.communication

import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class SkyroomCallEngineTest {

    @Test
    fun joinForwardsLoginUrlAndDoesNotCallRest() = runTest {
        val client = FakeSkyroomClient()
        val engine = SkyroomCallEngine(client)

        engine.join("https://example.test/join/opaque")
        engine.mute()
        engine.unmute()
        engine.cameraOn()
        engine.cameraOff()
        engine.speaker()
        engine.leave()

        assertEquals(listOf("https://example.test/join/opaque"), client.joinedUrls)
        assertEquals(
            listOf("join", "mute", "unmute", "cameraOn", "cameraOff", "speaker", "leave"),
            client.commands,
        )
        assertTrue(client.joinedUrls.none { it.contains("skyroom/api") })
        assertTrue(client.joinedUrls.none { it.contains("apikey") })
    }

    @Test
    fun joinRejectsBlankLoginUrl() = runTest {
        val thrown = runCatching { SkyroomCallEngine(FakeSkyroomClient()).join("  ") }.exceptionOrNull()
        assertTrue(thrown is IllegalArgumentException)
    }
}
