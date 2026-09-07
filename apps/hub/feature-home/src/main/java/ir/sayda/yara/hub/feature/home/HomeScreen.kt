package ir.sayda.yara.hub.feature.home

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableLongStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import ir.sayda.yara.hub.feature.home.presentation.emptyMedicationMessage
import ir.sayda.yara.hub.feature.home.presentation.needsCaregiverLogin
import ir.sayda.yara.hub.feature.home.presentation.showFamilyMessagesPlaceholder
import ir.sayda.yara.hub.feature.home.presentation.toConnectionPresentation
import ir.sayda.yara.hub.feature.home.presentation.toNextReminderPresentation
import ir.sayda.yara.hub.feature.home.presentation.todayRemindersSectionTitle
import ir.sayda.yara.hub.ui.components.ActiveVoiceMessageCard
import ir.sayda.yara.hub.ui.components.BrandHeader
import ir.sayda.yara.hub.ui.components.ConnectionIndicator
import ir.sayda.yara.hub.ui.components.ContactCard
import ir.sayda.yara.hub.ui.components.DeveloperDiagnosticsCard
import ir.sayda.yara.hub.ui.components.FamilyMediaMessageCard
import ir.sayda.yara.hub.ui.components.FamilyTextMessageCard
import ir.sayda.yara.hub.ui.components.GreetingSection
import ir.sayda.yara.hub.ui.components.HomeEmptyStateCard
import ir.sayda.yara.hub.ui.components.HomeLoadingSkeleton
import ir.sayda.yara.hub.ui.components.NextReminderHighlightCard
import ir.sayda.yara.hub.ui.components.RecordVoiceMessageCard
import ir.sayda.yara.hub.ui.components.SettingsButton
import ir.sayda.yara.hub.ui.components.TodayBackground
import ir.sayda.yara.hub.ui.components.TodayReminderCard
import ir.sayda.yara.hub.ui.theme.TextSecondary
import ir.sayda.yara.hub.ui.theme.WarmWhite
import kotlinx.coroutines.delay
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

