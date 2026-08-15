package ir.sayda.yara.hub.network.interceptor

import ir.sayda.yara.hub.network.auth.TokenRefreshHandler
import okhttp3.Authenticator
import okhttp3.Request
import okhttp3.Response
import okhttp3.Route
import javax.inject.Inject
import dagger.Lazy

class TokenAuthenticator @Inject constructor(
    private val tokenRefreshHandler: Lazy<TokenRefreshHandler>,
) : Authenticator {
    override fun authenticate(route: Route?, response: Response): Request? {
        if (responseCount(response) >= 2) {
            return null
        }
        if (response.request.header(RETRY_HEADER) != null) {
            return null
        }
        val token = kotlinx.coroutines.runBlocking {
            tokenRefreshHandler.get().refreshAndGetAccessToken()
        } ?: return null
        return response.request.newBuilder()
            .header("Authorization", "Bearer $token")
            .header(RETRY_HEADER, "1")
            .build()
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
