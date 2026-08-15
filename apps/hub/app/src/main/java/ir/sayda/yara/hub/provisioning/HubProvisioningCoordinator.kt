package ir.sayda.yara.hub.provisioning

import android.content.Context
import android.provider.Settings
import dagger.hilt.android.qualifiers.ApplicationContext
import ir.sayda.yara.hub.core.domain.model.ConnectivityState
import ir.sayda.yara.hub.core.domain.model.ProvisioningState
import ir.sayda.yara.hub.core.domain.repository.AuthRepository
import ir.sayda.yara.hub.core.domain.repository.ConnectivityRepository
import ir.sayda.yara.hub.core.domain.repository.ProvisioningRepository
import ir.sayda.yara.hub.core.result.AppResult
import ir.sayda.yara.hub.core.provisioning.HubDeviceCredentialsProvider
import ir.sayda.yara.hub.core.runtime.RuntimeScheduler
import ir.sayda.yara.hub.data.identity.SecureHubIdentityStore
import ir.sayda.yara.hub.data.provisioning.ProvisioningStateMachine
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.launch
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import java.util.concurrent.atomic.AtomicBoolean
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
    private val provisionCredentials: HubDeviceCredentialsProvider,
    private val runtimeScheduler: RuntimeScheduler,
) {
    private val provisioningMutex = Mutex()
    private val provisionInFlight = AtomicBoolean(false)
    private var lastProvisionAttemptMs = 0L

    fun start(scope: CoroutineScope) {
        scope.launch {
            runStartupFlow()
        }
        scope.launch {
            stateMachine.observeState()
                .distinctUntilChanged()
                .collect { state ->
                    if (state != ProvisioningState.ERROR) return@collect
                    delay(RETRY_COOLDOWN_MS)
                    scheduleRetry()
                }
        }
        scope.launch {
            connectivityRepository.observeConnectivity()
                .map { it.state }
                .distinctUntilChanged()
                .collect { connectivityState ->
                    if (connectivityState == ConnectivityState.DISCONNECTED) return@collect
                    if (stateMachine.currentState() == ProvisioningState.READY) return@collect
                    delay(RETRY_COOLDOWN_MS)
                    scheduleRetry()
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
            ProvisioningState.UNPROVISIONED,
            ProvisioningState.REGISTERING,
            -> registerAndAuthenticate()
            ProvisioningState.ERROR -> resumeAfterError()
            ProvisioningState.REGISTERED,
            ProvisioningState.AUTHENTICATING,
            -> authenticateExisting()
            ProvisioningState.READY -> authRepository.refreshTokenIfNeeded()
        }
    }

    private suspend fun scheduleRetry() {
        val now = System.currentTimeMillis()
        if (now - lastProvisionAttemptMs < RETRY_COOLDOWN_MS) return
        lastProvisionAttemptMs = now
        retryIfNeeded()
    }

    private suspend fun retryIfNeeded() {
        when (stateMachine.currentState()) {
            ProvisioningState.ERROR -> resumeAfterError()
            ProvisioningState.UNPROVISIONED -> registerAndAuthenticate()
            ProvisioningState.REGISTERED -> authenticateExisting()
            else -> Unit
        }
    }

    private suspend fun resumeAfterError() {
        if (identityStore.readProvisioning()?.deviceId != null) {
            authenticateExisting()
        } else {
            registerAndAuthenticate()
        }
    }

    private suspend fun registerAndAuthenticate() {
        if (stateMachine.currentState() == ProvisioningState.READY) return
        if (!provisionInFlight.compareAndSet(false, true)) return
        try {
            provisioningMutex.withLock {
                if (stateMachine.currentState() == ProvisioningState.READY) return@withLock
                val serial = Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID)
                    ?: return@withLock
                when (provisioningRepository.registerDevice(serial, deviceModelCode.value)) {
                    is AppResult.Success -> authenticateWithinLock()
                    is AppResult.Error -> Unit
                }
            }
        } finally {
            provisionInFlight.set(false)
        }
    }

    private suspend fun authenticateExisting() {
        if (stateMachine.currentState() == ProvisioningState.READY) return
        if (!provisionInFlight.compareAndSet(false, true)) return
        try {
            provisioningMutex.withLock {
                if (stateMachine.currentState() == ProvisioningState.READY) return@withLock
                authenticateWithinLock()
            }
        } finally {
            provisionInFlight.set(false)
        }
    }

    private suspend fun authenticateWithinLock() {
        val deviceId = identityStore.readProvisioning()?.deviceId ?: return
        val credentials = provisionCredentials.credentials() ?: return
        when (
            provisioningRepository.authenticate(
                deviceId = deviceId,
                phone = credentials.phone,
                password = credentials.password,
            )
        ) {
            is AppResult.Success -> {
                connectivityRepository.refreshBackendReachability()
                runtimeScheduler.scheduleOneTimeRuntimeWork()
            }
            is AppResult.Error -> Unit
        }
    }

    companion object {
        private const val RETRY_COOLDOWN_MS = 10_000L
    }
}

interface HubDeviceModelCode {
    val value: String
}