@Composable
fun HomeRoute(
    isDebugBuild: Boolean,
    onOpenDeveloperSettings: () -> Unit,
    onSettingsLongPress: () -> Unit,
    onCallContact: (contactId: String, elderId: String, channel: String, displayName: String) -> Unit = { _, _, _, _ -> },
    modifier: Modifier = Modifier,
    viewModel: HomeViewModel = hiltViewModel(),
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    val snapshot = uiState.snapshot
    var nowEpochMillis by remember { mutableLongStateOf(System.currentTimeMillis()) }
    LaunchedEffect(Unit) {
        while (true) {
            nowEpochMillis = System.currentTimeMillis()
            delay(1_000L)
        }
    }
    val now = Date(nowEpochMillis)
    val timeFormatter = SimpleDateFormat("HH:mm", Locale("fa", "IR"))
    val dateFormatter = SimpleDateFormat("EEEE، d MMMM yyyy", Locale("fa", "IR"))
    val reminderTimeFormatter = SimpleDateFormat("HH:mm", Locale("fa", "IR"))
    val connection = snapshot.toConnectionPresentation()
    val nextReminder = snapshot.toNextReminderPresentation(reminderTimeFormatter)

    CompositionLocalProvider(androidx.compose.ui.platform.LocalLayoutDirection provides LayoutDirection.Rtl) {
        Scaffold(
            modifier = modifier.fillMaxSize(),
            containerColor = WarmWhite,
        ) { innerPadding ->
            Box(modifier = Modifier.fillMaxSize()) {
                TodayBackground(modifier = Modifier.fillMaxSize())
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(innerPadding),
                ) {
                    BrandHeader(
                        time = timeFormatter.format(now),
                        date = dateFormatter.format(now),
                        onLogoActivated = {
                            if (isDebugBuild) onOpenDeveloperSettings()
                        },
                    )
                    if (uiState.isLoading) {
                        HomeLoadingSkeleton(
                            modifier = Modifier.padding(horizontal = 24.dp, vertical = 32.dp),
                        )
                    } else {
                        LazyColumn(
                            modifier = Modifier.fillMaxSize(),
                            contentPadding = PaddingValues(
                                start = 24.dp,
                                end = 24.dp,
                                top = 16.dp,
                                bottom = 120.dp,
                            ),
                            verticalArrangement = Arrangement.spacedBy(24.dp),
                            horizontalAlignment = Alignment.CenterHorizontally,
                        ) {
                            item {
                                GreetingSection(name = snapshot.elderDisplayName.ifBlank { "دوست عزیز" })
                                Spacer(modifier = Modifier.height(24.dp))
                            }

                            if (snapshot.needsCaregiverLogin()) {
                                item {
                                    CaregiverLoginCard(
                                        phone = uiState.phone,
                                        password = uiState.password,
                                        isSubmitting = uiState.isSubmittingLogin,
                                        errorMessage = uiState.loginError,
                                        onPhoneChange = viewModel::onPhoneChange,
                                        onPasswordChange = viewModel::onPasswordChange,
                                        onSubmit = viewModel::submitCaregiverLogin,
                                    )
                                }
                            } else {
                            item {
                                NextReminderHighlightCard(
                                    title = nextReminder.title,
                                    subtitle = nextReminder.subtitle,
                                    description = nextReminder.description,
                                    scheduledTime = nextReminder.scheduledTime,
                                    onClick = {},
                                )
                            }

                            val sectionTitle = snapshot.todayRemindersSectionTitle()
                            if (sectionTitle != null) {
                                item {
                                    Text(text = sectionTitle, color = TextSecondary)
                                }
                                items(snapshot.todayReminders.drop(1)) { reminder ->
                                    val description = if (reminder.localConfirmationRecorded) {
                                        "ثبت شد ✓"
                                    } else {
                                        reminder.friendlyDescription
                                    }
                                    TodayReminderCard(
                                        title = reminder.title,
                                        description = description,
                                        scheduledTime = reminderTimeFormatter.format(Date(reminder.scheduledForEpochMillis)),
                                        onClick = {},
                                    )
                                }
                            }

                            snapshot.emptyMedicationMessage()?.let { message ->
                                item {
                                    HomeEmptyStateCard(message = message)
                                }
                            }

                            item {
                                Text(
                                    text = "تماس با خانواده",
                                    color = TextSecondary,
                                    modifier = Modifier.fillMaxWidth(),
                                )
                            }
                            items(snapshot.priorityContacts) { contact ->
                                ContactCard(
                                    name = contact.displayName,
                                    isRecordingVoice = uiState.isRecordingVoice,
                                    onVideoCallClick = {
                                        onCallContact(
                                            contact.id,
                                            contact.elderId,
                                            "VIDEO",
                                            contact.displayName,
                                        )
                                    },
                                    onVoiceCallClick = {
                                        onCallContact(
                                            contact.id,
                                            contact.elderId,
                                            "VOICE",
                                            contact.displayName,
                                        )
                                    },
                                    onVoiceMessageClick = {
                                        if (uiState.isRecordingVoice) {
                                            viewModel.stopAndSendVoice()
                                        } else {
                                            viewModel.startRecordingVoice()
                                        }
                                    },
                                )
                            }

                            item {
                                RecordVoiceMessageCard(
                                    isRecording = uiState.isRecordingVoice,
                                    recordingSeconds = uiState.recordingDurationSeconds,
                                    onStartRecording = { viewModel.startRecordingVoice() },
                                    onStopAndSend = { viewModel.stopAndSendVoice() },
                                    onCancelRecording = { viewModel.cancelRecordingVoice() },
                                )
                            }

                            val incomingMessages = uiState.messages.filter {
                                it.direction == ir.sayda.yara.hub.core.domain.model.MessageDirection.FAMILY_TO_HUB
                            }
                            item {
                                Row(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .padding(top = 12.dp, bottom = 4.dp),
                                    horizontalArrangement = Arrangement.SpaceBetween,
                                    verticalAlignment = Alignment.CenterVertically,
                                ) {
                                    Text(
                                        text = "صندوق پیام‌های خانواده",
                                        color = TextSecondary,
                                    )
                                    if (incomingMessages.isNotEmpty()) {
                                        Surface(
                                            shape = RoundedCornerShape(12.dp),
                                            color = ir.sayda.yara.hub.ui.theme.YaraLightGreen,
                                        ) {
                                            Text(
                                                text = "${incomingMessages.size} پیام دریافتی",
                                                style = MaterialTheme.typography.labelMedium,
                                                color = ir.sayda.yara.hub.ui.theme.YaraGreen,
                                                fontWeight = FontWeight.Bold,
                                                modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp),
                                            )
                                        }
                                    }
                                }
                            }
                            if (incomingMessages.isEmpty()) {
                                item {
                                    HomeEmptyStateCard(message = "هنوز پیام جدیدی از خانواده دریافت نشده است")
                                }
                            } else {
                                items(incomingMessages.sortedByDescending { it.createdAtEpochMillis }, key = { it.id }) { msg ->
                                    if (msg.messageType == ir.sayda.yara.hub.core.domain.model.MessageType.VOICE) {
                                        val durSecs = msg.durationSeconds ?: 0
                                        val durationText = "${durSecs / 60}:${(durSecs % 60).toString().padStart(2, '0')}"
                                        ActiveVoiceMessageCard(
                                            senderName = msg.senderDisplayName ?: "خانواده",
                                            isPlaying = uiState.isPlayingAudio && uiState.playingMessageId == msg.id,
                                            durationText = durationText,
                                            onPlayPauseClick = { viewModel.togglePlayVoiceMessage(msg) },
                                        )
                                    } else if (msg.messageType == ir.sayda.yara.hub.core.domain.model.MessageType.TEXT) {
                                        FamilyTextMessageCard(
                                            senderName = msg.senderDisplayName ?: "خانواده",
                                            text = msg.body.orEmpty(),
                                            time = timeFormatter.format(Date(msg.createdAtEpochMillis)),
                                        )
                                    } else if (msg.messageType == ir.sayda.yara.hub.core.domain.model.MessageType.IMAGE) {
                                        FamilyMediaMessageCard(
                                            senderName = msg.senderDisplayName ?: "خانواده",
                                            title = "عکس از ${msg.senderDisplayName ?: "خانواده"}",
                                            text = msg.body,
                                            localFileUri = msg.localFileUri,
                                            time = timeFormatter.format(Date(msg.createdAtEpochMillis)),
                                        )
                                    } else if (msg.messageType == ir.sayda.yara.hub.core.domain.model.MessageType.VIDEO) {
                                        FamilyMediaMessageCard(
                                            senderName = msg.senderDisplayName ?: "خانواده",
                                            title = "ویدیو از ${msg.senderDisplayName ?: "خانواده"}",
                                            text = msg.body,
                                            localFileUri = msg.localFileUri,
                                            time = timeFormatter.format(Date(msg.createdAtEpochMillis)),
                                        )
                                    }
                                }
                            }
                            }

                            item {
                                ConnectionIndicator(
                                    state = connection.state,
                                    title = connection.title,
                                    subtitle = connection.subtitle,
                                )
                            }

                            if (isDebugBuild) {
                                item {
                                    DeveloperDiagnosticsCard(
                                        replicaHealth = snapshot.replicaHealth,
                                        runtimeHealth = snapshot.runtimeHealth,
                                        lastSyncEpochMillis = snapshot.lastSyncEpochMillis,
                                        isOnline = snapshot.isOnline,
                                        activeExecutionCount = snapshot.activeExecutions.size,
                                        todayReminderCount = snapshot.todayReminders.size,
                                        nextReminderEpochMillis = snapshot.nextReminderEpochMillis,
                                        pendingEvidenceCount = snapshot.pendingEvidenceCount,
                                        synchronizationAvailable = snapshot.synchronizationAvailable,
                                        registeredAlarmCount = snapshot.registeredAlarmCount,
                                    )
                                }
                            }
                        }
                    }
                }
                Box(
                    modifier = Modifier
                        .align(Alignment.BottomStart)
                        .padding(24.dp),
                ) {
                    SettingsButton(
                        onLongClick = {
                            if (isDebugBuild) {
                                onOpenDeveloperSettings()
                            } else {
                                onSettingsLongPress()
                            }
                        },
                    )
                }
            }
        }
    }
}
