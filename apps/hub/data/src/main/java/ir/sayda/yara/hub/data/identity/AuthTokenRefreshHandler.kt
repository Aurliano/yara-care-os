package ir.sayda.yara.hub.data.identity

import ir.sayda.yara.hub.network.auth.TokenRefreshHandler
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AuthTokenRefreshHandler @Inject constructor(
    private val coordinator: HubTokenRefreshCoordinator,
) : TokenRefreshHandler {
    override suspend fun refreshAccessToken(): Boolean = coordinator.refresh(force = true)

    override suspend fun refreshAndGetAccessToken(): String? =
        coordinator.refreshAndGetAccessToken(force = true)
}
