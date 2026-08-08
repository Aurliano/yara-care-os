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
}
