package ir.sayda.yara.hub.feature.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import ir.sayda.yara.hub.core.domain.model.HomeRuntimeSnapshot
import ir.sayda.yara.hub.core.domain.model.ProvisioningState
import ir.sayda.yara.hub.core.domain.repository.ProvisioningRepository
import ir.sayda.yara.hub.core.domain.usecase.ObserveHomeSnapshotUseCase
import ir.sayda.yara.hub.core.domain.usecase.RunSynchronizationCycleUseCase
import ir.sayda.yara.hub.core.provisioning.HubDeviceCredentialsProvider
import ir.sayda.yara.hub.core.provisioning.ProvisionCredential
import ir.sayda.yara.hub.core.result.AppResult
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

data class HomeUiState(
    val isLoading: Boolean,
    val snapshot: HomeRuntimeSnapshot,
    val phone: String = "",
    val password: String = "",
    val isSubmittingLogin: Boolean = false,
    val loginError: String? = null,
)

@HiltViewModel
class HomeViewModel @Inject constructor(
    observeHomeSnapshotUseCase: ObserveHomeSnapshotUseCase,
    private val provisioningRepository: ProvisioningRepository,
    private val credentialsProvider: HubDeviceCredentialsProvider,
    private val runSynchronizationCycleUseCase: RunSynchronizationCycleUseCase,
) : ViewModel() {
    private val suggested = credentialsProvider.suggestedCredentials()
    private val phone = MutableStateFlow(suggested?.phone.orEmpty())
    private val password = MutableStateFlow(suggested?.password.orEmpty())
    private val submitting = MutableStateFlow(false)
    private val loginError = MutableStateFlow<String?>(null)

    val uiState: StateFlow<HomeUiState> = combine(
        observeHomeSnapshotUseCase(),
        phone,
        password,
        submitting,
        loginError,
    ) { snapshot, phoneValue, passwordValue, isSubmitting, error ->
        HomeUiState(
            isLoading = false,
            snapshot = snapshot,
            phone = phoneValue,
            password = passwordValue,
            isSubmittingLogin = isSubmitting,
            loginError = error ?: snapshot.lastProvisioningError?.takeIf {
                snapshot.provisioningState == ProvisioningState.ERROR
            },
        )
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = HomeUiState(isLoading = true, snapshot = placeholderSnapshot()),
    )

    val snapshot: StateFlow<HomeRuntimeSnapshot> = uiState
        .map { it.snapshot }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = placeholderSnapshot(),
        )

    fun onPhoneChange(value: String) {
        phone.value = value
        loginError.value = null
    }

    fun onPasswordChange(value: String) {
        password.value = value
        loginError.value = null
    }

    fun submitCaregiverLogin() {
        val deviceId = uiState.value.snapshot.deviceId
        if (deviceId.isNullOrBlank()) {
            loginError.value = "دستگاه هنوز ثبت نشده است. کمی صبر کنید."
            return
        }
        val phoneValue = phone.value.trim()
        val passwordValue = password.value
        if (phoneValue.isBlank() || passwordValue.isBlank()) {
            loginError.value = "شماره موبایل و رمز عبور مراقب را وارد کنید."
            return
        }
        viewModelScope.launch {
            submitting.value = true
            loginError.value = null
            credentialsProvider.saveCredentials(
                ProvisionCredential(phone = phoneValue, password = passwordValue),
            )
            when (
                val result = provisioningRepository.authenticate(
                    deviceId = deviceId,
                    phone = phoneValue,
                    password = passwordValue,
                )
            ) {
                is AppResult.Success -> {
                    loginError.value = null
                    runSynchronizationCycleUseCase("caregiver-login:${System.currentTimeMillis()}")
                }
                is AppResult.Error -> {
                    loginError.value = result.exception.message
                        ?: "ورود انجام نشد. شماره و رمز مراقب را بررسی کنید."
                }
            }
            submitting.value = false
        }
    }

    companion object {
        private fun placeholderSnapshot() = HomeRuntimeSnapshot(
            elderDisplayName = "سالمند",
            activeExecutions = emptyList(),
            todayReminders = emptyList(),
            priorityContacts = emptyList(),
            replicaHealth = "",
            runtimeHealth = "",
            lastSyncEpochMillis = null,
            isOnline = false,
        )
    }
}
