package ir.sayda.yara.hub.feature.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import ir.sayda.yara.hub.core.domain.model.HomeRuntimeSnapshot
import ir.sayda.yara.hub.core.domain.usecase.ObserveHomeSnapshotUseCase
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import javax.inject.Inject

data class HomeUiState(
    val isLoading: Boolean,
    val snapshot: HomeRuntimeSnapshot,
)

@HiltViewModel
class HomeViewModel @Inject constructor(
    observeHomeSnapshotUseCase: ObserveHomeSnapshotUseCase,
) : ViewModel() {
    val uiState: StateFlow<HomeUiState> = observeHomeSnapshotUseCase()
        .map { snapshot -> HomeUiState(isLoading = false, snapshot = snapshot) }
        .stateIn(
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
