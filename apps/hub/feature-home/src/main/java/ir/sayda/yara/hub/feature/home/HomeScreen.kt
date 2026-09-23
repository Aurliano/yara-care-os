package ir.sayda.yara.hub.feature.home

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.width
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.foundation.background
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.rounded.ArrowBack
import androidx.compose.material.icons.automirrored.rounded.Send
import androidx.compose.material.icons.rounded.AccessTime
import androidx.compose.material.icons.rounded.Call
import androidx.compose.material.icons.rounded.Chat
import androidx.compose.material.icons.rounded.Check
import androidx.compose.material.icons.rounded.CheckCircle
import androidx.compose.material.icons.rounded.Medication
import androidx.compose.material.icons.rounded.Mic
import androidx.compose.material.icons.rounded.Person
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.material.icons.rounded.Videocam
import androidx.compose.ui.draw.clip
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableLongStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.ui.text.style.TextOverflow
import ir.sayda.yara.hub.core.domain.model.Contact
import ir.sayda.yara.hub.core.domain.model.HomeRuntimeSnapshot
import ir.sayda.yara.hub.core.domain.model.Message
import ir.sayda.yara.hub.core.domain.model.MessageDirection
import ir.sayda.yara.hub.core.domain.model.MessageType
import ir.sayda.yara.hub.core.domain.model.TodayReminderItem
import java.util.Calendar
import ir.sayda.yara.hub.feature.home.presentation.emptyMedicationMessage
import ir.sayda.yara.hub.feature.home.presentation.needsCaregiverLogin
import ir.sayda.yara.hub.feature.home.presentation.toConnectionPresentation
import ir.sayda.yara.hub.feature.home.presentation.toNextReminderPresentation
import ir.sayda.yara.hub.ui.components.ActiveVoiceMessageCard
import ir.sayda.yara.hub.ui.components.ContactAvatar
import ir.sayda.yara.hub.ui.components.ContactCard
import ir.sayda.yara.hub.ui.components.ContactSuggestionCard
import ir.sayda.yara.hub.ui.components.FamilyMediaMessageCard
import ir.sayda.yara.hub.ui.components.FamilyTextMessageCard
import ir.sayda.yara.hub.ui.components.FullScreenMediaViewerDialog
import ir.sayda.yara.hub.ui.components.HubMediaViewerTarget
import ir.sayda.yara.hub.ui.components.HomeEmptyStateCard
import ir.sayda.yara.hub.ui.components.HomeLoadingSkeleton
import ir.sayda.yara.hub.ui.components.HubActionCard
import ir.sayda.yara.hub.ui.components.HubContactItemCard
import ir.sayda.yara.hub.ui.components.HubFooterBadges
import ir.sayda.yara.hub.ui.components.HubOutgoingMessageCard
import ir.sayda.yara.hub.ui.components.HubTopBar
import ir.sayda.yara.hub.ui.components.NextReminderHighlightCard
import ir.sayda.yara.hub.ui.components.RecordVoiceMessageCard
import ir.sayda.yara.hub.ui.components.SettingsButton
import ir.sayda.yara.hub.ui.components.TodayBackground
import ir.sayda.yara.hub.ui.components.TodayReminderCard
import ir.sayda.yara.hub.ui.presentation.formatPersianDayAndMonth
import ir.sayda.yara.hub.ui.presentation.formatPersianYear
import ir.sayda.yara.hub.ui.theme.BadgeRed
import ir.sayda.yara.hub.ui.theme.CardCallAccent
import ir.sayda.yara.hub.ui.theme.CardCallBadgeBg
import ir.sayda.yara.hub.ui.theme.CardCallBadgeText
import ir.sayda.yara.hub.ui.theme.CardCallBgEnd
import ir.sayda.yara.hub.ui.theme.CardCallBgStart
import ir.sayda.yara.hub.ui.theme.CardCallBorder
import ir.sayda.yara.hub.ui.theme.CardCallIconBg
import ir.sayda.yara.hub.ui.theme.CardMedicationAccent
import ir.sayda.yara.hub.ui.theme.CardMedicationBadgeBg
import ir.sayda.yara.hub.ui.theme.CardMedicationBadgeText
import ir.sayda.yara.hub.ui.theme.CardMedicationBgEnd
import ir.sayda.yara.hub.ui.theme.CardMedicationBgStart
import ir.sayda.yara.hub.ui.theme.CardMedicationBorder
import ir.sayda.yara.hub.ui.theme.CardMedicationIconBg
import ir.sayda.yara.hub.ui.theme.CardMessageAccent
import ir.sayda.yara.hub.ui.theme.CardMessageBadgeBg
import ir.sayda.yara.hub.ui.theme.CardMessageBadgeText
import ir.sayda.yara.hub.ui.theme.CardMessageBgEnd
import ir.sayda.yara.hub.ui.theme.CardMessageBgStart
import ir.sayda.yara.hub.ui.theme.CardMessageBorder
import ir.sayda.yara.hub.ui.theme.CardMessageIconBg
import ir.sayda.yara.hub.ui.theme.TabletBg
import ir.sayda.yara.hub.ui.theme.TextSlatePrimary
import ir.sayda.yara.hub.ui.theme.TextSlateSecondary
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
    val appTimeZone = ir.sayda.yara.hub.core.scheduling.resolveSchedulingTimeZone()
    val timeFormatter = SimpleDateFormat("HH:mm", Locale.ENGLISH).apply { timeZone = appTimeZone }
    val reminderTimeFormatter = SimpleDateFormat("HH:mm", Locale("fa", "IR")).apply { timeZone = appTimeZone }
    val connection = snapshot.toConnectionPresentation()
    val nextReminder = snapshot.toNextReminderPresentation(reminderTimeFormatter)

    val currentHour = remember(nowEpochMillis) {
        Calendar.getInstance(appTimeZone).apply { timeInMillis = nowEpochMillis }.get(Calendar.HOUR_OF_DAY)
    }
    val elderDisplayName = snapshot.elderDisplayName.ifBlank { "مادر جان" }
    val circadianGreeting = when (currentHour) {
        in 5..11 -> "صبح بخیر، $elderDisplayName"
        in 12..17 -> "عصر بخیر، $elderDisplayName"
        else -> "شامگاه خوش، $elderDisplayName"
    }

    var showMedicationSheet by remember { mutableStateOf(false) }
    var showCallSheet by remember { mutableStateOf(false) }
    var showMessagesSheet by remember { mutableStateOf(false) }

    CompositionLocalProvider(LocalLayoutDirection provides LayoutDirection.Rtl) {
        Scaffold(
            modifier = modifier.fillMaxSize(),
            containerColor = TabletBg,
        ) { innerPadding ->
            Box(modifier = Modifier.fillMaxSize()) {
                TodayBackground(modifier = Modifier.fillMaxSize())

                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(innerPadding),
                ) {
                    // Top Header Bar matching reference image
                    HubTopBar(
                        time = timeFormatter.format(now),
                        dateDayMonth = formatPersianDayAndMonth(now),
                        dateYear = formatPersianYear(now),
                        elderName = elderDisplayName,
                        greetingText = circadianGreeting,
                        isOnline = snapshot.isOnline,
                        connectionState = connection.state,
                        onLogoTap = {
                            if (isDebugBuild) onOpenDeveloperSettings()
                        },
                    )

                    if (uiState.isLoading) {
                        HomeLoadingSkeleton(
                            modifier = Modifier.padding(horizontal = 32.dp, vertical = 32.dp),
                        )
                    } else if (snapshot.needsCaregiverLogin()) {
                        Box(
                            modifier = Modifier
                                .fillMaxSize()
                                .padding(horizontal = 32.dp, vertical = 16.dp),
                            contentAlignment = Alignment.Center,
                        ) {
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
                        // Main Calm 3-Card Center Stage
                        val configuration = LocalConfiguration.current
                        val isLandscape = configuration.screenWidthDp > configuration.screenHeightDp
                        val isTabletWidth = configuration.screenWidthDp >= 720

                        Column(
                            modifier = Modifier
                                .fillMaxSize()
                                .padding(horizontal = 24.dp),
                            verticalArrangement = Arrangement.SpaceBetween,
                        ) {
                            Spacer(modifier = Modifier.height(8.dp))

                            // Dynamic state for action cards
                            val unconfirmedReminders = snapshot.todayReminders.filter { !it.localConfirmationRecorded }
                            val nextUnconfirmedToday = unconfirmedReminders.minByOrNull { it.scheduledForEpochMillis }
                            val remainingReminders = unconfirmedReminders.size

                            val priorityContacts = snapshot.priorityContacts.ifEmpty { uiState.contacts }

                            val incomingMessages = uiState.messages.filter {
                                it.direction == MessageDirection.FAMILY_TO_HUB
                            }
                            val unreadMessages = incomingMessages.filter {
                                it.status != ir.sayda.yara.hub.core.domain.model.MessageStatus.READ
                            }
                            val latestMessage = unreadMessages.maxByOrNull { it.createdAtEpochMillis }
                                ?: incomingMessages.maxByOrNull { it.createdAtEpochMillis }

                            if (isLandscape || isTabletWidth) {
                                Row(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .padding(horizontal = 8.dp),
                                    horizontalArrangement = Arrangement.spacedBy(20.dp),
                                    verticalAlignment = Alignment.CenterVertically,
                                ) {
                                    // 1. دارو (Medication Card)
                                    HubActionCard(
                                        title = "دارو",
                                        icon = Icons.Rounded.Medication,
                                        iconBgColor = CardMedicationIconBg,
                                        bgStartColor = CardMedicationBgStart,
                                        bgEndColor = CardMedicationBgEnd,
                                        borderColor = CardMedicationBorder,
                                        buttonText = "مشاهده برنامه",
                                        buttonColor = CardMedicationAccent,
                                        onButtonClick = { showMedicationSheet = true },
                                        customBodyContent = {
                                            MedicationCardBody(
                                                nextReminder = nextUnconfirmedToday,
                                                totalToday = snapshot.todayReminders.size,
                                                remainingCount = remainingReminders,
                                                timeFormatter = reminderTimeFormatter,
                                            )
                                        },
                                        badgeContent = {
                                            if (snapshot.todayReminders.isEmpty()) {
                                                CardStatusPill(
                                                    icon = Icons.Rounded.AccessTime,
                                                    text = "برنامه دارویی ثبت نشده",
                                                    bg = CardMedicationBadgeBg,
                                                    textColor = CardMedicationBadgeText,
                                                )
                                            } else if (remainingReminders > 0) {
                                                CardStatusPill(
                                                    icon = Icons.Rounded.AccessTime,
                                                    text = "$remainingReminders نوبت امروز باقی مانده",
                                                    bg = CardMedicationBadgeBg,
                                                    textColor = CardMedicationBadgeText,
                                                )
                                            } else {
                                                CardStatusPill(
                                                    icon = Icons.Rounded.CheckCircle,
                                                    text = "همه داروها مصرف شد ✓",
                                                    bg = CardMedicationBadgeBg,
                                                    textColor = CardMedicationBadgeText,
                                                )
                                            }
                                        },
                                        modifier = Modifier.weight(1f),
                                    )

                                    // 2. تماس (Call Card)
                                    HubActionCard(
                                        title = "تماس",
                                        icon = Icons.Rounded.Call,
                                        iconBgColor = CardCallIconBg,
                                        bgStartColor = CardCallBgStart,
                                        bgEndColor = CardCallBgEnd,
                                        borderColor = CardCallBorder,
                                        buttonIcon = Icons.Rounded.Call,
                                        buttonText = "تماس",
                                        buttonColor = CardCallAccent,
                                        onButtonClick = { showCallSheet = true },
                                        customBodyContent = {
                                            FamilyCallCardBody(
                                                contacts = priorityContacts,
                                                onCallContact = onCallContact,
                                            )
                                        },
                                        badgeContent = {
                                            ContactsAvatarBadge(contacts = priorityContacts)
                                        },
                                        modifier = Modifier.weight(1f),
                                    )

                                    // 3. پیام (Message Card)
                                    HubActionCard(
                                        title = "پیام",
                                        icon = Icons.Rounded.Chat,
                                        iconBgColor = CardMessageIconBg,
                                        bgStartColor = CardMessageBgStart,
                                        bgEndColor = CardMessageBgEnd,
                                        borderColor = CardMessageBorder,
                                        buttonText = "مشاهده پیام‌ها",
                                        buttonColor = CardMessageAccent,
                                        onButtonClick = { showMessagesSheet = true },
                                        customBodyContent = {
                                            MessageCardBody(
                                                unreadMessages = unreadMessages,
                                                contacts = priorityContacts,
                                                latestMessage = latestMessage,
                                                onOpenChatWithContact = { contactId ->
                                                    viewModel.selectContact(contactId)
                                                    showMessagesSheet = true
                                                },
                                            )
                                        },
                                        badgeContent = {
                                            if (unreadMessages.isNotEmpty()) {
                                                MessageCountBadge(count = unreadMessages.size)
                                            } else {
                                                CardStatusPill(
                                                    icon = Icons.Rounded.Chat,
                                                    text = "صندوق پیام‌ها",
                                                    bg = CardMessageBadgeBg,
                                                    textColor = CardMessageBadgeText,
                                                )
                                            }
                                        },
                                        modifier = Modifier.weight(1f),
                                    )
                                }
                            } else {
                                // Portrait / Narrow Screen fallback (Vertical Scrollable)
                                Column(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .verticalScroll(rememberScrollState()),
                                    verticalArrangement = Arrangement.spacedBy(16.dp),
                                ) {
                                    HubActionCard(
                                        title = "دارو",
                                        icon = Icons.Rounded.Medication,
                                        iconBgColor = CardMedicationIconBg,
                                        bgStartColor = CardMedicationBgStart,
                                        bgEndColor = CardMedicationBgEnd,
                                        borderColor = CardMedicationBorder,
                                        buttonText = "مشاهده برنامه",
                                        buttonColor = CardMedicationAccent,
                                        onButtonClick = { showMedicationSheet = true },
                                        customBodyContent = {
                                            MedicationCardBody(
                                                nextReminder = nextUnconfirmedToday,
                                                totalToday = snapshot.todayReminders.size,
                                                remainingCount = remainingReminders,
                                                timeFormatter = reminderTimeFormatter,
                                            )
                                        },
                                        badgeContent = {
                                            CardStatusPill(
                                                icon = Icons.Rounded.AccessTime,
                                                text = if (remainingReminders > 0) "$remainingReminders نوبت باقی مانده" else if (snapshot.todayReminders.isEmpty()) "برنامه دارویی ثبت نشده" else "همه داروها مصرف شد ✓",
                                                bg = CardMedicationBadgeBg,
                                                textColor = CardMedicationBadgeText,
                                            )
                                        },
                                    )

                                    HubActionCard(
                                        title = "تماس",
                                        icon = Icons.Rounded.Call,
                                        iconBgColor = CardCallIconBg,
                                        bgStartColor = CardCallBgStart,
                                        bgEndColor = CardCallBgEnd,
                                        borderColor = CardCallBorder,
                                        buttonIcon = Icons.Rounded.Call,
                                        buttonText = "تماس",
                                        buttonColor = CardCallAccent,
                                        onButtonClick = { showCallSheet = true },
                                        customBodyContent = {
                                            FamilyCallCardBody(
                                                contacts = priorityContacts,
                                                onCallContact = onCallContact,
                                            )
                                        },
                                        badgeContent = {
                                            ContactsAvatarBadge(contacts = priorityContacts)
                                        },
                                    )

                                    HubActionCard(
                                        title = "پیام",
                                        icon = Icons.Rounded.Chat,
                                        iconBgColor = CardMessageIconBg,
                                        bgStartColor = CardMessageBgStart,
                                        bgEndColor = CardMessageBgEnd,
                                        borderColor = CardMessageBorder,
                                        buttonText = "مشاهده پیام‌ها",
                                        buttonColor = CardMessageAccent,
                                        onButtonClick = { showMessagesSheet = true },
                                        customBodyContent = {
                                            MessageCardBody(
                                                unreadMessages = unreadMessages,
                                                contacts = priorityContacts,
                                                latestMessage = latestMessage,
                                                onOpenChatWithContact = { contactId ->
                                                    viewModel.selectContact(contactId)
                                                    showMessagesSheet = true
                                                },
                                            )
                                        },
                                        badgeContent = {
                                            if (unreadMessages.isNotEmpty()) {
                                                MessageCountBadge(count = unreadMessages.size)
                                            } else {
                                                CardStatusPill(
                                                    icon = Icons.Rounded.Chat,
                                                    text = "صندوق پیام‌ها",
                                                    bg = CardMessageBadgeBg,
                                                    textColor = CardMessageBadgeText,
                                                )
                                            }
                                        },
                                    )
                                }
                            }

                            Spacer(modifier = Modifier.weight(1f))

                            // Bottom reassurance badges
                            HubFooterBadges()

                            Spacer(modifier = Modifier.height(10.dp))
                        }
                    }
                }

                // Discreet Settings Access Button at Bottom Start
                Box(
                    modifier = Modifier
                        .align(Alignment.BottomStart)
                        .padding(16.dp),
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

        // --- Detail Modals / Dialogs for the 3 Cards ---

        // 1. Medication Detail Dialog
        if (showMedicationSheet) {
            MedicationScheduleDialog(
                snapshot = snapshot,
                nextReminderTitle = nextReminder.title,
                nextReminderSubtitle = nextReminder.subtitle,
                nextReminderDescription = nextReminder.description,
                nextReminderScheduledTime = nextReminder.scheduledTime,
                reminderTimeFormatter = reminderTimeFormatter,
                onDismiss = { showMedicationSheet = false },
            )
        }

        // 2. Family Call Detail Dialog
        if (showCallSheet) {
            FamilyCallDialog(
                contacts = snapshot.priorityContacts,
                isRecordingVoice = uiState.isRecordingVoice,
                onCallContact = onCallContact,
                onVoiceMessageClick = {
                    if (uiState.isRecordingVoice) {
                        viewModel.stopAndSendVoice()
                    } else {
                        viewModel.startRecordingVoice()
                    }
                },
                onDismiss = { showCallSheet = false },
            )
        }

        // 3. Family Messages Detail Dialog
        if (showMessagesSheet) {
            FamilyMessagesDialog(
                uiState = uiState,
                timeFormatter = timeFormatter,
                onStartRecording = { viewModel.startRecordingVoice() },
                onStopAndSend = { viewModel.stopAndSendVoice() },
                onCancelRecording = { viewModel.cancelRecordingVoice() },
                onTogglePlayVoice = { viewModel.togglePlayVoiceMessage(it) },
                onSendTextMessage = { viewModel.sendTextMessage(it) },
                onRetryMessage = { viewModel.retryMessage(it) },
                onMarkIncomingRead = { viewModel.markIncomingMessagesAsRead() },
                onSelectContact = { viewModel.selectContact(it) },
                onDismiss = {
                    showMessagesSheet = false
                    viewModel.selectContact(null)
                },
            )
        }
    }
}

@Composable
private fun CardStatusPill(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    text: String,
    bg: Color,
    textColor: Color,
    modifier: Modifier = Modifier,
) {
    Surface(
        shape = RoundedCornerShape(20.dp),
        color = bg,
        modifier = modifier.height(38.dp),
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 14.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(6.dp),
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = textColor,
                modifier = Modifier.size(18.dp),
            )
            Text(
                text = text,
                style = MaterialTheme.typography.labelMedium,
                color = textColor,
                fontWeight = FontWeight.SemiBold,
                fontSize = 14.sp,
            )
        }
    }
}

