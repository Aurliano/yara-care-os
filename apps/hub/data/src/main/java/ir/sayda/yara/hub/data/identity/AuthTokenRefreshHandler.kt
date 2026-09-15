package ir.sayda.yara.hub.data.identity

import ir.sayda.yara.hub.network.auth.TokenRefreshHandler
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AuthTokenRefreshHandler @Inject constructor(
    private val coordinator: HubTokenRefreshCoordinator,
) : TokenRefreshHandler {
    override suspend fun refreshAccessToken(failedAccessToken: String?): Boolean = coordinator.refresh(failedAccessToken = failedAccessToken, force = true)

    override suspend fun refreshAndGetAccessToken(failedAccessToken: String?): String? =
        coordinator.refreshAndGetAccessToken(failedAccessToken = failedAccessToken, force = true)
}
