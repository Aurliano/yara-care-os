package ir.sayda.yara.hub.feature.home

import android.content.Context
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import dagger.hilt.android.qualifiers.ApplicationContext
import ir.sayda.yara.hub.core.domain.model.Contact
import ir.sayda.yara.hub.core.domain.model.HomeRuntimeSnapshot
import ir.sayda.yara.hub.core.domain.model.Message
import ir.sayda.yara.hub.core.domain.model.MessageType
import ir.sayda.yara.hub.core.domain.model.ProvisioningState
import ir.sayda.yara.hub.core.domain.repository.CommunicationReplicaRepository
import ir.sayda.yara.hub.core.domain.repository.MessagingRepository
import ir.sayda.yara.hub.core.domain.repository.ProvisioningRepository
import ir.sayda.yara.hub.core.domain.usecase.ObserveHomeSnapshotUseCase
import ir.sayda.yara.hub.core.domain.usecase.ObserveHubIdentityUseCase
import ir.sayda.yara.hub.core.domain.usecase.RunSynchronizationCycleUseCase
import ir.sayda.yara.hub.core.media.AudioPlayer
import ir.sayda.yara.hub.core.media.AudioRecorder
import ir.sayda.yara.hub.core.provisioning.HubDeviceCredentialsProvider
import ir.sayda.yara.hub.core.provisioning.ProvisionCredential
import ir.sayda.yara.hub.core.result.AppResult
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import java.io.File
import java.util.UUID
import javax.inject.Inject

data class HomeUiState(
    val isLoading: Boolean,
    val snapshot: HomeRuntimeSnapshot,
    val phone: String = "",
    val password: String = "",
    val isSubmittingLogin: Boolean = false,
    val loginError: String? = null,
    val contacts: List<Contact> = emptyList(),
    val selectedContactId: String? = null,
    val messages: List<Message> = emptyList(),
    val isPlayingAudio: Boolean = false,
    val playingMessageId: String? = null,
    val isRecordingVoice: Boolean = false,
    val recordingDurationSeconds: Int = 0,
)

private data class HomeBaseState(
    val snapshot: HomeRuntimeSnapshot,
    val phone: String,
    val password: String,
    val isSubmitting: Boolean,
    val error: String?,
)

private data class HomeMessageState(
    val contacts: List<Contact>,
    val selectedContactId: String?,
    val messages: List<Message>,
    val isPlayingAudio: Boolean,
    val playingMessageId: String?,
    val isRecordingVoice: Boolean,
    val recordingDurationSeconds: Int,
)

