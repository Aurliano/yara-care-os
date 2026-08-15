package ir.sayda.yara.hub.feature.reminder

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import ir.sayda.yara.hub.core.domain.model.ReminderPresentation
import ir.sayda.yara.hub.core.domain.usecase.ConfirmReminderUseCase
import ir.sayda.yara.hub.core.domain.usecase.ObserveReminderPresentationUseCase
import ir.sayda.yara.hub.core.domain.usecase.PostponeReminderUseCase
import ir.sayda.yara.hub.core.result.AppResult
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class ReminderViewModel @Inject constructor(
    private val observeReminderPresentationUseCase: ObserveReminderPresentationUseCase,
    private val confirmReminderUseCase: ConfirmReminderUseCase,
    private val postponeReminderUseCase: PostponeReminderUseCase,
) : ViewModel() {

    private val _presentation = MutableStateFlow<ReminderPresentation?>(null)
    val presentation: StateFlow<ReminderPresentation?> = _presentation.asStateFlow()

    private val _confirmationState = MutableStateFlow<ConfirmationState>(ConfirmationState.Idle)
    val confirmationState: StateFlow<ConfirmationState> = _confirmationState.asStateFlow()

    private val _postponeState = MutableStateFlow<PostponeState>(PostponeState.Idle)
    val postponeState: StateFlow<PostponeState> = _postponeState.asStateFlow()

    fun load(executionId: String) {
        viewModelScope.launch {
            _presentation.value = observeReminderPresentationUseCase(executionId)
        }
    }

    fun confirm(executionId: String) {
        viewModelScope.launch {
            _confirmationState.value = ConfirmationState.Submitting
            when (val result = confirmReminderUseCase(executionId, interactionReference = "hub_ui_confirm")) {
                is AppResult.Success -> {
                    _presentation.value = observeReminderPresentationUseCase(executionId)
                    _confirmationState.value = ConfirmationState.Completed(result.data)
                }
                is AppResult.Error -> _confirmationState.value = ConfirmationState.Failed(
                    result.message.ifBlank { result.exception.message.orEmpty() },
                )
            }
        }
    }

    fun postpone(executionId: String) {
        viewModelScope.launch {
            _postponeState.value = PostponeState.Submitting
            when (val result = postponeReminderUseCase(executionId, interactionReference = "hub_ui_postpone")) {
                is AppResult.Success -> _postponeState.value = PostponeState.Completed(result.data)
                is AppResult.Error -> _postponeState.value = PostponeState.Failed(
                    result.message.ifBlank { result.exception.message.orEmpty() },
                )
            }
        }
    }

    sealed interface ConfirmationState {
        data object Idle : ConfirmationState
        data object Submitting : ConfirmationState
        data class Completed(val pendingEvidenceId: String) : ConfirmationState
        data class Failed(val message: String) : ConfirmationState
    }

    sealed interface PostponeState {
        data object Idle : PostponeState
        data object Submitting : PostponeState
        data class Completed(val postponedUntilEpochMillis: Long) : PostponeState
        data class Failed(val message: String) : PostponeState
    }
}
