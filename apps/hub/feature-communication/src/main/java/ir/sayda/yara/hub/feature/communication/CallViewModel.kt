package ir.sayda.yara.hub.feature.communication

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import ir.sayda.yara.hub.core.communication.CommunicationProviderException
import ir.sayda.yara.hub.core.communication.ProviderFailureReason
import ir.sayda.yara.hub.core.domain.model.CallRuntimeState
import ir.sayda.yara.hub.core.domain.model.CallSession
import ir.sayda.yara.hub.core.domain.model.Contact
import ir.sayda.yara.hub.core.domain.model.isActive
import ir.sayda.yara.hub.core.domain.repository.AuthRepository
import ir.sayda.yara.hub.core.domain.repository.CommunicationReplicaRepository
import ir.sayda.yara.hub.core.result.AppResult
import ir.sayda.yara.hub.core.runtime.CommunicationPresentationGateway
import ir.sayda.yara.hub.feature.communication.presentation.CommunicationPresentationState
import ir.sayda.yara.hub.feature.communication.presentation.CommunicationPresentationStateMapper
import ir.sayda.yara.hub.runtime.communication.CommunicationRuntime
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class CallViewArgs(
    val contactId: String = "",
    val elderId: String = "",
    val channel: String = "",
    val contactName: String = "",
)

private data class CallViewBits(
    val session: CallSession? = null,
    val contacts: List<Contact> = emptyList(),
    val muted: Boolean = false,
    val cameraOn: Boolean = false,
    val startFailed: Boolean = false,
    val startFailedStatusRes: Int? = null,
    val fallbackName: String = "",
    val awaitingOutgoing: Boolean = false,
    val locallyFinished: Boolean = false,
)