@Composable
private fun MedicationCardBody(
    nextReminder: TodayReminderItem?,
    totalToday: Int,
    remainingCount: Int,
    timeFormatter: SimpleDateFormat,
    modifier: Modifier = Modifier,
) {
    if (nextReminder != null) {
        Column(
            modifier = modifier.fillMaxWidth(),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center,
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(6.dp),
            ) {
                Surface(
                    shape = RoundedCornerShape(8.dp),
                    color = CardMedicationAccent.copy(alpha = 0.12f),
                ) {
                    Text(
                        text = "نوبت بعدی",
                        style = MaterialTheme.typography.labelSmall,
                        color = CardMedicationAccent,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp),
                    )
                }
                Text(
                    text = "ساعت ${timeFormatter.format(Date(nextReminder.scheduledForEpochMillis))}",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    color = CardMedicationAccent,
                    fontSize = 15.sp,
                )
            }
            Spacer(modifier = Modifier.height(3.dp))
            Text(
                text = nextReminder.title,
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
                color = TextSlatePrimary,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
                fontSize = 16.sp,
            )
        }
    } else if (totalToday > 0 && remainingCount == 0) {
        Column(
            modifier = modifier.fillMaxWidth(),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center,
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(4.dp),
            ) {
                Icon(
                    imageVector = Icons.Rounded.CheckCircle,
                    contentDescription = null,
                    tint = CardMedicationAccent,
                    modifier = Modifier.size(18.dp),
                )
                Text(
                    text = "همه داروها مصرف شد",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    color = CardMedicationAccent,
                    fontSize = 15.sp,
                )
            }
            Spacer(modifier = Modifier.height(2.dp))
            Text(
                text = "روزی سرشار از تندرستی و آرامش",
                style = MaterialTheme.typography.bodySmall,
                color = TextSlateSecondary,
                fontSize = 12.sp,
            )
        }
    } else {
        Text(
            text = "یادآوری مصرف داروها\nو مشاهده برنامه امروز",
            style = MaterialTheme.typography.bodyMedium,
            color = TextSlateSecondary,
            textAlign = TextAlign.Center,
            minLines = 2,
            maxLines = 2,
            lineHeight = 22.sp,
            fontSize = 15.sp,
        )
    }
}

