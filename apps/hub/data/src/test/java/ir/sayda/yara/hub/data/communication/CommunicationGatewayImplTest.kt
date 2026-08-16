package ir.sayda.yara.hub.data.communication

import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.mockk
import io.mockk.any
import ir.sayda.yara.hub.core.communication.ActiveCallExistsException
import ir.sayda.yara.hub.core.result.AppResult
import ir.sayda.yara.hub.network.api.CommunicationApi
import ir.sayda.yara.hub.network.dto.CallJoinResponseDto
import ir.sayda.yara.hub.network.dto.CallStartRequestDto
import kotlinx.coroutines.test.runTest
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.ResponseBody.Companion.toResponseBody
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import retrofit2.HttpException
import retrofit2.Response

class CommunicationGatewayImplTest {

    @Test
    fun startCallMapsOpaqueJoinCredentials() = runTest {
        val api = mockk<CommunicationApi>()
        coEvery { api.startCall(any()) } returns CallJoinResponseDto(
            sessionId = "session-1",
            joinToken = "opaque-token",
            expiresAt = "2026-08-16T08:00:00Z",
        )
        val gateway = CommunicationGatewayImpl(api)

        val result = gateway.startCall("elder-1", "VOICE", "contact-1")

        assertTrue(result is AppResult.Success)
        val session = (result as AppResult.Success).data
        assertEquals("session-1", session.sessionId)
        assertEquals("opaque-token", session.joinToken)
        coVerify {
            api.startCall(
                CallStartRequestDto(
                    elderId = "elder-1",
                    channel = "VOICE",
                    recipientContactId = "contact-1",
                ),
            )
        }
    }

    @Test
    fun startCallMapsConflictToActiveCallExists() = runTest {
        val api = mockk<CommunicationApi>()
        coEvery { api.startCall(any()) } throws httpException(409)
        val gateway = CommunicationGatewayImpl(api)

        val result = gateway.startCall("elder-1", "VOICE", "contact-1")

        assertTrue(result is AppResult.Error)
        assertTrue((result as AppResult.Error).exception is ActiveCallExistsException)
    }

    @Test
    fun parseExpiresAtReadsIso8601() {
        val expected = java.time.Instant.parse("2026-08-16T08:00:00Z").toEpochMilli()
        val millis = parseExpiresAt("2026-08-16T08:00:00Z", fallbackNow = 0L)
        assertEquals(expected, millis)
    }

    private fun httpException(code: Int): HttpException {
        val body = "{}".toResponseBody("application/json".toMediaType())
        return HttpException(Response.error<Unit>(code, body))
    }
}
