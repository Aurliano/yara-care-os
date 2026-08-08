package ir.sayda.yara.hub.data.repository

import android.content.Context
import android.net.ConnectivityManager
import android.net.Network
import android.net.NetworkCapabilities
import android.net.NetworkRequest
import dagger.hilt.android.qualifiers.ApplicationContext
import ir.sayda.yara.hub.core.domain.model.ConnectivitySnapshot
import ir.sayda.yara.hub.core.domain.model.ConnectivityState
import ir.sayda.yara.hub.core.domain.model.HubIdentity
import ir.sayda.yara.hub.core.domain.model.ProvisioningState
import ir.sayda.yara.hub.core.domain.repository.AuthRepository
import ir.sayda.yara.hub.core.domain.repository.ConnectivityRepository
import ir.sayda.yara.hub.core.domain.repository.ProvisioningRepository
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ConnectivityRepositoryImpl @Inject constructor(
    @ApplicationContext private val context: Context,
    private val authRepository: AuthRepository,
    private val provisioningRepository: ProvisioningRepository,
) : ConnectivityRepository {

    private val connectivityManager =
        context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager

    override fun observeOnline(): Flow<Boolean> =
        observeConnectivity().map { it.state != ConnectivityState.DISCONNECTED }

    override suspend fun isOnline(): Boolean {
        val network = connectivityManager.activeNetwork ?: return false
        val capabilities = connectivityManager.getNetworkCapabilities(network) ?: return false
        return capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET) &&
            capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED)
    }

    override fun observeConnectivity(): Flow<ConnectivitySnapshot> =
        combine(
            networkAvailabilityFlow(),
            authRepository.observeIdentity(),
            provisioningRepository.observeProvisioningStatus(),
        ) { online, identity, provisioning ->
            buildSnapshot(online = online, identity = identity, provisioningState = provisioning.state)
        }.distinctUntilChanged()

    override suspend fun refreshBackendReachability(): ConnectivitySnapshot {
        val online = isOnline()
        val identity = authRepository.getIdentity()
        val provisioning = provisioningRepository.getStatus()
        val reachable = if (online && identity != null) {
            authRepository.refreshTokenIfNeeded().let { it is ir.sayda.yara.hub.core.result.AppResult.Success }
        } else {
            false
        }
        return buildSnapshot(
            online = online,
            identity = identity,
            provisioningState = provisioning.state,
            backendReachable = reachable,
        )
    }

    private fun buildSnapshot(
        online: Boolean,
        identity: HubIdentity?,
        provisioningState: ProvisioningState,
        backendReachable: Boolean = online && identity != null,
    ): ConnectivitySnapshot {
        val connectionType = currentConnectionType()
        val state = when {
            !online -> ConnectivityState.DISCONNECTED
            provisioningState == ProvisioningState.REGISTERING ||
                provisioningState == ProvisioningState.AUTHENTICATING -> ConnectivityState.CONNECTING
            identity == null -> ConnectivityState.CONNECTED
            provisioningState == ProvisioningState.READY && backendReachable -> ConnectivityState.PROVISIONED
            identity.accessToken.isNotBlank() -> ConnectivityState.AUTHENTICATED
            else -> ConnectivityState.CONNECTED
        }
        return ConnectivitySnapshot(
            state = state,
            connectionType = connectionType,
            isBackendReachable = backendReachable,
        )
    }

    private fun currentConnectionType(): String {
        val network = connectivityManager.activeNetwork ?: return "NONE"
        val capabilities = connectivityManager.getNetworkCapabilities(network) ?: return "UNKNOWN"
        return when {
            capabilities.hasTransport(NetworkCapabilities.TRANSPORT_WIFI) -> "WIFI"
            capabilities.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR) -> "CELLULAR"
            capabilities.hasTransport(NetworkCapabilities.TRANSPORT_ETHERNET) -> "ETHERNET"
            else -> "OTHER"
        }
    }

    private fun networkAvailabilityFlow(): Flow<Boolean> = callbackFlow {
        val callback = object : ConnectivityManager.NetworkCallback() {
            override fun onAvailable(network: Network) {
                trySend(true)
            }

            override fun onLost(network: Network) {
                trySend(false)
            }
        }
        val request = NetworkRequest.Builder()
            .addCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
            .build()
        connectivityManager.registerNetworkCallback(request, callback)
        trySend(isOnline())
        awaitClose { connectivityManager.unregisterNetworkCallback(callback) }
    }.distinctUntilChanged()
}