@Composable
private fun FamilyCallCardBody(
    contacts: List<Contact>,
    onCallContact: (contactId: String, elderId: String, channel: String, displayName: String) -> Unit,
    modifier: Modifier = Modifier,
) {
    val displayContacts = contacts.take(3)
    if (displayContacts.size == 1) {
        val contact = displayContacts.first()
        Surface(
            onClick = {
                onCallContact(contact.id, contact.elderId, "VIDEO", contact.displayName)
            },
            shape = RoundedCornerShape(18.dp),
            color = Color.White,
            border = BorderStroke(1.5.dp, CardCallAccent.copy(alpha = 0.40f)),
            shadowElevation = 2.dp,
            modifier = modifier.fillMaxWidth(),
        ) {
            Row(
                modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                Box(contentAlignment = Alignment.BottomEnd) {
                    ContactAvatar(
                        displayName = contact.displayName,
                        photoReference = contact.photoReference,
                        size = 50.dp,
                        isPriority = true,
                    )
                    Surface(
                        shape = CircleShape,
                        color = CardCallAccent,
                        modifier = Modifier.size(18.dp),
                    ) {
                        Box(contentAlignment = Alignment.Center) {
                            Icon(
                                imageVector = Icons.Rounded.Videocam,
                                contentDescription = null,
                                tint = Color.White,
                                modifier = Modifier.size(11.dp),
                            )
                        }
                    }
                }
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = contact.displayName,
                        style = MaterialTheme.typography.titleMedium,
                        color = TextSlatePrimary,
                        fontWeight = FontWeight.Bold,
                        fontSize = 17.sp,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                    )
                    Text(
                        text = "تماس تصویری مستقیم",
                        style = MaterialTheme.typography.bodySmall,
                        color = CardCallAccent,
                        fontWeight = FontWeight.SemiBold,
                        fontSize = 12.sp,
                    )
                }
            }
        }
    } else if (displayContacts.size > 1) {
        Row(
            modifier = modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.Center,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            displayContacts.forEach { contact ->
                Surface(
                    onClick = {
                        onCallContact(contact.id, contact.elderId, "VIDEO", contact.displayName)
                    },
                    shape = RoundedCornerShape(16.dp),
                    color = Color.White.copy(alpha = 0.9f),
                    border = BorderStroke(1.dp, CardCallBorder),
                    shadowElevation = 1.dp,
                    modifier = Modifier.padding(horizontal = 4.dp),
                ) {
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally,
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 6.dp),
                    ) {
                        Box(contentAlignment = Alignment.BottomEnd) {
                            ContactAvatar(
                                displayName = contact.displayName,
                                photoReference = contact.photoReference,
                                size = 46.dp,
                                isPriority = contact.isPriority,
                            )
                            Surface(
                                shape = CircleShape,
                                color = CardCallAccent,
                                modifier = Modifier.size(16.dp),
                            ) {
                                Box(contentAlignment = Alignment.Center) {
                                    Icon(
                                        imageVector = Icons.Rounded.Call,
                                        contentDescription = null,
                                        tint = Color.White,
                                        modifier = Modifier.size(10.dp),
                                    )
                                }
                            }
                        }
                        Spacer(modifier = Modifier.height(3.dp))
                        Text(
                            text = contact.displayName.trim().take(8),
                            style = MaterialTheme.typography.labelSmall,
                            color = TextSlatePrimary,
                            fontWeight = FontWeight.Bold,
                            fontSize = 12.sp,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis,
                        )
                    }
                }
            }
        }
    } else {
        Text(
            text = "تماس با خانواده و دوستان\nو دریافت تماس‌های ورودی",
            style = MaterialTheme.typography.bodyMedium,
            color = TextSlateSecondary,
            textAlign = TextAlign.Center,
            minLines = 2,
            maxLines = 2,
            lineHeight = 22.sp,
            fontSize = 15.sp,
        )
    }
}

