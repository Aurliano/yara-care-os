package ir.sayda.yara.hub.feature.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import ir.sayda.yara.hub.core.domain.model.HomeRuntimeSnapshot
import ir.sayda.yara.hub.core.domain.usecase.ObserveHomeSnapshotUseCase
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import javax.inject.Inject

@HiltViewModel
class HomeViewModel @Inject constructor(
    observeHomeSnapshotUseCase: ObserveHomeSnapshotUseCase,
) : ViewModel() {
    val snapshot: StateFlow<HomeRuntimeSnapshot> = observeHomeSnapshotUseCase()
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = HomeRuntimeSnapshot(
                elderDisplayName = "سالمند",
                activeExecutions = emptyList(),
                priorityContacts = emptyList(),
                replicaHealth = "UNKNOWN",
                isOnline = false,
            ),
        )
}
