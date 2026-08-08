package ir.sayda.yara.hub.network.interceptor

import ir.sayda.yara.hub.network.auth.TokenRefreshHandler
import ir.sayda.yara.hub.network.identity.ReplicaIdentityProvider
import okhttp3.Authenticator
import okhttp3.Request
import okhttp3.Response
import okhttp3.Route
import java.util.concurrent.atomic.AtomicBoolean
import javax.inject.Inject
import dagger.Lazy

class TokenAuthenticator @Inject constructor(
    private val identityProvider: ReplicaIdentityProvider,
    private val tokenRefreshHandler: Lazy<TokenRefreshHandler>,
) : Authenticator {
  private val refreshInProgress = AtomicBoolean(false)

    override fun authenticate(route: Route?, response: Response): Request? {
        if (responseCount(response) >= 2) {
            return null
        }
        if (response.request.header(RETRY_HEADER) != null) {
            return null
        }
        if (!refreshInProgress.compareAndSet(false, true)) {
            return null
        }
        return try {
            val refreshed = kotlinx.coroutines.runBlocking {
                tokenRefreshHandler.get().refreshAccessToken()
            }
            if (!refreshed) {
                return null
            }
            val token = identityProvider.accessToken() ?: return null
            response.request.newBuilder()
                .header("Authorization", "Bearer $token")
                .header(RETRY_HEADER, "1")
                .build()
        } finally {
            refreshInProgress.set(false)
        }
    }

    private fun responseCount(response: Response): Int {
        var count = 1
        var prior = response.priorResponse
        while (prior != null) {
            count++
            prior = prior.priorResponse
        }
        return count
    }

    companion object {
        private const val RETRY_HEADER = "X-Auth-Retry"
    }
}
