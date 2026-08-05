package ir.sayda.yara.hub.connectivity

import android.content.Context
import android.net.ConnectivityManager
import android.net.Network
import android.net.NetworkCapabilities
import android.net.NetworkRequest
import dagger.hilt.android.qualifiers.ApplicationContext
import ir.sayda.yara.hub.core.runtime.RuntimeScheduler
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ConnectivitySyncTrigger @Inject constructor(
    @ApplicationContext private val context: Context,
    private val runtimeScheduler: RuntimeScheduler,
) {
    private val connectivityManager =
        context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager

    private var registered = false

    fun register() {
        if (registered) return
        registered = true
        val request = NetworkRequest.Builder()
            .addCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
            .addCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED)
            .build()
        connectivityManager.registerNetworkCallback(
            request,
            object : ConnectivityManager.NetworkCallback() {
                override fun onAvailable(network: Network) {
                    runtimeScheduler.scheduleOneTimeRuntimeWork(occurrenceId = null)
                }
            },
        )
    }
}