@Composable
private fun MessageCardBody(
    unreadMessages: List<Message>,
    contacts: List<Contact>,
    latestMessage: Message?,
    onOpenChatWithContact: (contactId: String) -> Unit,
    modifier: Modifier = Modifier,
) {
    val unreadBySender = remember(unreadMessages, contacts) {
        val list = mutableListOf<Pair<Contact, Message>>()
        val seen = mutableSetOf<String>()
        for (msg in unreadMessages.sortedByDescending { it.createdAtEpochMillis }) {
            val contact = contacts.firstOrNull { it.displayName == msg.senderDisplayName }
                ?: (if (contacts.size == 1) contacts.first() else null)
            if (contact != null && seen.add(contact.id)) {
                list.add(contact to msg)
            }
        }
        list
    }

    if (unreadBySender.size >= 2) {
        Column(
            modifier = modifier.fillMaxWidth(),
            verticalArrangement = Arrangement.spacedBy(6.dp),
        ) {
            unreadBySender.take(2).forEach { (contact, msg) ->
                Surface(
                    onClick = { onOpenChatWithContact(contact.id) },
                    shape = RoundedCornerShape(14.dp),
                    color = Color.White.copy(alpha = 0.90f),
                    border = BorderStroke(1.dp, CardMessageBorder.copy(alpha = 0.7f)),
                    shadowElevation = 1.dp,
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Row(
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 5.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        ContactAvatar(
                            displayName = contact.displayName,
                            photoReference = contact.photoReference,
                            size = 34.dp,
                            unread = true,
                        )
                        Column(modifier = Modifier.weight(1f)) {
                            Row(
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(4.dp),
                            ) {
                                Text(
                                    text = contact.displayName,
                                    style = MaterialTheme.typography.titleSmall,
                                    fontWeight = FontWeight.Bold,
                                    color = CardMessageAccent,
                                    fontSize = 13.sp,
                                    maxLines = 1,
                                    overflow = TextOverflow.Ellipsis,
                                )
                                Surface(
                                    shape = CircleShape,
                                    color = BadgeRed,
                                    modifier = Modifier.size(6.dp),
                                ) {}
                            }
                            val snippet = when (msg.messageType) {
                                MessageType.VOICE -> "🎙️ پیام صوتی"
                                MessageType.IMAGE -> "📷 عکس جدید"
                                MessageType.VIDEO -> "🎥 ویدیو"
                                MessageType.TEXT -> msg.body ?: "پیام جدید"
                            }
                            Text(
                                text = snippet,
                                style = MaterialTheme.typography.bodySmall,
                                color = TextSlatePrimary,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis,
                                fontSize = 12.sp,
                            )
                        }
                    }
                }
            }
        }
    } else if (unreadBySender.size == 1) {
        val (contact, msg) = unreadBySender.first()
        Surface(
            onClick = { onOpenChatWithContact(contact.id) },
            shape = RoundedCornerShape(18.dp),
            color = Color.White,
            border = BorderStroke(1.5.dp, CardMessageAccent.copy(alpha = 0.45f)),
            shadowElevation = 2.dp,
            modifier = modifier.fillMaxWidth(),
        ) {
            Row(
                modifier = Modifier.padding(horizontal = 10.dp, vertical = 8.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                ContactAvatar(
                    displayName = contact.displayName,
                    photoReference = contact.photoReference,
                    size = 46.dp,
                    unread = true,
                )
                Column(
                    modifier = Modifier.weight(1f),
                    verticalArrangement = Arrangement.spacedBy(2.dp),
                ) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(6.dp),
                    ) {
                        Surface(
                            shape = RoundedCornerShape(6.dp),
                            color = BadgeRed.copy(alpha = 0.12f),
                        ) {
                            Text(
                                text = "پیام جدید",
                                style = MaterialTheme.typography.labelSmall,
                                color = BadgeRed,
                                fontWeight = FontWeight.Bold,
                                modifier = Modifier.padding(horizontal = 5.dp, vertical = 1.dp),
                                fontSize = 11.sp,
                            )
                        }
                        Text(
                            text = contact.displayName,
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold,
                            color = CardMessageAccent,
                            fontSize = 15.sp,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis,
                        )
                    }
                    val snippet = when (msg.messageType) {
                        MessageType.VOICE -> "🎙️ پیام صوتی"
                        MessageType.IMAGE -> "📷 عکس خانوادگی"
                        MessageType.VIDEO -> "🎥 ویدیو"
                        MessageType.TEXT -> msg.body ?: "پیام متنی"
                    }
                    Text(
                        text = snippet,
                        style = MaterialTheme.typography.bodyMedium,
                        color = TextSlatePrimary,
                        fontWeight = FontWeight.SemiBold,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                        fontSize = 14.sp,
                    )
                }
            }
        }
    } else if (latestMessage != null) {
        val contact = contacts.firstOrNull { it.displayName == latestMessage.senderDisplayName }
            ?: (if (contacts.size == 1) contacts.first() else null)
        Surface(
            onClick = {
                if (contact != null) onOpenChatWithContact(contact.id)
            },
            shape = RoundedCornerShape(18.dp),
            color = Color.White.copy(alpha = 0.9f),
            border = BorderStroke(1.dp, CardMessageBorder),
            modifier = modifier.fillMaxWidth(),
        ) {
            Row(
                modifier = Modifier.padding(horizontal = 10.dp, vertical = 8.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                ContactAvatar(
                    displayName = contact?.displayName ?: latestMessage.senderDisplayName ?: "خ",
                    photoReference = contact?.photoReference,
                    size = 44.dp,
                    unread = false,
                )
                Column(
                    modifier = Modifier.weight(1f),
                    verticalArrangement = Arrangement.spacedBy(2.dp),
                ) {
                    Text(
                        text = contact?.displayName ?: latestMessage.senderDisplayName ?: "پیام",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold,
                        color = CardMessageAccent,
                        fontSize = 15.sp,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                    )
                    val snippet = when (latestMessage.messageType) {
                        MessageType.VOICE -> "🎙️ پیام صوتی"
                        MessageType.IMAGE -> "📷 عکس خانوادگی"
                        MessageType.VIDEO -> "🎥 ویدیو"
                        MessageType.TEXT -> latestMessage.body ?: "پیام متنی"
                    }
                    Text(
                        text = snippet,
                        style = MaterialTheme.typography.bodySmall,
                        color = TextSlateSecondary,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                        fontSize = 13.sp,
                    )
                }
            }
        }
    } else {
        Text(
            text = "مشاهده پیام‌ها و\nعکس‌های عزیزانتان",
            style = MaterialTheme.typography.bodyMedium,
            color = TextSlateSecondary,
            textAlign = TextAlign.Center,
            minLines = 2,
            maxLines = 2,
            lineHeight = 22.sp,
            fontSize = 15.sp,
        )
    }
}