@HiltViewModel
class HomeViewModel @Inject constructor(
    observeHomeSnapshotUseCase: ObserveHomeSnapshotUseCase,
    observeHubIdentityUseCase: ObserveHubIdentityUseCase,
    private val communicationReplicaRepository: CommunicationReplicaRepository,
    private val messagingRepository: MessagingRepository,
    private val audioRecorder: AudioRecorder,
    private val audioPlayer: AudioPlayer,
    private val provisioningRepository: ProvisioningRepository,
    private val credentialsProvider: HubDeviceCredentialsProvider,
    private val runSynchronizationCycleUseCase: RunSynchronizationCycleUseCase,
    @ApplicationContext private val context: Context,
) : ViewModel() {
    private val suggested = credentialsProvider.suggestedCredentials()
    private val phone = MutableStateFlow(suggested?.phone.orEmpty())
    private val password = MutableStateFlow(suggested?.password.orEmpty())
    private val submitting = MutableStateFlow(false)
    private val loginError = MutableStateFlow<String?>(null)

    private val isPlayingAudio = MutableStateFlow(false)
    private val playingMessageId = MutableStateFlow<String?>(null)
    private val isRecordingVoice = MutableStateFlow(false)
    private val recordingDurationSeconds = MutableStateFlow(0)
    private var recordingTimerJob: Job? = null
    private var currentElderId: String? = null

    init {
        viewModelScope.launch {
            observeHubIdentityUseCase().collectLatest { identity ->
                val elderId = identity?.elderId
                currentElderId = elderId
                if (elderId != null) {
                    var currentDelayMs = 3_000L
                    while (true) {
                        try {
                            val result = messagingRepository.syncElderMessages(elderId)
                            if (result is AppResult.Success) {
                                currentDelayMs = 3_000L
                            } else {
                                currentDelayMs = (currentDelayMs * 2).coerceAtMost(30_000L)
                            }
                        } catch (_: Exception) {
                            currentDelayMs = (currentDelayMs * 2).coerceAtMost(30_000L)
                        }
                        delay(currentDelayMs)
                    }
                }
            }
        }
    }

    private val selectedContactId = MutableStateFlow<String?>(null)

    fun selectContact(contactId: String?) {
        selectedContactId.value = contactId
    }

    @OptIn(kotlinx.coroutines.ExperimentalCoroutinesApi::class)
    private val contactsFlow = observeHubIdentityUseCase().flatMapLatest { identity ->
        val elderId = identity?.elderId
        if (elderId != null) {
            communicationReplicaRepository.observeContacts(elderId)
        } else {
            flowOf(emptyList())
        }
    }

    @OptIn(kotlinx.coroutines.ExperimentalCoroutinesApi::class)
    private val messagesFlow = observeHubIdentityUseCase().flatMapLatest { identity ->
        val elderId = identity?.elderId
        if (elderId != null) {
            messagingRepository.observeMessages(elderId)
        } else {
            flowOf(emptyList())
        }
    }

    val uiState: StateFlow<HomeUiState> = combine(
        combine(
            observeHomeSnapshotUseCase(),
            phone,
            password,
            submitting,
            loginError,
        ) { snapshot, phoneVal, passVal, isSub, err ->
            HomeBaseState(snapshot, phoneVal, passVal, isSub, err)
        },
        combine(
            combine(contactsFlow, selectedContactId) { contacts, selId -> Pair(contacts, selId) },
            messagesFlow,
            isPlayingAudio,
            playingMessageId,
            combine(isRecordingVoice, recordingDurationSeconds) { rec, secs -> Pair(rec, secs) },
        ) { (contacts, selId), msgs, isPlaying, playingId, (isRec, recSecs) ->
            HomeMessageState(contacts, selId, msgs, isPlaying, playingId, isRec, recSecs)
        },
    ) { base, msgState ->
        HomeUiState(
            isLoading = false,
            snapshot = base.snapshot,
            phone = base.phone,
            password = base.password,
            isSubmittingLogin = base.isSubmitting,
            loginError = base.error ?: base.snapshot.lastProvisioningError?.takeIf {
                base.snapshot.provisioningState == ProvisioningState.ERROR
            },
            contacts = msgState.contacts,
            selectedContactId = msgState.selectedContactId,
            messages = msgState.messages,
            isPlayingAudio = msgState.isPlayingAudio,
            playingMessageId = msgState.playingMessageId,
            isRecordingVoice = msgState.isRecordingVoice,
            recordingDurationSeconds = msgState.recordingDurationSeconds,
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

    fun togglePlayVoiceMessage(message: Message) {
        if (isPlayingAudio.value && playingMessageId.value == message.id) {
            audioPlayer.stop()
            isPlayingAudio.value = false
            playingMessageId.value = null
            return
        }

        val fileUri = message.localFileUri ?: return
        val file = File(fileUri)
        if (!file.exists()) return

        audioPlayer.stop()
        val result = audioPlayer.play(file) {
            isPlayingAudio.value = false
            playingMessageId.value = null
        }
        if (result is AppResult.Success) {
            isPlayingAudio.value = true
            playingMessageId.value = message.id
            if (message.status != ir.sayda.yara.hub.core.domain.model.MessageStatus.READ) {
                viewModelScope.launch {
                    messagingRepository.markMessageRead(message.id)
                }
            }
        }
    }

    fun startRecordingVoice() {
        if (isRecordingVoice.value) return
        val tempFile = File(context.cacheDir, "record_${UUID.randomUUID()}.m4a")
        val result = audioRecorder.startRecording(tempFile)
        if (result is AppResult.Success) {
            isRecordingVoice.value = true
            recordingDurationSeconds.value = 0
            recordingTimerJob?.cancel()
            recordingTimerJob = viewModelScope.launch {
                while (isRecordingVoice.value) {
                    delay(1_000L)
                    recordingDurationSeconds.value += 1
                }
            }
        }
    }

    fun stopAndSendVoice() {
        if (!isRecordingVoice.value) return
        recordingTimerJob?.cancel()
        recordingTimerJob = null
        isRecordingVoice.value = false
        val seconds = recordingDurationSeconds.value
        recordingDurationSeconds.value = 0

        viewModelScope.launch {
            val result = audioRecorder.stopRecording()
            if (result is AppResult.Success) {
                val recorded = result.data
                val elderId = currentElderId
                if (elderId != null) {
                    messagingRepository.enqueueOutgoingMessage(
                        elderId = elderId,
                        messageType = MessageType.VOICE,
                        body = null,
                        localFileUri = recorded.file.absolutePath,
                        durationSeconds = recorded.durationSeconds.takeIf { it > 0 } ?: seconds,
                        fileSize = recorded.fileSize,
                    )
                }
            }
        }
    }

    fun sendTextMessage(text: String) {
        val trimmed = text.trim()
        if (trimmed.isBlank()) return
        val elderId = currentElderId ?: return
        viewModelScope.launch {
            messagingRepository.enqueueOutgoingMessage(
                elderId = elderId,
                messageType = MessageType.TEXT,
                body = trimmed,
                localFileUri = null,
                durationSeconds = null,
                fileSize = null,
            )
        }
    }

    fun retryMessage(message: Message) {
        val elderId = currentElderId ?: return
        viewModelScope.launch {
            messagingRepository.enqueueOutgoingMessage(
                elderId = elderId,
                messageType = message.messageType,
                body = message.body,
                localFileUri = message.localFileUri,
                durationSeconds = message.durationSeconds,
                fileSize = message.fileSize,
            )
        }
    }

    fun markIncomingMessagesAsRead() {
        val unreadList = uiState.value.messages.filter {
            it.direction == ir.sayda.yara.hub.core.domain.model.MessageDirection.FAMILY_TO_HUB &&
                it.status != ir.sayda.yara.hub.core.domain.model.MessageStatus.READ
        }
        if (unreadList.isEmpty()) return
        viewModelScope.launch {
            for (msg in unreadList) {
                messagingRepository.markMessageRead(msg.id)
            }
        }
    }

    fun cancelRecordingVoice() {
        recordingTimerJob?.cancel()
        recordingTimerJob = null
        isRecordingVoice.value = false
        recordingDurationSeconds.value = 0
        audioRecorder.cancelRecording()
    }

    override fun onCleared() {
        super.onCleared()
        audioPlayer.stop()
        if (isRecordingVoice.value) {
            audioRecorder.cancelRecording()
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
