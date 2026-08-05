package ir.sayda.yara.hub.navigation

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
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
) : ViewModel() {

    private val _openRequests = MutableStateFlow<ReminderOpenRequest?>(null)
    val openRequests: StateFlow<ReminderOpenRequest?> = _openRequests.asStateFlow()

    init {
        viewModelScope.launch {
            reminderPresentationGateway.observeOpenRequests().collect { request ->
                _openRequests.value = request
            }
        }
    }
}