@Composable
private fun ContactsAvatarBadge(
    contacts: List<Contact>,
    modifier: Modifier = Modifier,
) {
    Surface(
        shape = RoundedCornerShape(20.dp),
        color = CardCallBadgeBg,
        modifier = modifier.height(38.dp),
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 14.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Row(horizontalArrangement = Arrangement.spacedBy((-6).dp)) {
                val displayContacts = contacts.take(3)
                if (displayContacts.isEmpty()) {
                    Surface(
                        shape = CircleShape,
                        color = Color.White,
                        border = BorderStroke(1.5.dp, CardCallBorder),
                        modifier = Modifier.size(24.dp),
                    ) {
                        Box(contentAlignment = Alignment.Center) {
                            Icon(
                                imageVector = Icons.Rounded.Person,
                                contentDescription = null,
                                tint = CardCallAccent,
                                modifier = Modifier.size(16.dp),
                            )
                        }
                    }
                } else {
                    displayContacts.forEach { contact ->
                        ContactAvatar(
                            displayName = contact.displayName,
                            photoReference = contact.photoReference,
                            size = 24.dp,
                            isPriority = contact.isPriority,
                        )
                    }
                }
            }
            Text(
                text = if (contacts.isNotEmpty()) "${contacts.size} مخاطب اصلی" else "خانواده و نزدیکان",
                style = MaterialTheme.typography.labelMedium,
                color = CardCallBadgeText,
                fontWeight = FontWeight.SemiBold,
                fontSize = 14.sp,
            )
        }
    }
}

@Composable
private fun MessageCountBadge(
    count: Int,
    modifier: Modifier = Modifier,
) {
    Surface(
        shape = RoundedCornerShape(20.dp),
        color = CardMessageBadgeBg,
        modifier = modifier.height(38.dp),
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 14.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Surface(
                shape = CircleShape,
                color = BadgeRed,
                modifier = Modifier.size(20.dp),
            ) {
                Box(contentAlignment = Alignment.Center) {
                    Text(
                        text = "$count",
                        color = Color.White,
                        style = MaterialTheme.typography.labelMedium,
                        fontWeight = FontWeight.Bold,
                        fontSize = 12.sp,
                    )
                }
            }
            Text(
                text = "$count پیام جدید",
                style = MaterialTheme.typography.labelMedium,
                color = CardMessageBadgeText,
                fontWeight = FontWeight.SemiBold,
                fontSize = 14.sp,
            )
        }
    }
}

// -------------------------------------------------------------
// DETAIL MODALS / DIALOGS
// -------------------------------------------------------------

@Composable
private fun MedicationScheduleDialog(
    snapshot: HomeRuntimeSnapshot,
    nextReminderTitle: String,
    nextReminderSubtitle: String,
    nextReminderDescription: String?,
    nextReminderScheduledTime: String?,
    reminderTimeFormatter: SimpleDateFormat,
    onDismiss: () -> Unit,
) {
    Dialog(
        onDismissRequest = onDismiss,
        properties = DialogProperties(usePlatformDefaultWidth = false),
    ) {
        BackHandler(onBack = onDismiss)
        Surface(
            shape = RoundedCornerShape(32.dp),
            color = TabletBg,
            border = BorderStroke(1.5.dp, CardMedicationBorder),
            shadowElevation = 8.dp,
            modifier = Modifier
                .fillMaxWidth(0.92f)
                .fillMaxHeight(0.90f),
        ) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(horizontal = 32.dp, vertical = 24.dp),
            ) {
                // Dialog Header
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(12.dp),
                    ) {
                        Surface(
                            shape = CircleShape,
                            color = CardMedicationIconBg,
                            modifier = Modifier.size(44.dp),
                        ) {
                            Box(contentAlignment = Alignment.Center) {
                                Icon(
                                    imageVector = Icons.Rounded.Medication,
                                    contentDescription = null,
                                    tint = Color.White,
                                    modifier = Modifier.size(26.dp),
                                )
                            }
                        }
                        Text(
                            text = "برنامه دارویی امروز",
                            style = MaterialTheme.typography.headlineLarge,
                            color = TextSlatePrimary,
                            fontWeight = FontWeight.Bold,
                            fontSize = 26.sp,
                        )
                    }

                    // Back / Return Button
                    Surface(
                        onClick = onDismiss,
                        shape = RoundedCornerShape(20.dp),
                        color = CardMedicationAccent,
                        modifier = Modifier.height(44.dp),
                    ) {
                        Row(
                            modifier = Modifier.padding(horizontal = 18.dp),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(8.dp),
                        ) {
                            Icon(
                                imageVector = Icons.AutoMirrored.Rounded.ArrowBack,
                                contentDescription = "بازگشت",
                                tint = Color.White,
                                modifier = Modifier.size(20.dp),
                            )
                            Text(
                                text = "بازگشت",
                                style = MaterialTheme.typography.titleMedium,
                                color = Color.White,
                                fontWeight = FontWeight.Bold,
                                fontSize = 16.sp,
                            )
                        }
                    }
                }

                Spacer(modifier = Modifier.height(20.dp))

                // Content List
                LazyColumn(
                    modifier = Modifier.fillMaxSize(),
                    verticalArrangement = Arrangement.spacedBy(16.dp),
                    contentPadding = PaddingValues(bottom = 24.dp),
                ) {
                    item {
                        NextReminderHighlightCard(
                            title = nextReminderTitle,
                            subtitle = nextReminderSubtitle,
                            description = nextReminderDescription,
                            scheduledTime = nextReminderScheduledTime,
                            onClick = {},
                        )
                    }

                    if (snapshot.todayReminders.size > 1) {
                        item {
                            Text(
                                text = "سایر نوبت‌های امروز",
                                style = MaterialTheme.typography.titleMedium,
                                color = TextSlateSecondary,
                                fontWeight = FontWeight.SemiBold,
                                modifier = Modifier.padding(top = 8.dp),
                            )
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
                }
            }
        }
    }
}