@HiltViewModel
class CallViewModel @Inject constructor(
    private val communicationRuntime: CommunicationRuntime,
    private val presentationGateway: CommunicationPresentationGateway,
    private val authRepository: AuthRepository,
    private val communicationReplicaRepository: CommunicationReplicaRepository,
) : ViewModel() {

    private val bits = MutableStateFlow(CallViewBits())
    private var outgoingArgs: CallViewArgs? = null
    private var outgoingStarted = false

    val uiState: StateFlow<CommunicationPresentationState> = bits
        .map { current ->
            val session = current.session
            CommunicationPresentationStateMapper.map(
                session = session,
                contactName = session?.let { active ->
                    CommunicationPresentationStateMapper.resolvedContactName(
                        session = active,
                        contacts = current.contacts,
                        fallbackName = current.fallbackName,
                    )
                } ?: current.fallbackName,
                muted = current.muted,
                cameraOn = current.cameraOn,
                startFailed = current.startFailed,
                startFailedStatusRes = current.startFailedStatusRes,
                awaitingOutgoing = current.awaitingOutgoing,
                locallyFinished = current.locallyFinished,
            )
        }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = CommunicationPresentationStateMapper.map(session = null, contactName = ""),
        )

    init {
        viewModelScope.launch {
            presentationGateway.observeCallSessions().collect { update ->
                bits.update {
                    it.copy(
                        session = update,
                        startFailed = false,
                        awaitingOutgoing = false,
                        locallyFinished = update.runtimeState == CallRuntimeState.Finished,
                    )
                }
            }
        }
        viewModelScope.launch {
            communicationRuntime.observeCurrent().collect { current ->
                if (current != null) {
                    bits.update { it.copy(session = current, awaitingOutgoing = false) }
                }
            }
        }
        viewModelScope.launch {
            val elderId = authRepository.getIdentity()?.elderId.orEmpty()
            if (elderId.isBlank()) return@launch
            communicationReplicaRepository.observePriorityContacts(elderId).collect { contacts ->
                bits.update { it.copy(contacts = contacts) }
            }
        }
    }

    fun prepare(args: CallViewArgs) {
        if (args.contactName.isNotBlank()) {
            bits.update { it.copy(fallbackName = args.contactName) }
        }
        val video = args.channel.equals("VIDEO", ignoreCase = true)
        bits.update { it.copy(cameraOn = video) }
        if (args.contactId.isBlank()) return
        outgoingArgs = args
        startOutgoing(args)
    }

    fun answer() {
        viewModelScope.launch {
            val current = bits.value.session
            val elderId = current?.elderId?.ifBlank { null }
                ?: authRepository.getIdentity()?.elderId.orEmpty()
            if (elderId.isBlank()) return@launch
            communicationRuntime.joinIncomingCall(
                elderId = elderId,
                channel = current?.channel?.ifBlank { "VOICE" } ?: "VOICE",
                recipientContactId = current?.recipientContactId.orEmpty(),
            )
        }
    }

    fun hangup() {
        viewModelScope.launch {
            val ended = communicationRuntime.endCall()
            bits.update { current ->
                val session = current.session
                when {
                    ended is AppResult.Success -> current.copy(
                        awaitingOutgoing = false,
                        startFailed = false,
                        locallyFinished = true,
                        session = session?.copy(runtimeState = CallRuntimeState.Finished),
                    )
                    session == null -> current.copy(
                        awaitingOutgoing = false,
                        locallyFinished = true,
                    )
                    else -> current
                }
            }
        }
    }

    fun retry() {
        val failedOutgoing = outgoingArgs
        if (bits.value.startFailed && failedOutgoing != null) {
            outgoingStarted = false
            startOutgoing(failedOutgoing)
            return
        }
        viewModelScope.launch {
            bits.update { it.copy(startFailed = false) }
            if (communicationRuntime.reconnect() is AppResult.Error) {
                if (bits.value.session?.runtimeState?.isActive() != true) {
                    bits.update { it.copy(startFailed = true, startFailedStatusRes = R.string.call_failed_status) }
                }
            }
        }
    }

    fun toggleMute() {
        viewModelScope.launch {
            val next = !bits.value.muted
            if (next) communicationRuntime.mute() else communicationRuntime.unmute()
            bits.update { it.copy(muted = next) }
        }
    }

    fun speaker() {
        viewModelScope.launch { communicationRuntime.speaker() }
    }

    fun toggleCamera() {
        viewModelScope.launch {
            val video = bits.value.session?.channel.equals("VIDEO", ignoreCase = true)
            if (!video) return@launch
            val next = !bits.value.cameraOn
            if (next) communicationRuntime.cameraOn() else communicationRuntime.cameraOff()
            bits.update { it.copy(cameraOn = next) }
        }
    }

    private fun startOutgoing(args: CallViewArgs) {
        if (outgoingStarted) return
        outgoingStarted = true
        bits.update { it.copy(awaitingOutgoing = true, startFailed = false, locallyFinished = false) }
        viewModelScope.launch {
            val elderId = args.elderId.ifBlank { authRepository.getIdentity()?.elderId.orEmpty() }
            val channel = args.channel.ifBlank { "VOICE" }
            if (elderId.isBlank()) {
                bits.update { it.copy(startFailed = true, startFailedStatusRes = R.string.call_failed_status, awaitingOutgoing = false) }
                return@launch
            }
            val current = bits.value.session
            if (current != null && current.runtimeState.isActive()) {
                bits.update { it.copy(awaitingOutgoing = false) }
                return@launch
            }
            when (val result = communicationRuntime.startCall(elderId, channel, args.contactId)) {
                is AppResult.Success -> bits.update { it.copy(startFailed = false, startFailedStatusRes = null, awaitingOutgoing = false) }
                is AppResult.Error -> bits.update {
                    it.copy(
                        startFailed = true,
                        startFailedStatusRes = callFailureStatusRes(result.exception),
                        awaitingOutgoing = false,
                    )
                }
            }
        }
    }
}

internal fun callFailureStatusRes(error: Throwable): Int {
    if (error is CommunicationProviderException) {
        when (error.reason) {
            ProviderFailureReason.NOT_CONFIGURED -> return R.string.call_provider_not_configured
            ProviderFailureReason.UNREACHABLE -> return R.string.call_provider_unreachable
            ProviderFailureReason.BUSY -> return R.string.call_provider_busy
            ProviderFailureReason.REJECTED,
            ProviderFailureReason.INVALID_RESPONSE,
            -> return R.string.call_provider_rejected
        }
    }
    val detail = error.message.orEmpty()
    return when {
        detail.contains("not configured", ignoreCase = true) -> R.string.call_provider_not_configured
        detail.contains("unreachable", ignoreCase = true) -> R.string.call_provider_unreachable
        else -> R.string.call_failed_status
    }
}
