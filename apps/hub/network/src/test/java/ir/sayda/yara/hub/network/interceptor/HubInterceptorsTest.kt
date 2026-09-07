package ir.sayda.yara.hub.network.interceptor

import io.mockk.every
import io.mockk.mockk
import ir.sayda.yara.hub.network.identity.CorrelationIdProvider
import ir.sayda.yara.hub.network.identity.ReplicaIdentityProvider
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.junit.Assert.assertEquals
import org.junit.Test

class HubInterceptorsTest {
  @Test
  fun authenticatedRequestIncludesRequiredHeaders() {
        val server = MockWebServer()
        server.enqueue(MockResponse().setResponseCode(200).setBody("{}"))
        server.start()

        val identityProvider = mockk<ReplicaIdentityProvider>()
        every { identityProvider.accessToken() } returns "access-token"
        every { identityProvider.replicaId() } returns "replica-1"
        every { identityProvider.deviceId() } returns "device-1"

        val correlationIdProvider = mockk<CorrelationIdProvider>()
        every { correlationIdProvider.next() } returns "corr-123"

        val client = OkHttpClient.Builder()
            .addInterceptor(HubHeadersInterceptor(identityProvider, correlationIdProvider))
            .addInterceptor(AuthInterceptor(identityProvider))
            .build()

        val request = Request.Builder().url(server.url("/test")).build()
        client.newCall(request).execute().close()

        val recorded = server.takeRequest()
        assertEquals("Bearer access-token", recorded.getHeader("Authorization"))
        assertEquals("replica-1", recorded.getHeader("X-Replica-ID"))
        assertEquals("device-1", recorded.getHeader("X-Device-ID"))
        assertEquals("corr-123", recorded.getHeader("X-Correlation-ID"))
        server.shutdown()
    }

    @Test
    fun testDeserializeMessageWithFloatDuration() {
        val jsonStr = """
        {
          "id": "11d25e32-174d-42b7-a7fc-1aacbd5aeac1",
          "elder_id": "84c884c8-37c3-4374-8bbd-c428555e31d2",
          "direction": "FAMILY_TO_HUB",
          "message_type": "VOICE",
          "body": "",
          "status": "SENT",
          "attachment": {
            "id": "001d7972-47d7-4d03-9569-02941dad5e0d",
            "media_type": "VOICE",
            "file_size": 43730,
            "mime_type": "audio/m4a",
            "duration_seconds": 2.0,
            "download_url": "/api/v1/media/001d7972-47d7-4d03-9569-02941dad5e0d/download/",
            "created_at": "2026-09-07T10:36:54.744563Z"
          }
        }
        """.trimIndent()
        val json = ir.sayda.yara.hub.network.di.NetworkModule.provideJson()
        val dto = json.decodeFromString<ir.sayda.yara.hub.network.dto.MessageResponseDto>(jsonStr)
        assertEquals("11d25e32-174d-42b7-a7fc-1aacbd5aeac1", dto.id)
    }
}