@Composable
private fun FamilyCallDialog(
    contacts: List<Contact>,
    isRecordingVoice: Boolean,
    onCallContact: (contactId: String, elderId: String, channel: String, displayName: String) -> Unit,
    onVoiceMessageClick: () -> Unit,
    onDismiss: () -> Unit,
) {
    Dialog(
        onDismissRequest = onDismiss,
        properties = DialogProperties(usePlatformDefaultWidth = false),
    ) {
        BackHandler(onBack = onDismiss)
        Surface(
            shape = RoundedCornerShape(32.dp),
            color = TabletBg,
            border = BorderStroke(1.5.dp, CardCallBorder),
            shadowElevation = 8.dp,
            modifier = Modifier
                .fillMaxWidth(0.92f)
                .fillMaxHeight(0.90f),
        ) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(horizontal = 32.dp, vertical = 24.dp),
            ) {
                // Dialog Header
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(12.dp),
                    ) {
                        Surface(
                            shape = CircleShape,
                            color = CardCallIconBg,
                            modifier = Modifier.size(44.dp),
                        ) {
                            Box(contentAlignment = Alignment.Center) {
                                Icon(
                                    imageVector = Icons.Rounded.Call,
                                    contentDescription = null,
                                    tint = Color.White,
                                    modifier = Modifier.size(24.dp),
                                )
                            }
                        }
                        Text(
                            text = "تماس با خانواده و نزدیکان",
                            style = MaterialTheme.typography.headlineLarge,
                            color = TextSlatePrimary,
                            fontWeight = FontWeight.Bold,
                            fontSize = 26.sp,
                        )
                    }

                    // Back Button
                    Surface(
                        onClick = onDismiss,
                        shape = RoundedCornerShape(20.dp),
                        color = CardCallAccent,
                        modifier = Modifier.height(44.dp),
                    ) {
                        Row(
                            modifier = Modifier.padding(horizontal = 18.dp),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(8.dp),
                        ) {
                            Icon(
                                imageVector = Icons.AutoMirrored.Rounded.ArrowBack,
                                contentDescription = "بازگشت",
                                tint = Color.White,
                                modifier = Modifier.size(20.dp),
                            )
                            Text(
                                text = "بازگشت",
                                style = MaterialTheme.typography.titleMedium,
                                color = Color.White,
                                fontWeight = FontWeight.Bold,
                                fontSize = 16.sp,
                            )
                        }
                    }
                }

                Spacer(modifier = Modifier.height(20.dp))

                if (contacts.isEmpty()) {
                    HomeEmptyStateCard(message = "مخاطبی برای برقراری تماس ثبت نشده است")
                } else {
                    LazyVerticalGrid(
                        columns = GridCells.Adaptive(minSize = 220.dp),
                        modifier = Modifier.fillMaxSize(),
                        horizontalArrangement = Arrangement.spacedBy(16.dp),
                        verticalArrangement = Arrangement.spacedBy(16.dp),
                        contentPadding = PaddingValues(bottom = 24.dp),
                    ) {
                        items(contacts, key = { it.id }) { contact ->
                            ContactSuggestionCard(
                                displayName = contact.displayName,
                                relationship = if (contact.isPriority) "مخاطب اصلی" else "خانواده",
                                photoReference = contact.photoReference,
                                isPriority = contact.isPriority,
                                actionButtonText = "تماس تصویری",
                                actionButtonIcon = Icons.Rounded.Videocam,
                                actionButtonColor = CardCallAccent,
                                onActionClick = {
                                    onCallContact(
                                        contact.id,
                                        contact.elderId,
                                        "VIDEO",
                                        contact.displayName,
                                    )
                                },
                                secondaryButtonText = "تماس صوتی",
                                secondaryButtonIcon = Icons.Rounded.Call,
                                onSecondaryClick = {
                                    onCallContact(
                                        contact.id,
                                        contact.elderId,
                                        "VOICE",
                                        contact.displayName,
                                    )
                                },
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun FamilyMessagesDialog(
    uiState: HomeUiState,
    timeFormatter: SimpleDateFormat,
    onStartRecording: () -> Unit,
    onStopAndSend: () -> Unit,
    onCancelRecording: () -> Unit,
    onTogglePlayVoice: (ir.sayda.yara.hub.core.domain.model.Message) -> Unit,
    onSendTextMessage: (String) -> Unit,
    onRetryMessage: (ir.sayda.yara.hub.core.domain.model.Message) -> Unit,
    onMarkIncomingRead: () -> Unit,
    onSelectContact: (String?) -> Unit,
    onDismiss: () -> Unit,
) {
    val selectedContactId = uiState.selectedContactId
    val selectedContact = remember(selectedContactId, uiState.contacts) {
        uiState.contacts.firstOrNull { it.id == selectedContactId }
    }

    Dialog(
        onDismissRequest = onDismiss,
        properties = DialogProperties(usePlatformDefaultWidth = false),
    ) {
        Surface(
            shape = RoundedCornerShape(32.dp),
            color = TabletBg,
            border = BorderStroke(1.5.dp, CardMessageBorder),
            shadowElevation = 8.dp,
            modifier = Modifier
                .fillMaxWidth(0.92f)
                .fillMaxHeight(0.90f),
        ) {
            if (selectedContact == null) {
                // LEVEL 1: CONTACT LIST
                BackHandler(onBack = onDismiss)

                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(horizontal = 32.dp, vertical = 24.dp),
                ) {
                    // Header
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(12.dp),
                        ) {
                            Surface(
                                shape = CircleShape,
                                color = CardMessageIconBg,
                                modifier = Modifier.size(44.dp),
                            ) {
                                Box(contentAlignment = Alignment.Center) {
                                    Icon(
                                        imageVector = Icons.Rounded.Chat,
                                        contentDescription = null,
                                        tint = Color.White,
                                        modifier = Modifier.size(24.dp),
                                    )
                                }
                            }
                            Column {
                                Text(
                                    text = "پیام‌ها و ارتباط با خانواده",
                                    style = MaterialTheme.typography.headlineLarge,
                                    color = TextSlatePrimary,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 24.sp,
                                )
                                Text(
                                    text = "انتخاب مخاطب برای گفتگو",
                                    style = MaterialTheme.typography.bodyMedium,
                                    color = TextSlateSecondary,
                                    fontSize = 14.sp,
                                )
                            }
                        }

                        // Back Button (Exits dialog to Home)
                        Surface(
                            onClick = onDismiss,
                            shape = RoundedCornerShape(20.dp),
                            color = CardMessageAccent,
                            modifier = Modifier.height(44.dp),
                        ) {
                            Row(
                                modifier = Modifier.padding(horizontal = 18.dp),
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(8.dp),
                            ) {
                                Icon(
                                    imageVector = Icons.AutoMirrored.Rounded.ArrowBack,
                                    contentDescription = "بازگشت",
                                    tint = Color.White,
                                    modifier = Modifier.size(20.dp),
                                )
                                Text(
                                    text = "بازگشت",
                                    style = MaterialTheme.typography.titleMedium,
                                    color = Color.White,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 16.sp,
                                )
                            }
                        }
                    }

                    Spacer(modifier = Modifier.height(20.dp))

                    if (uiState.contacts.isEmpty()) {
                        HomeEmptyStateCard(message = "مخاطبی برای ارسال یا دریافت پیام ثبت نشده است")
                    } else {
                        LazyVerticalGrid(
                            columns = GridCells.Adaptive(minSize = 220.dp),
                            modifier = Modifier.fillMaxSize(),
                            horizontalArrangement = Arrangement.spacedBy(16.dp),
                            verticalArrangement = Arrangement.spacedBy(16.dp),
                            contentPadding = PaddingValues(bottom = 24.dp),
                        ) {
                            items(uiState.contacts, key = { it.id }) { contact ->
                                val contactUnread = uiState.messages.count {
                                    it.direction == MessageDirection.FAMILY_TO_HUB &&
                                        it.status != ir.sayda.yara.hub.core.domain.model.MessageStatus.READ &&
                                        (it.senderDisplayName == contact.displayName || uiState.contacts.size == 1)
                                }
                                ContactSuggestionCard(
                                    displayName = contact.displayName,
                                    relationship = if (contact.isPriority) "مخاطب اصلی" else "خانواده",
                                    photoReference = contact.photoReference,
                                    isPriority = contact.isPriority,
                                    unreadCount = contactUnread,
                                    actionButtonText = "گفتگو و پیام‌ها",
                                    actionButtonIcon = Icons.Rounded.Chat,
                                    actionButtonColor = CardMessageAccent,
                                    onActionClick = { onSelectContact(contact.id) },
                                )
                            }
                        }
                    }
                }
            } else {
                // LEVEL 2: CONVERSATION WITH SELECTED CONTACT
                BackHandler(onBack = { onSelectContact(null) })

                val conversationMessages = remember(uiState.messages, selectedContact, uiState.contacts.size) {
                    if (uiState.contacts.size <= 1) {
                        uiState.messages
                    } else {
                        uiState.messages.filter { msg ->
                            msg.direction == MessageDirection.HUB_TO_FAMILY ||
                                msg.senderDisplayName == selectedContact.displayName
                        }
                    }
                }

                val unreadIncomingMessages = remember(conversationMessages) {
                    conversationMessages.filter {
                        it.direction == MessageDirection.FAMILY_TO_HUB &&
                            it.status != ir.sayda.yara.hub.core.domain.model.MessageStatus.READ
                    }
                }

                LaunchedEffect(selectedContact.id) {
                    onMarkIncomingRead()
                }
                LaunchedEffect(unreadIncomingMessages.size) {
                    if (unreadIncomingMessages.isNotEmpty()) {
                        onMarkIncomingRead()
                    }
                }

                var customTextMessage by remember { mutableStateOf("") }
                var viewerTarget by remember { mutableStateOf<HubMediaViewerTarget?>(null) }

                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(horizontal = 32.dp, vertical = 24.dp),
                ) {
                    // Conversation Header
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(14.dp),
                        ) {
                            ContactAvatar(
                                displayName = selectedContact.displayName,
                                photoReference = selectedContact.photoReference,
                                size = 48.dp,
                                isPriority = selectedContact.isPriority,
                            )
                            Column {
                                Text(
                                    text = "گفتگو با ${selectedContact.displayName}",
                                    style = MaterialTheme.typography.headlineLarge,
                                    color = TextSlatePrimary,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 24.sp,
                                )
                                Text(
                                    text = if (selectedContact.isPriority) "مخاطب اصلی • ارتباط مستقیم" else "پیام متنی و صوتی",
                                    style = MaterialTheme.typography.bodyMedium,
                                    color = TextSlateSecondary,
                                    fontSize = 14.sp,
                                )
                            }
                        }

                        // Back Button (Returns to Contact List)
                        Surface(
                            onClick = { onSelectContact(null) },
                            shape = RoundedCornerShape(20.dp),
                            color = CardMessageAccent,
                            modifier = Modifier.height(48.dp),
                        ) {
                            Row(
                                modifier = Modifier.padding(horizontal = 20.dp),
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(8.dp),
                            ) {
                                Icon(
                                    imageVector = Icons.AutoMirrored.Rounded.ArrowBack,
                                    contentDescription = "بازگشت به مخاطبین",
                                    tint = Color.White,
                                    modifier = Modifier.size(20.dp),
                                )
                                Text(
                                    text = "بازگشت به مخاطبین",
                                    style = MaterialTheme.typography.titleMedium,
                                    color = Color.White,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 15.sp,
                                )
                            }
                        }
                    }

                    Spacer(modifier = Modifier.height(14.dp))

                    val sortedMessages = remember(conversationMessages) {
                        conversationMessages.sortedBy { it.createdAtEpochMillis }
                    }
                    val conversationListState = rememberLazyListState()

                    LaunchedEffect(selectedContact.id, sortedMessages.size) {
                        if (sortedMessages.isNotEmpty()) {
                            conversationListState.scrollToItem(sortedMessages.size - 1)
                        }
                    }

                    // 1. Scrollable Message History (weight 1f - only history scrolls)
                    LazyColumn(
                        state = conversationListState,
                        modifier = Modifier
                            .fillMaxWidth()
                            .weight(1f),
                        verticalArrangement = Arrangement.spacedBy(14.dp),
                        contentPadding = PaddingValues(top = 4.dp, bottom = 8.dp),
                    ) {
                        if (sortedMessages.isEmpty()) {
                            item {
                                HomeEmptyStateCard(message = "هنوز پیامی با ${selectedContact.displayName} مبادله نشده است. می‌توانید با ضبط صدا یا نوشتن پیام، گفتگو را شروع کنید.")
                            }
                        } else {
                            items(sortedMessages, key = { it.id }) { msg ->
                                if (msg.direction == MessageDirection.HUB_TO_FAMILY) {
                                    val statusText = when (msg.status) {
                                        ir.sayda.yara.hub.core.domain.model.MessageStatus.PENDING -> "در حال ارسال..."
                                        ir.sayda.yara.hub.core.domain.model.MessageStatus.SENT -> "ارسال شد ✓"
                                        ir.sayda.yara.hub.core.domain.model.MessageStatus.DELIVERED -> "تحویل شد ✓"
                                        ir.sayda.yara.hub.core.domain.model.MessageStatus.READ -> "خوانده شد ✓✓"
                                        ir.sayda.yara.hub.core.domain.model.MessageStatus.FAILED -> "خطا در ارسال"
                                    }
                                    val isFailed = msg.status == ir.sayda.yara.hub.core.domain.model.MessageStatus.FAILED
                                    if (msg.messageType == MessageType.VOICE) {
                                        val durSecs = msg.durationSeconds ?: 0
                                        val durationText = "${durSecs / 60}:${(durSecs % 60).toString().padStart(2, '0')}"
                                        HubOutgoingMessageCard(
                                            text = null,
                                            time = timeFormatter.format(Date(msg.createdAtEpochMillis)),
                                            statusText = statusText,
                                            isVoice = true,
                                            durationText = durationText,
                                            isPlaying = uiState.isPlayingAudio && uiState.playingMessageId == msg.id,
                                            isFailed = isFailed,
                                            onPlayPauseClick = { onTogglePlayVoice(msg) },
                                            onRetryClick = { onRetryMessage(msg) },
                                        )
                                    } else {
                                        HubOutgoingMessageCard(
                                            text = msg.body,
                                            time = timeFormatter.format(Date(msg.createdAtEpochMillis)),
                                            statusText = statusText,
                                            isVoice = false,
                                            isFailed = isFailed,
                                            onRetryClick = { onRetryMessage(msg) },
                                        )
                                    }
                                } else {
                                    if (msg.messageType == MessageType.VOICE) {
                                        val durSecs = msg.durationSeconds ?: 0
                                        val durationText = "${durSecs / 60}:${(durSecs % 60).toString().padStart(2, '0')}"
                                        ActiveVoiceMessageCard(
                                            senderName = msg.senderDisplayName ?: selectedContact.displayName,
                                            isPlaying = uiState.isPlayingAudio && uiState.playingMessageId == msg.id,
                                            durationText = durationText,
                                            onPlayPauseClick = { onTogglePlayVoice(msg) },
                                        )
                                    } else if (msg.messageType == MessageType.TEXT) {
                                        FamilyTextMessageCard(
                                            senderName = msg.senderDisplayName ?: selectedContact.displayName,
                                            text = msg.body.orEmpty(),
                                            time = timeFormatter.format(Date(msg.createdAtEpochMillis)),
                                        )
                                    } else if (msg.messageType == MessageType.IMAGE || msg.messageType == MessageType.VIDEO) {
                                        FamilyMediaMessageCard(
                                            senderName = msg.senderDisplayName ?: selectedContact.displayName,
                                            title = if (msg.messageType == MessageType.IMAGE) {
                                                "عکس از ${msg.senderDisplayName ?: selectedContact.displayName}"
                                            } else {
                                                "ویدیو از ${msg.senderDisplayName ?: selectedContact.displayName}"
                                            },
                                            text = msg.body,
                                            localFileUri = msg.localFileUri,
                                            time = timeFormatter.format(Date(msg.createdAtEpochMillis)),
                                            isVideo = msg.messageType == MessageType.VIDEO,
                                            onClick = if (msg.localFileUri != null) {
                                                {
                                                    viewerTarget = HubMediaViewerTarget(
                                                        localFileUri = msg.localFileUri,
                                                        isVideo = msg.messageType == MessageType.VIDEO,
                                                        title = if (msg.messageType == MessageType.IMAGE) {
                                                            "عکس ارسالی از ${msg.senderDisplayName ?: selectedContact.displayName}"
                                                        } else {
                                                            "ویدیوی ارسالی از ${msg.senderDisplayName ?: selectedContact.displayName}"
                                                        },
                                                        caption = msg.body,
                                                    )
                                                }
                                            } else null,
                                        )
                                    }
                                }
                            }
                        }
                    }

                    Spacer(modifier = Modifier.height(10.dp))

                    // 2. Fixed Bottom Composer
                    if (uiState.isRecordingVoice) {
                        // Expanding Recording Bar (visible only during active recording)
                        Surface(
                            shape = RoundedCornerShape(20.dp),
                            color = Color(0xFFFEF2F2),
                            border = BorderStroke(1.5.dp, Color(0xFFFECACA)),
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(64.dp),
                        ) {
                            Row(
                                modifier = Modifier
                                    .fillMaxSize()
                                    .padding(horizontal = 20.dp),
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.SpaceBetween,
                            ) {
                                Row(
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.spacedBy(10.dp),
                                ) {
                                    Box(
                                        modifier = Modifier
                                            .size(14.dp)
                                            .clip(CircleShape)
                                            .background(Color(0xFFEF4444))
                                    )
                                    Text(
                                        text = "در حال ضبط صدا: ${uiState.recordingDurationSeconds} ثانیه",
                                        style = MaterialTheme.typography.titleMedium,
                                        color = Color(0xFF991B1B),
                                        fontWeight = FontWeight.Bold,
                                        fontSize = 16.sp,
                                    )
                                }

                                Row(
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.spacedBy(10.dp),
                                ) {
                                    Surface(
                                        onClick = onCancelRecording,
                                        shape = RoundedCornerShape(14.dp),
                                        color = Color(0xFFF1F5F9),
                                        modifier = Modifier.height(44.dp),
                                    ) {
                                        Box(
                                            modifier = Modifier.padding(horizontal = 16.dp),
                                            contentAlignment = Alignment.Center,
                                        ) {
                                            Text(
                                                text = "انصراف",
                                                style = MaterialTheme.typography.labelLarge,
                                                color = Color(0xFF64748B),
                                                fontWeight = FontWeight.SemiBold,
                                                fontSize = 14.sp,
                                            )
                                        }
                                    }

                                    Surface(
                                        onClick = onStopAndSend,
                                        shape = RoundedCornerShape(14.dp),
                                        color = Color(0xFF059669),
                                        modifier = Modifier.height(44.dp),
                                    ) {
                                        Row(
                                            modifier = Modifier.padding(horizontal = 18.dp),
                                            verticalAlignment = Alignment.CenterVertically,
                                            horizontalArrangement = Arrangement.spacedBy(6.dp),
                                        ) {
                                            Icon(
                                                imageVector = Icons.Rounded.Check,
                                                contentDescription = null,
                                                tint = Color.White,
                                                modifier = Modifier.size(18.dp),
                                            )
                                            Text(
                                                text = "ارسال صدا",
                                                style = MaterialTheme.typography.labelLarge,
                                                color = Color.White,
                                                fontWeight = FontWeight.Bold,
                                                fontSize = 15.sp,
                                            )
                                        }
                                    }
                                }
                            }
                        }
                    } else {
                        // Compact Quick Replies + Compact Input Bar
                        Column(
                            modifier = Modifier.fillMaxWidth(),
                            verticalArrangement = Arrangement.spacedBy(8.dp),
                        ) {
                            // Horizontal compact quick replies chips
                            Row(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .horizontalScroll(rememberScrollState()),
                                horizontalArrangement = Arrangement.spacedBy(8.dp),
                                verticalAlignment = Alignment.CenterVertically,
                            ) {
                                listOf("سلام", "خوبم ممنون", "تماس بگیرید", "متشکرم").forEach { phrase ->
                                    Surface(
                                        onClick = { onSendTextMessage(phrase) },
                                        shape = RoundedCornerShape(16.dp),
                                        color = CardMessageAccent.copy(alpha = 0.10f),
                                        border = BorderStroke(1.dp, CardMessageAccent.copy(alpha = 0.30f)),
                                        modifier = Modifier.height(42.dp),
                                    ) {
                                        Box(
                                            modifier = Modifier.padding(horizontal = 16.dp),
                                            contentAlignment = Alignment.Center,
                                        ) {
                                            Text(
                                                text = phrase,
                                                style = MaterialTheme.typography.labelMedium,
                                                color = CardMessageAccent,
                                                fontWeight = FontWeight.Bold,
                                                fontSize = 14.sp,
                                            )
                                        }
                                    }
                                }
                            }

                            // Normal Input Bar: Mic button + Text Input + Send button
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.spacedBy(10.dp),
                                verticalAlignment = Alignment.CenterVertically,
                            ) {
                                Surface(
                                    onClick = onStartRecording,
                                    shape = CircleShape,
                                    color = CardMessageAccent.copy(alpha = 0.12f),
                                    border = BorderStroke(1.5.dp, CardMessageAccent.copy(alpha = 0.35f)),
                                    modifier = Modifier.size(54.dp),
                                ) {
                                    Box(contentAlignment = Alignment.Center) {
                                        Icon(
                                            imageVector = Icons.Rounded.Mic,
                                            contentDescription = "ضبط صدا",
                                            tint = CardMessageAccent,
                                            modifier = Modifier.size(26.dp),
                                        )
                                    }
                                }

                                androidx.compose.material3.OutlinedTextField(
                                    value = customTextMessage,
                                    onValueChange = { customTextMessage = it },
                                    placeholder = {
                                        Text(
                                            "نوشتن پیام دلخواه برای ${selectedContact.displayName}...",
                                            style = MaterialTheme.typography.bodyMedium,
                                            color = TextSlateSecondary,
                                        )
                                    },
                                    singleLine = true,
                                    shape = RoundedCornerShape(18.dp),
                                    modifier = Modifier
                                        .weight(1f)
                                        .height(54.dp),
                                )

                                Surface(
                                    onClick = {
                                        if (customTextMessage.isNotBlank()) {
                                            onSendTextMessage(customTextMessage)
                                            customTextMessage = ""
                                        }
                                    },
                                    shape = RoundedCornerShape(18.dp),
                                    color = if (customTextMessage.isNotBlank()) CardMessageAccent else CardMessageAccent.copy(alpha = 0.35f),
                                    modifier = Modifier.height(54.dp),
                                ) {
                                    Row(
                                        modifier = Modifier.padding(horizontal = 18.dp),
                                        verticalAlignment = Alignment.CenterVertically,
                                        horizontalArrangement = Arrangement.spacedBy(6.dp),
                                    ) {
                                        Icon(
                                            imageVector = Icons.AutoMirrored.Rounded.Send,
                                            contentDescription = "ارسال",
                                            tint = Color.White,
                                            modifier = Modifier.size(18.dp),
                                        )
                                        Text(
                                            text = "ارسال",
                                            style = MaterialTheme.typography.titleMedium,
                                            color = Color.White,
                                            fontWeight = FontWeight.Bold,
                                            fontSize = 15.sp,
                                        )
                                    }
                                }
                            }
                        }
                    }
                }

                val currentTarget = viewerTarget
                if (currentTarget != null) {
                    FullScreenMediaViewerDialog(
                        target = currentTarget,
                        onDismiss = { viewerTarget = null },
                    )
                }
            }
        }
    }
}
