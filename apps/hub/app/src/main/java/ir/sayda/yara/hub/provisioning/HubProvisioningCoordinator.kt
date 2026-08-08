package ir.sayda.yara.hub.provisioning

import android.content.Context
import android.provider.Settings
import dagger.hilt.android.qualifiers.ApplicationContext
import ir.sayda.yara.hub.core.domain.model.ProvisioningState
import ir.sayda.yara.hub.core.domain.repository.AuthRepository
import ir.sayda.yara.hub.core.domain.repository.ConnectivityRepository
import ir.sayda.yara.hub.core.domain.repository.ProvisioningRepository
import ir.sayda.yara.hub.core.result.AppResult
import ir.sayda.yara.hub.data.identity.SecureHubIdentityStore
import ir.sayda.yara.hub.data.provisioning.ProvisioningStateMachine
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class HubProvisioningCoordinator @Inject constructor(
    @ApplicationContext private val context: Context,
    private val provisioningRepository: ProvisioningRepository,
    private val authRepository: AuthRepository,
    private val connectivityRepository: ConnectivityRepository,
    private val identityStore: SecureHubIdentityStore,
    private val stateMachine: ProvisioningStateMachine,
    private val deviceModelCode: HubDeviceModelCode,
    private val provisionCredentials: HubProvisionCredentials,
) {
    fun start(scope: CoroutineScope) {
        scope.launch { runStartupFlow() }
        scope.launch {
            connectivityRepository.observeConnectivity().collectLatest {
                if (it.state == ir.sayda.yara.hub.core.domain.model.ConnectivityState.CONNECTED) {
                    retryIfNeeded()
                }
            }
        }
    }

    suspend fun runStartupFlow() {
        identityStore.readProvisioning()?.provisioningState?.let { stateMachine.restore(it) }
        authRepository.refreshTokenIfNeeded()
        val restored = provisioningRepository.restoreProvisioning()
        val currentState = when (restored) {
            is AppResult.Success -> restored.data.state
            is AppResult.Error -> ProvisioningState.UNPROVISIONED
        }
        when (currentState) {
            ProvisioningState.UNPROVISIONED, ProvisioningState.ERROR -> registerAndAuthenticate()
            ProvisioningState.REGISTERED -> authenticateExisting()
            ProvisioningState.READY -> authRepository.refreshTokenIfNeeded()
            else -> Unit
        }
    }

    private suspend fun retryIfNeeded() {
        when (stateMachine.currentState()) {
            ProvisioningState.ERROR, ProvisioningState.UNPROVISIONED -> registerAndAuthenticate()
            ProvisioningState.REGISTERED -> authenticateExisting()
            else -> Unit
        }
    }

    private suspend fun registerAndAuthenticate() {
        val serial = Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID)
            ?: return
        when (val registered = provisioningRepository.registerDevice(serial, deviceModelCode.value)) {
            is AppResult.Success -> authenticateExisting()
            is AppResult.Error -> Unit
        }
    }

    private suspend fun authenticateExisting() {
        val deviceId = identityStore.readProvisioning()?.deviceId ?: return
        val credentials = provisionCredentials.credentials() ?: return
        provisioningRepository.authenticate(
            deviceId = deviceId,
            phone = credentials.phone,
            password = credentials.password,
        )
        connectivityRepository.refreshBackendReachability()
    }
}

interface HubDeviceModelCode {
    val value: String
}

interface HubProvisionCredentials {
    fun credentials(): ProvisionCredential?
}

data class ProvisionCredential(
    val phone: String,
    val password: String,
)
