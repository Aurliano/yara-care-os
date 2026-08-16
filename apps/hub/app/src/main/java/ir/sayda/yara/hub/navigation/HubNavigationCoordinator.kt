package ir.sayda.yara.hub.navigation

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import ir.sayda.yara.hub.core.domain.model.CallSession
import ir.sayda.yara.hub.core.domain.model.isActive
import ir.sayda.yara.hub.core.runtime.CommunicationPresentationGateway
import ir.sayda.yara.hub.core.runtime.ReminderOpenRequest
import ir.sayda.yara.hub.core.runtime.ReminderPresentationGateway
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class HubNavigationCoordinator @Inject constructor(
    reminderPresentationGateway: ReminderPresentationGateway,
    communicationPresentationGateway: CommunicationPresentationGateway,
) : ViewModel() {

    private val _openRequests = MutableStateFlow<ReminderOpenRequest?>(null)
    val openRequests: StateFlow<ReminderOpenRequest?> = _openRequests.asStateFlow()

    private val _activeCall = MutableStateFlow<CallSession?>(null)
    val activeCall: StateFlow<CallSession?> = _activeCall.asStateFlow()

    init {
        viewModelScope.launch {
            reminderPresentationGateway.observeOpenRequests().collect { request ->
                _openRequests.value = request
            }
        }
        viewModelScope.launch {
            communicationPresentationGateway.observeCallSessions().collect { session ->
                _activeCall.value = session.takeIf { it.runtimeState.isActive() }
            }
        }
    }
}
