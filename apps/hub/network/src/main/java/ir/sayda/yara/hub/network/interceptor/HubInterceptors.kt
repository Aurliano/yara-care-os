package ir.sayda.yara.hub.network.interceptor

import ir.sayda.yara.hub.network.identity.CorrelationIdProvider
import ir.sayda.yara.hub.network.identity.ReplicaIdentityProvider
import okhttp3.Interceptor
import okhttp3.Response

class AuthInterceptor(
    private val identityProvider: ReplicaIdentityProvider,
) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val token = identityProvider.accessToken()
        val requestBuilder = chain.request().newBuilder()
        if (!token.isNullOrBlank()) {
            requestBuilder.header("Authorization", "Bearer $token")
        }
        return chain.proceed(requestBuilder.build())
    }
}

class HubHeadersInterceptor(
    private val identityProvider: ReplicaIdentityProvider,
    private val correlationIdProvider: CorrelationIdProvider,
) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val requestBuilder = chain.request().newBuilder()
            .header("X-Correlation-ID", correlationIdProvider.next())
        identityProvider.replicaId()?.let { requestBuilder.header("X-Replica-ID", it) }
        identityProvider.deviceId()?.let { requestBuilder.header("X-Device-ID", it) }
        return chain.proceed(requestBuilder.build())
    }
}
