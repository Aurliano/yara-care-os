package ir.sayda.yara.hub.ui.components

import android.graphics.BitmapFactory
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.combinedClickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.rounded.Send
import androidx.compose.material.icons.rounded.CalendarToday
import androidx.compose.material.icons.rounded.Call
import androidx.compose.material.icons.rounded.Check
import androidx.compose.material.icons.rounded.CheckCircle
import androidx.compose.material.icons.rounded.ChevronLeft
import androidx.compose.material.icons.rounded.Cloud
import androidx.compose.material.icons.rounded.CloudOff
import androidx.compose.material.icons.rounded.CloudQueue
import androidx.compose.material.icons.rounded.Medication
import androidx.compose.material.icons.rounded.Mic
import androidx.compose.material.icons.rounded.Pause
import androidx.compose.material.icons.rounded.PlayArrow
import androidx.compose.material.icons.rounded.AccessTime
import androidx.compose.material.icons.rounded.ArrowBack
import androidx.compose.material.icons.rounded.BatteryFull
import androidx.compose.material.icons.rounded.Chat
import androidx.compose.material.icons.rounded.Favorite
import androidx.compose.material.icons.rounded.Person
import androidx.compose.material.icons.rounded.Security
import androidx.compose.material.icons.rounded.Settings
import androidx.compose.material.icons.rounded.Spa
import androidx.compose.material.icons.rounded.Stop
import androidx.compose.material.icons.rounded.Close
import androidx.compose.material.icons.rounded.Videocam
import androidx.compose.material.icons.rounded.Wifi
import androidx.compose.material.icons.rounded.ZoomIn
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.ui.viewinterop.AndroidView
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Fill
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.material.icons.rounded.Image
import androidx.compose.material.icons.rounded.Refresh
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import ir.sayda.yara.hub.ui.R
import ir.sayda.yara.hub.ui.presentation.ConnectionVisualState
import ir.sayda.yara.hub.ui.presentation.formatEpochForDisplay
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
import ir.sayda.yara.hub.ui.theme.Error
import ir.sayda.yara.hub.ui.theme.SoftBlue
import ir.sayda.yara.hub.ui.theme.SoftOrange
import ir.sayda.yara.hub.ui.theme.SoftRed
import ir.sayda.yara.hub.ui.theme.StatusOnlineGreen
import ir.sayda.yara.hub.ui.theme.Success
import ir.sayda.yara.hub.ui.theme.SurfaceGray
import ir.sayda.yara.hub.ui.theme.TextPrimary
import ir.sayda.yara.hub.ui.theme.TextSecondary
import ir.sayda.yara.hub.ui.theme.TextSlateMuted
import ir.sayda.yara.hub.ui.theme.TextSlatePrimary
import ir.sayda.yara.hub.ui.theme.TextSlateSecondary
import ir.sayda.yara.hub.ui.theme.TextTertiary
import ir.sayda.yara.hub.ui.theme.Warning
import ir.sayda.yara.hub.ui.theme.WarmWhite
import ir.sayda.yara.hub.ui.theme.YaraGreen
import ir.sayda.yara.hub.ui.theme.YaraLightGreen
import ir.sayda.yara.hub.ui.theme.YaraTheme
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

@Composable
fun TodayBackground(modifier: Modifier = Modifier) {
    Canvas(modifier = modifier.fillMaxSize()) {
        val width = size.width
        val height = size.height
        val topCurve = Path().apply {
            moveTo(0f, height * 0.22f)
            quadraticBezierTo(width * 0.5f, height * 0.18f, width, height * 0.24f)
        }
        drawPath(
            path = topCurve,
            color = YaraLightGreen.copy(alpha = 0.6f),
            style = Stroke(width = 2.dp.toPx()),
        )
        val bottomPath = Path().apply {
            moveTo(0f, height * 0.85f)
            cubicTo(width * 0.35f, height * 0.80f, width * 0.65f, height * 0.95f, width, height * 0.88f)
            lineTo(width, height)
            lineTo(0f, height)
            close()
        }
        drawPath(path = bottomPath, color = YaraGreen, style = Fill)
    }
}

@Composable
fun BrandHeader(
    time: String,
    date: String,
    onLogoActivated: () -> Unit = {},
    modifier: Modifier = Modifier,
) {
    var logoTapCount by remember { mutableIntStateOf(0) }
    LaunchedEffect(logoTapCount) {
        if (logoTapCount == 0) return@LaunchedEffect
        kotlinx.coroutines.delay(2_000)
        logoTapCount = 0
    }

    Row(
        modifier = modifier
            .fillMaxWidth()
            .padding(horizontal = 32.dp, vertical = 32.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.Top,
    ) {
        CompositionLocalProvider(LocalLayoutDirection provides LayoutDirection.Ltr) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Image(
                    painter = painterResource(R.drawable.yara_logo),
                    contentDescription = "لوگوی یارا",
                    contentScale = ContentScale.Fit,
                    modifier = Modifier
                        .size(width = 56.dp, height = 60.dp)
                        .clickable {
                            logoTapCount++
                            if (logoTapCount >= 5) {
                                onLogoActivated()
                                logoTapCount = 0
                            }
                        },
                )
                Spacer(modifier = Modifier.width(12.dp))
                Column(horizontalAlignment = Alignment.Start) {
                    Image(
                        painter = painterResource(R.drawable.yara_typo),
                        contentDescription = "یارا",
                        contentScale = ContentScale.Fit,
                        modifier = Modifier
                            .height(28.dp)
                            .width(115.dp),
                    )
                    Text(
                        text = "همدم هوشمند سالمندان",
                        style = MaterialTheme.typography.labelMedium,
                        color = TextSecondary,
                        fontSize = 12.sp,
                        lineHeight = 18.sp,
                    )
                }
            }
        }
        Column(horizontalAlignment = Alignment.Start) {
            Text(
                text = time,
                style = MaterialTheme.typography.displayMedium,
                color = TextPrimary,
                fontWeight = FontWeight.Medium,
            )
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    imageVector = Icons.Rounded.CalendarToday,
                    contentDescription = null,
                    tint = YaraGreen,
                    modifier = Modifier.size(20.dp),
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = date,
                    style = MaterialTheme.typography.labelMedium,
                    color = TextSecondary,
                    fontSize = 16.sp,
                )
            }
        }
    }
}

@Composable
fun GreetingSection(name: String, modifier: Modifier = Modifier) {
    Column(
        modifier = modifier.fillMaxWidth(),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text(
            text = "سلام، وقت بخیر",
            style = MaterialTheme.typography.headlineLarge,
            color = TextPrimary,
        )
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.Center,
        ) {
            Text(
                text = name,
                style = MaterialTheme.typography.headlineMedium,
                color = TextPrimary,
                fontWeight = FontWeight.Medium,
            )
            Spacer(modifier = Modifier.width(8.dp))
            Icon(
                imageVector = Icons.Rounded.Spa,
                contentDescription = null,
                tint = YaraGreen,
                modifier = Modifier.size(28.dp),
            )
        }
        Spacer(modifier = Modifier.height(16.dp))
        Text(
            text = "امیدوارم امروز روز خوبی داشته باشید.",
            style = MaterialTheme.typography.bodyLarge,
            color = TextSecondary,
        )
    }
}

@Composable
private fun YaraBaseCard(
    onClick: () -> Unit,
    icon: ImageVector,
    iconColor: Color,
    iconBackground: Color,
    title: String,
    subtitle: String,
    description: String? = null,
    borderColor: Color = Color.Transparent,
    trailingIcon: ImageVector = Icons.Rounded.ChevronLeft,
    modifier: Modifier = Modifier,
) {
    Surface(
        onClick = onClick,
        shape = RoundedCornerShape(24.dp),
        color = Color.White,
        border = if (borderColor != Color.Transparent) BorderStroke(2.dp, borderColor) else null,
        shadowElevation = 4.dp,
        modifier = modifier
            .fillMaxWidth()
            .heightIn(min = 120.dp),
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 24.dp, vertical = 28.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Box(
                modifier = Modifier
                    .size(80.dp)
                    .clip(CircleShape)
                    .background(iconBackground),
                contentAlignment = Alignment.Center,
            ) {
                Icon(imageVector = icon, contentDescription = null, tint = iconColor, modifier = Modifier.size(48.dp))
            }
            Spacer(modifier = Modifier.width(24.dp))
            Column(modifier = Modifier.weight(1f), horizontalAlignment = Alignment.Start) {
                Text(text = title, style = MaterialTheme.typography.labelMedium, color = TextSecondary)
                Text(
                    text = subtitle,
                    style = MaterialTheme.typography.titleLarge,
                    color = TextPrimary,
                    fontWeight = FontWeight.Bold,
                )
                if (description != null) {
                    Text(text = description, style = MaterialTheme.typography.bodyLarge, color = TextPrimary)
                }
            }
            Spacer(modifier = Modifier.width(16.dp))
            Icon(
                imageVector = trailingIcon,
                contentDescription = null,
                tint = TextSecondary.copy(alpha = 0.3f),
                modifier = Modifier.size(32.dp),
            )
        }
    }
}

@Composable
fun ConnectionIndicator(
    state: ConnectionVisualState,
    title: String,
    subtitle: String,
    modifier: Modifier = Modifier,
) {
    val (icon, iconColor, iconBackground) = when (state) {
        ConnectionVisualState.Connected -> Triple(Icons.Rounded.Wifi, Success, YaraLightGreen)
        ConnectionVisualState.Waiting -> Triple(Icons.Rounded.CloudQueue, Warning, SoftOrange.copy(alpha = 0.15f))
        ConnectionVisualState.Offline -> Triple(Icons.Rounded.CloudOff, Error, Error.copy(alpha = 0.12f))
        ConnectionVisualState.Provisioning -> Triple(Icons.Rounded.Cloud, TextTertiary, SurfaceGray)
    }
    Surface(
        shape = RoundedCornerShape(20.dp),
        color = Color.White,
        shadowElevation = 2.dp,
        modifier = modifier.fillMaxWidth(),
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 20.dp, vertical = 16.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Box(
                modifier = Modifier
                    .size(48.dp)
                    .clip(CircleShape)
                    .background(iconBackground),
                contentAlignment = Alignment.Center,
            ) {
                Icon(imageVector = icon, contentDescription = null, tint = iconColor, modifier = Modifier.size(28.dp))
            }
            Spacer(modifier = Modifier.width(16.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(text = title, style = MaterialTheme.typography.titleMedium, color = TextPrimary, fontWeight = FontWeight.SemiBold)
                Text(text = subtitle, style = MaterialTheme.typography.bodyLarge, color = TextSecondary, lineHeight = 28.sp)
            }
        }
    }
}

@Composable
fun NextReminderHighlightCard(
    title: String,
    subtitle: String,
    description: String?,
    scheduledTime: String?,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    YaraBaseCard(
        onClick = onClick,
        icon = Icons.Rounded.Medication,
        iconColor = YaraGreen,
        iconBackground = YaraLightGreen,
        title = scheduledTime ?: "امروز",
        subtitle = title,
        description = description ?: subtitle,
        modifier = modifier,
    )
}

@Composable
fun HomeEmptyStateCard(
    message: String,
    modifier: Modifier = Modifier,
) {
    Surface(
        shape = RoundedCornerShape(24.dp),
        color = Color.White,
        shadowElevation = 2.dp,
        modifier = modifier
            .fillMaxWidth()
            .heightIn(min = 96.dp),
    ) {
        Box(
            modifier = Modifier.padding(horizontal = 24.dp, vertical = 28.dp),
            contentAlignment = Alignment.Center,
        ) {
            Text(
                text = message,
                style = MaterialTheme.typography.titleLarge,
                color = TextSecondary,
                lineHeight = 32.sp,
            )
        }
    }
}

@Composable
fun HomeLoadingSkeleton(modifier: Modifier = Modifier) {
    Column(
        modifier = modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        repeat(3) {
            Surface(
                shape = RoundedCornerShape(24.dp),
                color = SurfaceGray,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(120.dp),
            ) {}
        }
    }
}

@Composable
fun DeveloperDiagnosticsCard(
    replicaHealth: String,
    runtimeHealth: String,
    lastSyncEpochMillis: Long?,
    isOnline: Boolean,
    activeExecutionCount: Int,
    todayReminderCount: Int,
    nextReminderEpochMillis: Long?,
    pendingEvidenceCount: Int,
    synchronizationAvailable: Boolean,
    registeredAlarmCount: Int,
    modifier: Modifier = Modifier,
) {
    val lastSyncLabel = formatEpochForDisplay(lastSyncEpochMillis)
    val nextReminderLabel = nextReminderEpochMillis?.let { formatEpoch(it) } ?: "—"
    val syncLabel = if (synchronizationAvailable) "AVAILABLE" else "DISABLED"
    Surface(
        shape = RoundedCornerShape(16.dp),
        color = SurfaceGray,
        modifier = modifier.fillMaxWidth(),
    ) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Text(text = "Developer Diagnostics", style = MaterialTheme.typography.labelLarge, color = TextSecondary)
            Text(text = "Runtime: $runtimeHealth", style = MaterialTheme.typography.bodyMedium)
            Text(text = "Replica: $replicaHealth", style = MaterialTheme.typography.bodyMedium)
            Text(text = "Online: $isOnline", style = MaterialTheme.typography.bodyMedium)
            Text(text = "Synchronization: $syncLabel", style = MaterialTheme.typography.bodyMedium)
            Text(text = "Checkpoint / Last sync: $lastSyncLabel", style = MaterialTheme.typography.bodyMedium)
            Text(text = "PendingEvidence: $pendingEvidenceCount", style = MaterialTheme.typography.bodyMedium)
            Text(text = "Alarm count: $registeredAlarmCount", style = MaterialTheme.typography.bodyMedium)
            Text(text = "Active executions: $activeExecutionCount", style = MaterialTheme.typography.bodyMedium)
            Text(text = "Today reminders: $todayReminderCount · Next: $nextReminderLabel", style = MaterialTheme.typography.bodyMedium)
        }
    }
}

@Composable
fun ReminderLoadingIndicator(modifier: Modifier = Modifier) {
    Column(
        modifier = modifier,
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        CircularProgressIndicator(color = YaraGreen, modifier = Modifier.size(56.dp), strokeWidth = 4.dp)
        Text(text = "لطفاً چند لحظه صبر کنید...", color = TextSecondary, style = MaterialTheme.typography.bodyLarge)
    }
}

@Deprecated("Use ConnectionIndicator and DeveloperDiagnosticsCard instead")
@Composable
fun RuntimeStatusCard(
    replicaHealth: String,
    runtimeHealth: String,
    lastSyncEpochMillis: Long?,
    isOnline: Boolean,
    activeExecutionCount: Int,
    todayReminderCount: Int,
    nextReminderEpochMillis: Long? = null,
    pendingEvidenceCount: Int = 0,
    synchronizationAvailable: Boolean = false,
    registeredAlarmCount: Int = 0,
    modifier: Modifier = Modifier,
) {
    val lastSyncLabel = lastSyncEpochMillis?.let { formatEpoch(it) } ?: "هرگز"
    val nextReminderLabel = nextReminderEpochMillis?.let { formatEpoch(it) } ?: "نامشخص"
    val syncLabel = if (synchronizationAvailable) "همگام‌سازی در دسترس" else "همگام‌سازی غیرفعال"
    YaraBaseCard(
        onClick = {},
        icon = Icons.Rounded.Medication,
        iconColor = YaraGreen,
        iconBackground = YaraLightGreen,
        title = if (isOnline) "متصل به سرور" else "حالت آفلاین",
        subtitle = "یادآور بعدی: $nextReminderLabel · امروز: $todayReminderCount",
        description = "Runtime: $runtimeHealth | Replica: $replicaHealth | " +
            "آخرین همگام‌سازی: $lastSyncLabel | " +
            "شواهد در صف: $pendingEvidenceCount | " +
            "آلارم‌ها: $registeredAlarmCount | $syncLabel",
        modifier = modifier,
    )
}

@Composable
fun TodayReminderCard(
    title: String,
    description: String,
    scheduledTime: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    YaraBaseCard(
        onClick = onClick,
        icon = Icons.Rounded.Medication,
        iconColor = YaraGreen,
        iconBackground = YaraLightGreen,
        title = scheduledTime,
        subtitle = title,
        description = description,
        modifier = modifier,
    )
}

@Composable
fun ReminderActionButton(
    label: String,
    enabled: Boolean = true,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Surface(
        onClick = onClick,
        enabled = enabled,
        shape = RoundedCornerShape(24.dp),
        color = if (enabled) YaraGreen else TextSecondary.copy(alpha = 0.2f),
        modifier = modifier
            .fillMaxWidth()
            .heightIn(min = 72.dp),
    ) {
        Box(contentAlignment = Alignment.Center) {
            Text(
                text = label,
                style = MaterialTheme.typography.titleLarge,
                color = if (enabled) Color.White else TextSecondary,
                fontWeight = FontWeight.Bold,
            )
        }
    }
}

private fun formatEpoch(epochMillis: Long): String {
    val formatter = SimpleDateFormat("HH:mm", Locale("fa", "IR"))
    return formatter.format(Date(epochMillis))
}

@Composable
fun VoiceMessageCard(from: String, onClick: () -> Unit) {
    YaraBaseCard(
        onClick = onClick,
        icon = Icons.Rounded.PlayArrow,
        iconColor = SoftBlue,
        iconBackground = SoftBlue.copy(alpha = 0.1f),
        title = "پیام صوتی جدید",
        subtitle = from,
    )
}

@Composable
fun ActiveVoiceMessageCard(
    senderName: String,
    isPlaying: Boolean,
    durationText: String,
    onPlayPauseClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Surface(
        onClick = onPlayPauseClick,
        shape = RoundedCornerShape(24.dp),
        color = Color.White,
        shadowElevation = 2.dp,
        modifier = modifier
            .fillMaxWidth()
            .heightIn(min = 120.dp),
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 24.dp, vertical = 20.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Box(
                modifier = Modifier
                    .size(80.dp)
                    .clip(CircleShape)
                    .background(if (isPlaying) YaraLightGreen else SoftBlue.copy(alpha = 0.15f)),
                contentAlignment = Alignment.Center,
            ) {
                Icon(
                    imageVector = if (isPlaying) Icons.Rounded.Pause else Icons.Rounded.PlayArrow,
                    contentDescription = if (isPlaying) "توقف پخش" else "پخش پیام",
                    tint = if (isPlaying) YaraGreen else SoftBlue,
                    modifier = Modifier.size(48.dp),
                )
            }
            Spacer(modifier = Modifier.width(24.dp))
            Column(modifier = Modifier.weight(1f), horizontalAlignment = Alignment.Start) {
                Text(
                    text = "پیام صوتی از $senderName",
                    style = MaterialTheme.typography.titleLarge,
                    color = TextPrimary,
                    fontWeight = FontWeight.Bold,
                )
                Spacer(modifier = Modifier.height(6.dp))
                Text(
                    text = if (isPlaying) "در حال پخش... ($durationText)" else "برای شنیدن لمس کنید ($durationText)",
                    style = MaterialTheme.typography.bodyLarge,
                    color = TextSecondary,
                )
            }
        }
    }
}

@Composable
fun RecordVoiceMessageCard(
    isRecording: Boolean,
    recordingSeconds: Int,
    onStartRecording: () -> Unit,
    onStopAndSend: () -> Unit,
    onCancelRecording: () -> Unit = {},
    modifier: Modifier = Modifier,
) {
    Surface(
        shape = RoundedCornerShape(24.dp),
        color = if (isRecording) SoftRed.copy(alpha = 0.08f) else Color.White,
        shadowElevation = 3.dp,
        modifier = modifier.fillMaxWidth(),
    ) {
        Column(
            modifier = Modifier.padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            if (!isRecording) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Box(
                        modifier = Modifier
                            .size(64.dp)
                            .clip(CircleShape)
                            .background(YaraLightGreen),
                        contentAlignment = Alignment.Center,
                    ) {
                        Icon(
                            imageVector = Icons.Rounded.Mic,
                            contentDescription = null,
                            tint = YaraGreen,
                            modifier = Modifier.size(36.dp),
                        )
                    }
                    Spacer(modifier = Modifier.width(20.dp))
                    Column(modifier = Modifier.weight(1f), horizontalAlignment = Alignment.Start) {
                        Text(
                            text = "ارسال پیام صوتی به خانواده",
                            style = MaterialTheme.typography.titleLarge,
                            color = TextPrimary,
                            fontWeight = FontWeight.Bold,
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            text = "برای شروع صحبت، دکمه زیر را لمس کنید",
                            style = MaterialTheme.typography.bodyMedium,
                            color = TextSecondary,
                        )
                    }
                }
                Spacer(modifier = Modifier.height(20.dp))
                Surface(
                    onClick = onStartRecording,
                    shape = RoundedCornerShape(18.dp),
                    color = YaraGreen,
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(64.dp),
                ) {
                    Row(
                        modifier = Modifier.fillMaxSize(),
                        horizontalArrangement = Arrangement.Center,
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Icon(
                            imageVector = Icons.Rounded.Mic,
                            contentDescription = null,
                            tint = Color.White,
                            modifier = Modifier.size(28.dp),
                        )
                        Spacer(modifier = Modifier.width(12.dp))
                        Text(
                            text = "شروع ضبط پیام صوتی",
                            style = MaterialTheme.typography.titleLarge,
                            color = Color.White,
                            fontWeight = FontWeight.Bold,
                        )
                    }
                }
            } else {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceBetween,
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Box(
                            modifier = Modifier
                                .size(16.dp)
                                .clip(CircleShape)
                                .background(SoftRed),
                        )
                        Spacer(modifier = Modifier.width(12.dp))
                        Text(
                            text = "در حال ضبط صدای شما...",
                            style = MaterialTheme.typography.titleLarge,
                            color = SoftRed,
                            fontWeight = FontWeight.Bold,
                        )
                    }
                    Text(
                        text = "$recordingSeconds ثانیه",
                        style = MaterialTheme.typography.titleLarge,
                        color = TextPrimary,
                        fontWeight = FontWeight.Bold,
                    )
                }

                Spacer(modifier = Modifier.height(24.dp))

                Surface(
                    onClick = onStopAndSend,
                    shape = RoundedCornerShape(18.dp),
                    color = YaraGreen,
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(64.dp),
                ) {
                    Row(
                        modifier = Modifier.fillMaxSize(),
                        horizontalArrangement = Arrangement.Center,
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Icon(
                            imageVector = Icons.AutoMirrored.Rounded.Send,
                            contentDescription = null,
                            tint = Color.White,
                            modifier = Modifier.size(28.dp),
                        )
                        Spacer(modifier = Modifier.width(12.dp))
                        Text(
                            text = "ارسال پیام صوتی به خانواده",
                            style = MaterialTheme.typography.titleLarge,
                            color = Color.White,
                            fontWeight = FontWeight.Bold,
                        )
                    }
                }

                Spacer(modifier = Modifier.height(12.dp))

                Surface(
                    onClick = onCancelRecording,
                    shape = RoundedCornerShape(18.dp),
                    color = SurfaceGray,
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(48.dp),
                ) {
                    Row(
                        modifier = Modifier.fillMaxSize(),
                        horizontalArrangement = Arrangement.Center,
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Text(
                            text = "انصراف و حذف ضبط",
                            style = MaterialTheme.typography.titleMedium,
                            color = TextSecondary,
                            fontWeight = FontWeight.Medium,
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun FamilyTextMessageCard(
    senderName: String,
    text: String,
    time: String,
    modifier: Modifier = Modifier,
) {
    Surface(
        shape = RoundedCornerShape(topStart = 24.dp, topEnd = 24.dp, bottomEnd = 24.dp, bottomStart = 8.dp),
        color = Color(0xFFF8FAFC),
        border = BorderStroke(1.5.dp, Color(0xFFCBD5E1)),
        shadowElevation = 2.dp,
        modifier = modifier
            .fillMaxWidth()
            .heightIn(min = 90.dp),
    ) {
        Column(
            modifier = Modifier.padding(horizontal = 24.dp, vertical = 18.dp),
            horizontalAlignment = Alignment.Start,
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(
                    text = "پیام از $senderName",
                    style = MaterialTheme.typography.labelLarge,
                    color = SoftBlue,
                    fontWeight = FontWeight.Bold,
                    fontSize = 16.sp,
                )
                Text(
                    text = time,
                    style = MaterialTheme.typography.bodySmall,
                    color = TextTertiary,
                    fontSize = 13.sp,
                )
            }
            Spacer(modifier = Modifier.height(10.dp))
            Text(
                text = text,
                style = MaterialTheme.typography.titleLarge,
                color = TextPrimary,
                lineHeight = 32.sp,
            )
        }
    }
}

@Composable
fun HubContactItemCard(
    name: String,
    unreadCount: Int = 0,
    lastMessageText: String? = null,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Surface(
        onClick = onClick,
        shape = RoundedCornerShape(24.dp),
        color = Color.White,
        border = BorderStroke(1.5.dp, if (unreadCount > 0) Color(0xFFC084FC) else Color(0xFFE2E8F0)),
        shadowElevation = 2.dp,
        modifier = modifier
            .fillMaxWidth()
            .heightIn(min = 96.dp),
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 24.dp, vertical = 18.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween,
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(18.dp),
                modifier = Modifier.weight(1f),
            ) {
                Surface(
                    shape = CircleShape,
                    color = if (unreadCount > 0) Color(0xFFF3E8FF) else Color(0xFFEFF6FF),
                    border = BorderStroke(1.dp, if (unreadCount > 0) Color(0xFFD8B4FE) else Color(0xFFBFDBFE)),
                    modifier = Modifier.size(58.dp),
                ) {
                    Box(contentAlignment = Alignment.Center) {
                        Text(
                            text = name.firstOrNull()?.toString() ?: "خ",
                            style = MaterialTheme.typography.headlineSmall,
                            fontWeight = FontWeight.Bold,
                            color = if (unreadCount > 0) Color(0xFF7E22CE) else Color(0xFF1D4ED8),
                        )
                    }
                }
                Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text(
                        text = name,
                        style = MaterialTheme.typography.titleLarge,
                        fontWeight = FontWeight.Bold,
                        color = TextSlatePrimary,
                        fontSize = 20.sp,
                    )
                    Text(
                        text = lastMessageText ?: "ارتباط و گفتگو با خانواده",
                        style = MaterialTheme.typography.bodyMedium,
                        color = TextSlateSecondary,
                        fontSize = 14.sp,
                        maxLines = 1,
                    )
                }
            }

            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                if (unreadCount > 0) {
                    Surface(
                        shape = RoundedCornerShape(12.dp),
                        color = Color(0xFFF3E8FF),
                        border = BorderStroke(1.dp, Color(0xFFD8B4FE)),
                    ) {
                        Text(
                            text = "$unreadCount پیام جدید",
                            color = Color(0xFF7E22CE),
                            style = MaterialTheme.typography.labelMedium,
                            fontWeight = FontWeight.Bold,
                            modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp),
                        )
                    }
                }
                Surface(
                    shape = CircleShape,
                    color = Color(0xFFF8FAFC),
                    border = BorderStroke(1.dp, Color(0xFFE2E8F0)),
                    modifier = Modifier.size(40.dp),
                ) {
                    Box(contentAlignment = Alignment.Center) {
                        Icon(
                            imageVector = Icons.Rounded.ChevronLeft,
                            contentDescription = "ورود به گفتگو",
                            tint = Color(0xFF64748B),
                            modifier = Modifier.size(22.dp),
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun HubOutgoingMessageCard(
    text: String?,
    time: String,
    statusText: String,
    isVoice: Boolean = false,
    durationText: String? = null,
    isPlaying: Boolean = false,
    isFailed: Boolean = false,
    onPlayPauseClick: (() -> Unit)? = null,
    onRetryClick: (() -> Unit)? = null,
    modifier: Modifier = Modifier,
) {
    Surface(
        shape = RoundedCornerShape(topStart = 24.dp, topEnd = 24.dp, bottomStart = 24.dp, bottomEnd = 8.dp),
        color = if (isFailed) Color(0xFFFEF2F2) else Color(0xFFEFF6FF),
        border = BorderStroke(1.5.dp, if (isFailed) SoftRed.copy(alpha = 0.5f) else Color(0xFFBFDBFE)),
        shadowElevation = 2.dp,
        modifier = modifier
            .fillMaxWidth()
            .heightIn(min = 90.dp),
    ) {
        Column(
            modifier = Modifier.padding(horizontal = 24.dp, vertical = 18.dp),
            horizontalAlignment = Alignment.Start,
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    Text(
                        text = if (isVoice) "🎙️ صدای ضبط شده" else statusText,
                        style = MaterialTheme.typography.labelLarge,
                        color = if (isFailed) SoftRed else Color(0xFF0D9488),
                        fontWeight = FontWeight.Bold,
                    )
                    if (isVoice) {
                        Text(
                            text = "• $statusText",
                            style = MaterialTheme.typography.bodySmall,
                            color = if (isFailed) SoftRed else TextTertiary,
                        )
                    }
                }
                Text(
                    text = time,
                    style = MaterialTheme.typography.bodySmall,
                    color = TextTertiary,
                )
            }
            Spacer(modifier = Modifier.height(8.dp))
            if (isVoice) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceBetween,
                ) {
                    Text(
                        text = durationText ?: "صدای ضبط شده",
                        style = MaterialTheme.typography.titleMedium,
                        color = TextPrimary,
                    )
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(10.dp),
                    ) {
                        if (isFailed && onRetryClick != null) {
                            Surface(
                                onClick = onRetryClick,
                                shape = RoundedCornerShape(14.dp),
                                color = SoftRed.copy(alpha = 0.12f),
                                border = BorderStroke(1.dp, SoftRed.copy(alpha = 0.4f)),
                                modifier = Modifier.height(44.dp),
                            ) {
                                Row(
                                    modifier = Modifier.padding(horizontal = 14.dp),
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.spacedBy(6.dp),
                                ) {
                                    Icon(
                                        imageVector = Icons.Rounded.Refresh,
                                        contentDescription = "تلاش مجدد",
                                        tint = SoftRed,
                                        modifier = Modifier.size(18.dp),
                                    )
                                    Text(
                                        text = "تلاش مجدد",
                                        style = MaterialTheme.typography.bodySmall,
                                        color = SoftRed,
                                        fontWeight = FontWeight.Bold,
                                    )
                                }
                            }
                        }

                        if (onPlayPauseClick != null) {
                            Surface(
                                onClick = onPlayPauseClick,
                                shape = CircleShape,
                                color = Color(0xFF0D9488),
                                modifier = Modifier.size(48.dp),
                            ) {
                                Box(contentAlignment = Alignment.Center) {
                                    Icon(
                                        imageVector = if (isPlaying) Icons.Rounded.Pause else Icons.Rounded.PlayArrow,
                                        contentDescription = if (isPlaying) "توقف" else "پخش",
                                        tint = Color.White,
                                        modifier = Modifier.size(28.dp),
                                    )
                                }
                            }
                        }
                    }
                }
            } else {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text(
                        text = text.orEmpty(),
                        style = MaterialTheme.typography.titleLarge,
                        color = TextPrimary,
                        lineHeight = 32.sp,
                        modifier = Modifier.weight(1f, fill = false),
                    )
                    if (isFailed && onRetryClick != null) {
                        Spacer(modifier = Modifier.width(12.dp))
                        Surface(
                            onClick = onRetryClick,
                            shape = RoundedCornerShape(14.dp),
                            color = SoftRed.copy(alpha = 0.12f),
                            border = BorderStroke(1.dp, SoftRed.copy(alpha = 0.4f)),
                            modifier = Modifier.height(44.dp),
                        ) {
                            Row(
                                modifier = Modifier.padding(horizontal = 14.dp),
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(6.dp),
                            ) {
                                Icon(
                                    imageVector = Icons.Rounded.Refresh,
                                    contentDescription = "تلاش مجدد",
                                    tint = SoftRed,
                                    modifier = Modifier.size(18.dp),
                                )
                                Text(
                                    text = "تلاش مجدد",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = SoftRed,
                                    fontWeight = FontWeight.Bold,
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun FamilyMediaMessageCard(
    senderName: String,
    title: String,
    text: String?,
    localFileUri: String?,
    time: String,
    isVideo: Boolean = false,
    modifier: Modifier = Modifier,
    onClick: (() -> Unit)? = null,
) {
    val bitmap = remember(localFileUri, isVideo) {
        localFileUri?.let { path ->
            val f = java.io.File(path)
            if (f.exists()) {
                if (isVideo) {
                    try {
                        val retriever = android.media.MediaMetadataRetriever()
                        retriever.setDataSource(f.absolutePath)
                        val frame = retriever.getFrameAtTime(1000000) ?: retriever.frameAtTime
                        retriever.release()
                        frame?.asImageBitmap()
                    } catch (_: Exception) {
                        null
                    }
                } else {
                    BitmapFactory.decodeFile(f.absolutePath)?.asImageBitmap()
                }
            } else null
        }
    }
    Surface(
        onClick = { onClick?.invoke() },
        enabled = onClick != null,
        shape = RoundedCornerShape(topStart = 24.dp, topEnd = 24.dp, bottomEnd = 24.dp, bottomStart = 8.dp),
        color = Color(0xFFF8FAFC),
        border = BorderStroke(1.5.dp, Color(0xFFCBD5E1)),
        shadowElevation = 2.dp,
        modifier = modifier
            .fillMaxWidth()
            .heightIn(min = 100.dp),
    ) {
        Column(
            modifier = Modifier.padding(horizontal = 24.dp, vertical = 20.dp),
            horizontalAlignment = Alignment.Start,
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(
                    text = title.ifBlank { if (isVideo) "پیام ویدیویی از $senderName" else "پیام تصویری از $senderName" },
                    style = MaterialTheme.typography.labelLarge,
                    color = SoftBlue,
                    fontWeight = FontWeight.Bold,
                    fontSize = 16.sp,
                )
                Text(
                    text = time,
                    style = MaterialTheme.typography.bodySmall,
                    color = TextTertiary,
                    fontSize = 13.sp,
                )
            }
            if (bitmap != null) {
                Spacer(modifier = Modifier.height(12.dp))
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .heightIn(max = 280.dp)
                        .clip(RoundedCornerShape(16.dp)),
                ) {
                    Image(
                        bitmap = bitmap,
                        contentDescription = text ?: title,
                        modifier = Modifier.fillMaxSize(),
                        contentScale = ContentScale.Crop,
                    )
                    if (isVideo) {
                        Surface(
                            shape = CircleShape,
                            color = Color(0xFF00685F).copy(alpha = 0.90f),
                            border = BorderStroke(2.dp, Color.White),
                            modifier = Modifier
                                .size(56.dp)
                                .align(Alignment.Center),
                        ) {
                            Box(contentAlignment = Alignment.Center) {
                                Icon(
                                    imageVector = Icons.Rounded.PlayArrow,
                                    contentDescription = "پخش ویدیو",
                                    tint = Color.White,
                                    modifier = Modifier.size(34.dp),
                                )
                            }
                        }
                    }
                    Surface(
                        shape = RoundedCornerShape(12.dp),
                        color = Color.Black.copy(alpha = 0.65f),
                        modifier = Modifier
                            .align(Alignment.BottomEnd)
                            .padding(10.dp),
                    ) {
                        Row(
                            modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(6.dp),
                        ) {
                            Icon(
                                imageVector = if (isVideo) Icons.Rounded.PlayArrow else Icons.Rounded.ZoomIn,
                                contentDescription = null,
                                tint = Color.White,
                                modifier = Modifier.size(18.dp),
                            )
                            Text(
                                text = if (isVideo) "پخش تمام‌صفحه" else "نمایش بزرگ‌تر",
                                style = MaterialTheme.typography.labelMedium,
                                color = Color.White,
                                fontWeight = FontWeight.Bold,
                                fontSize = 12.sp,
                            )
                        }
                    }
                }
            } else if (isVideo && localFileUri != null && java.io.File(localFileUri).exists()) {
                Spacer(modifier = Modifier.height(12.dp))
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(170.dp)
                        .clip(RoundedCornerShape(16.dp))
                        .background(Color(0xFF0F172A)),
                    contentAlignment = Alignment.Center,
                ) {
                    Surface(
                        shape = CircleShape,
                        color = Color(0xFF00685F).copy(alpha = 0.90f),
                        border = BorderStroke(2.dp, Color.White),
                        modifier = Modifier.size(56.dp),
                    ) {
                        Box(contentAlignment = Alignment.Center) {
                            Icon(
                                imageVector = Icons.Rounded.PlayArrow,
                                contentDescription = "پخش ویدیو",
                                tint = Color.White,
                                modifier = Modifier.size(34.dp),
                            )
                        }
                    }
                    Surface(
                        shape = RoundedCornerShape(12.dp),
                        color = Color.Black.copy(alpha = 0.65f),
                        modifier = Modifier
                            .align(Alignment.BottomEnd)
                            .padding(10.dp),
                    ) {
                        Row(
                            modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(6.dp),
                        ) {
                            Icon(
                                imageVector = Icons.Rounded.PlayArrow,
                                contentDescription = null,
                                tint = Color.White,
                                modifier = Modifier.size(16.dp),
                            )
                            Text(
                                text = "پخش ویدیو",
                                style = MaterialTheme.typography.labelMedium,
                                color = Color.White,
                                fontWeight = FontWeight.Bold,
                                fontSize = 12.sp,
                            )
                        }
                    }
                }
            } else {
                Spacer(modifier = Modifier.height(10.dp))
                Surface(
                    shape = RoundedCornerShape(16.dp),
                    color = Color(0xFFF1F5F9),
                    border = BorderStroke(1.dp, Color(0xFFE2E8F0)),
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(110.dp),
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxSize()
                            .padding(16.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.Center,
                    ) {
                        Icon(
                            imageVector = if (isVideo) Icons.Rounded.Videocam else Icons.Rounded.Image,
                            contentDescription = null,
                            tint = Color(0xFF94A3B8),
                            modifier = Modifier.size(32.dp),
                        )
                        Spacer(modifier = Modifier.width(12.dp))
                        Text(
                            text = if (localFileUri != null) {
                                if (isVideo) "در حال آماده‌سازی ویدیو..." else "در حال بارگذاری تصویر..."
                            } else {
                                if (isVideo) "ویدیو در دستگاه موجود نیست" else "تصویر در دستگاه موجود نیست"
                            },
                            style = MaterialTheme.typography.bodyMedium,
                            color = TextSecondary,
                            fontSize = 14.sp,
                        )
                    }
                }
            }
            if (!text.isNullOrBlank()) {
                Spacer(modifier = Modifier.height(10.dp))
                Text(
                    text = text,
                    style = MaterialTheme.typography.titleLarge,
                    color = TextPrimary,
                    lineHeight = 32.sp,
                    fontSize = 19.sp,
                )
            }
        }
    }
}

data class HubMediaViewerTarget(
    val title: String,
    val localFileUri: String?,
    val caption: String?,
    val isVideo: Boolean = false,
)

@Composable
fun FullScreenMediaViewerDialog(
    target: HubMediaViewerTarget,
    onDismiss: () -> Unit,
) {
    FullScreenMediaViewerDialog(
        title = target.title,
        localFileUri = target.localFileUri,
        caption = target.caption,
        isVideo = target.isVideo,
        onDismiss = onDismiss,
    )
}

@Composable
fun FullScreenMediaViewerDialog(
    title: String,
    localFileUri: String?,
    caption: String?,
    isVideo: Boolean = false,
    onDismiss: () -> Unit,
) {
    Dialog(
        onDismissRequest = onDismiss,
        properties = DialogProperties(usePlatformDefaultWidth = false),
    ) {
        val bitmap = remember(localFileUri, isVideo) {
            if (!isVideo && !localFileUri.isNullOrBlank()) {
                val f = java.io.File(localFileUri)
                if (f.exists()) {
                    BitmapFactory.decodeFile(f.absolutePath)?.asImageBitmap()
                } else null
            } else null
        }

        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(Color(0xFF0B111A)),
        ) {
            // Main media presentation
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(top = 80.dp, bottom = if (!caption.isNullOrBlank()) 90.dp else 24.dp, start = 16.dp, end = 16.dp),
                contentAlignment = Alignment.Center,
            ) {
                if (isVideo) {
                    if (!localFileUri.isNullOrBlank() && java.io.File(localFileUri).exists()) {
                        AndroidView(
                            factory = { ctx ->
                                android.widget.VideoView(ctx).apply {
                                    val controller = android.widget.MediaController(ctx)
                                    controller.setAnchorView(this)
                                    setMediaController(controller)
                                    setVideoPath(localFileUri)
                                    start()
                                }
                            },
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(420.dp)
                                .clip(RoundedCornerShape(16.dp)),
                        )
                    } else {
                        Column(
                            horizontalAlignment = Alignment.CenterHorizontally,
                            verticalArrangement = Arrangement.spacedBy(12.dp),
                        ) {
                            Icon(
                                imageVector = Icons.Rounded.PlayArrow,
                                contentDescription = null,
                                tint = Color(0xFF64748B),
                                modifier = Modifier.size(64.dp),
                            )
                            Text(
                                text = "فایل ویدیو بر روی دستگاه در دسترس نیست",
                                style = MaterialTheme.typography.titleMedium,
                                color = Color(0xFF94A3B8),
                                fontSize = 18.sp,
                            )
                        }
                    }
                } else {
                    if (bitmap != null) {
                        Image(
                            bitmap = bitmap,
                            contentDescription = caption ?: title,
                            modifier = Modifier.fillMaxSize(),
                            contentScale = ContentScale.Fit,
                        )
                    } else {
                        Column(
                            horizontalAlignment = Alignment.CenterHorizontally,
                            verticalArrangement = Arrangement.spacedBy(12.dp),
                        ) {
                            Icon(
                                imageVector = Icons.Rounded.Image,
                                contentDescription = null,
                                tint = Color(0xFF64748B),
                                modifier = Modifier.size(64.dp),
                            )
                            Text(
                                text = "تصویر بر روی دستگاه در دسترس نیست",
                                style = MaterialTheme.typography.titleMedium,
                                color = Color(0xFF94A3B8),
                                fontSize = 18.sp,
                            )
                        }
                    }
                }
            }

            // Top Bar with large comfortable Close Button (56dp)
            Surface(
                color = Color.Black.copy(alpha = 0.65f),
                modifier = Modifier
                    .fillMaxWidth()
                    .align(Alignment.TopCenter),
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 24.dp, vertical = 16.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text(
                        text = title,
                        style = MaterialTheme.typography.titleLarge,
                        color = Color.White,
                        fontWeight = FontWeight.Bold,
                        fontSize = 20.sp,
                    )
                    Surface(
                        onClick = onDismiss,
                        shape = RoundedCornerShape(20.dp),
                        color = Color.White.copy(alpha = 0.25f),
                        modifier = Modifier.size(56.dp),
                    ) {
                        Box(contentAlignment = Alignment.Center) {
                            Icon(
                                imageVector = Icons.Rounded.Close,
                                contentDescription = "بستن",
                                tint = Color.White,
                                modifier = Modifier.size(28.dp),
                            )
                        }
                    }
                }
            }

            // Bottom Caption
            if (!caption.isNullOrBlank()) {
                Surface(
                    color = Color.Black.copy(alpha = 0.75f),
                    shape = RoundedCornerShape(topStart = 24.dp, topEnd = 24.dp),
                    modifier = Modifier
                        .fillMaxWidth()
                        .align(Alignment.BottomCenter),
                ) {
                    Text(
                        text = caption,
                        style = MaterialTheme.typography.bodyLarge,
                        color = Color.White,
                        fontSize = 18.sp,
                        lineHeight = 28.sp,
                        textAlign = TextAlign.Center,
                        modifier = Modifier.padding(horizontal = 32.dp, vertical = 18.dp),
                    )
                }
            }
        }
    }
}

/** Voice messages are not deliverable yet (ADR-014); say so instead of hiding the feature. */
@Composable
fun VoiceMessageUnavailableCard(message: String, modifier: Modifier = Modifier) {
    Surface(
        shape = RoundedCornerShape(24.dp),
        color = Color.White,
        shadowElevation = 2.dp,
        modifier = modifier
            .fillMaxWidth()
            .heightIn(min = 120.dp),
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 24.dp, vertical = 28.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Box(
                modifier = Modifier
                    .size(80.dp)
                    .clip(CircleShape)
                    .background(SurfaceGray),
                contentAlignment = Alignment.Center,
            ) {
                Icon(
                    imageVector = Icons.Rounded.PlayArrow,
                    contentDescription = null,
                    tint = TextSecondary,
                    modifier = Modifier.size(48.dp),
                )
            }
            Spacer(modifier = Modifier.width(24.dp))
            Column(modifier = Modifier.weight(1f), horizontalAlignment = Alignment.Start) {
                Text(text = "پیام صوتی", style = MaterialTheme.typography.labelMedium, color = TextSecondary)
                Text(
                    text = message,
                    style = MaterialTheme.typography.titleLarge,
                    color = TextSecondary,
                    lineHeight = 32.sp,
                )
            }
        }
    }
}

@Composable
fun ContactCard(
    name: String,
    onVideoCallClick: () -> Unit,
    onVoiceCallClick: () -> Unit,
    onVoiceMessageClick: (() -> Unit)? = null,
    isRecordingVoice: Boolean = false,
    modifier: Modifier = Modifier,
) {
    Surface(
        shape = RoundedCornerShape(24.dp),
        color = Color.White,
        shadowElevation = 4.dp,
        modifier = modifier
            .fillMaxWidth()
            .heightIn(min = 120.dp),
    ) {
        Column(
            modifier = Modifier.padding(horizontal = 24.dp, vertical = 20.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Box(
                    modifier = Modifier
                        .size(60.dp)
                        .clip(CircleShape)
                        .background(if (isRecordingVoice) SoftRed.copy(alpha = 0.15f) else YaraLightGreen),
                    contentAlignment = Alignment.Center,
                ) {
                    Icon(
                        imageVector = if (isRecordingVoice) Icons.Rounded.Mic else Icons.Rounded.Call,
                        contentDescription = null,
                        tint = if (isRecordingVoice) SoftRed else YaraGreen,
                        modifier = Modifier.size(32.dp),
                    )
                }
                Spacer(modifier = Modifier.width(16.dp))
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = if (isRecordingVoice) "در حال ضبط پیام برای" else "ارتباط با خانواده",
                        style = MaterialTheme.typography.labelMedium,
                        color = if (isRecordingVoice) SoftRed else TextSecondary,
                        fontWeight = if (isRecordingVoice) FontWeight.Bold else FontWeight.Normal,
                    )
                    Text(
                        text = name,
                        style = MaterialTheme.typography.titleLarge,
                        color = TextPrimary,
                        fontWeight = FontWeight.Bold,
                    )
                }
            }
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                Surface(
                    onClick = onVideoCallClick,
                    shape = RoundedCornerShape(16.dp),
                    color = YaraGreen,
                    modifier = Modifier
                        .weight(1f)
                        .height(56.dp),
                ) {
                    Row(
                        modifier = Modifier.fillMaxSize(),
                        horizontalArrangement = Arrangement.Center,
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Icon(
                            imageVector = Icons.Rounded.Videocam,
                            contentDescription = null,
                            tint = Color.White,
                            modifier = Modifier.size(22.dp),
                        )
                        Spacer(modifier = Modifier.width(6.dp))
                        Text(
                            text = if (onVoiceMessageClick != null) "تصویری" else "تماس تصویری",
                            style = MaterialTheme.typography.titleMedium,
                            color = Color.White,
                            fontWeight = FontWeight.Bold,
                        )
                    }
                }
                Surface(
                    onClick = onVoiceCallClick,
                    shape = RoundedCornerShape(16.dp),
                    color = SurfaceGray,
                    modifier = Modifier
                        .weight(1f)
                        .height(56.dp),
                ) {
                    Row(
                        modifier = Modifier.fillMaxSize(),
                        horizontalArrangement = Arrangement.Center,
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Icon(
                            imageVector = Icons.Rounded.Call,
                            contentDescription = null,
                            tint = TextPrimary,
                            modifier = Modifier.size(20.dp),
                        )
                        Spacer(modifier = Modifier.width(6.dp))
                        Text(
                            text = if (onVoiceMessageClick != null) "صوتی" else "تماس صوتی",
                            style = MaterialTheme.typography.titleMedium,
                            color = TextPrimary,
                            fontWeight = FontWeight.Medium,
                        )
                    }
                }
                if (onVoiceMessageClick != null) {
                    Surface(
                        onClick = onVoiceMessageClick,
                        shape = RoundedCornerShape(16.dp),
                        color = if (isRecordingVoice) YaraGreen else YaraLightGreen,
                        modifier = Modifier
                            .weight(1f)
                            .height(56.dp),
                    ) {
                        Row(
                            modifier = Modifier.fillMaxSize(),
                            horizontalArrangement = Arrangement.Center,
                            verticalAlignment = Alignment.CenterVertically,
                        ) {
                            Icon(
                                imageVector = if (isRecordingVoice) Icons.AutoMirrored.Rounded.Send else Icons.Rounded.Mic,
                                contentDescription = null,
                                tint = if (isRecordingVoice) Color.White else YaraGreen,
                                modifier = Modifier.size(20.dp),
                            )
                            Spacer(modifier = Modifier.width(6.dp))
                            Text(
                                text = if (isRecordingVoice) "ارسال پیام" else "پیام صوتی",
                                style = MaterialTheme.typography.titleMedium,
                                color = if (isRecordingVoice) Color.White else YaraGreen,
                                fontWeight = FontWeight.Bold,
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun ContactCard(name: String, onClick: () -> Unit) {
    ContactCard(
        name = name,
        onVideoCallClick = onClick,
        onVoiceCallClick = onClick,
    )
}

@Composable
fun CallActionButton(
    label: String,
    onClick: () -> Unit,
    containerColor: Color = YaraTheme.colors.primary,
    contentColor: Color = YaraTheme.colors.onPrimary,
    enabled: Boolean = true,
    icon: ImageVector? = null,
    modifier: Modifier = Modifier,
) {
    val tokens = YaraTheme.colors
    Surface(
        onClick = onClick,
        enabled = enabled,
        shape = RoundedCornerShape(28.dp),
        color = if (enabled) containerColor else tokens.muted.copy(alpha = 0.2f),
        modifier = modifier
            .fillMaxWidth()
            .heightIn(min = 88.dp),
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 28.dp, vertical = 20.dp),
            horizontalArrangement = Arrangement.Center,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            if (icon != null) {
                Icon(
                    imageVector = icon,
                    contentDescription = null,
                    tint = if (enabled) contentColor else tokens.muted,
                    modifier = Modifier.size(36.dp),
                )
                Spacer(modifier = Modifier.width(16.dp))
            }
            Text(
                text = label,
                style = MaterialTheme.typography.titleLarge,
                color = if (enabled) contentColor else tokens.muted,
                fontWeight = FontWeight.Bold,
            )
        }
    }
}

@Composable
fun CallIconButton(
    label: String,
    icon: ImageVector,
    onClick: () -> Unit,
    containerColor: Color = YaraTheme.colors.surface,
    contentColor: Color = YaraTheme.colors.onSurface,
    enabled: Boolean = true,
    modifier: Modifier = Modifier,
) {
    val tokens = YaraTheme.colors
    val resolvedContainer = if (enabled) containerColor else tokens.mutedContainer
    val resolvedContent = if (enabled) contentColor else tokens.muted
    Column(
        modifier = modifier,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Surface(
            onClick = onClick,
            enabled = enabled,
            shape = CircleShape,
            color = resolvedContainer,
            modifier = Modifier.size(96.dp),
        ) {
            Box(contentAlignment = Alignment.Center, modifier = Modifier.fillMaxSize()) {
                Icon(
                    imageVector = icon,
                    contentDescription = label,
                    tint = resolvedContent,
                    modifier = Modifier.size(44.dp),
                )
            }
        }
        Spacer(modifier = Modifier.height(12.dp))
        Text(
            text = label,
            style = MaterialTheme.typography.labelMedium,
            color = if (enabled) tokens.onBackground else tokens.muted,
            fontWeight = FontWeight.Medium,
        )
    }
}

@Composable
fun CallAvatar(
    name: String,
    modifier: Modifier = Modifier,
    size: Dp = 168.dp,
) {
    val initial = name.trim().firstOrNull()?.toString().orEmpty()
    Surface(
        shape = CircleShape,
        color = CardCallBgEnd,
        border = BorderStroke(3.5.dp, CardCallBorder),
        shadowElevation = 4.dp,
        modifier = modifier.size(size),
    ) {
        Box(
            modifier = Modifier.fillMaxSize(),
            contentAlignment = Alignment.Center,
        ) {
            Text(
                text = initial,
                style = MaterialTheme.typography.displayMedium,
                color = CardCallAccent,
                fontWeight = FontWeight.Bold,
            )
        }
    }
}

@OptIn(ExperimentalFoundationApi::class)
@Composable
fun SettingsButton(
    onLongClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Box(
        modifier = modifier
            .size(56.dp)
            .clip(RoundedCornerShape(24.dp))
            .combinedClickable(onClick = {}, onLongClick = onLongClick),
        contentAlignment = Alignment.Center,
    ) {
        Icon(
            imageVector = Icons.Rounded.Settings,
            contentDescription = "تنظیمات",
            tint = Color.White.copy(alpha = 0.8f),
            modifier = Modifier.size(32.dp),
        )
    }
}

@Composable
fun HubTopBar(
    time: String,
    dateDayMonth: String,
    dateYear: String,
    elderName: String,
    isOnline: Boolean,
    connectionState: ConnectionVisualState,
    onLogoTap: () -> Unit = {},
    greetingText: String = "سلام، $elderName",
    modifier: Modifier = Modifier,
) {
    var tapCount by remember { mutableIntStateOf(0) }
    LaunchedEffect(tapCount) {
        if (tapCount == 0) return@LaunchedEffect
        kotlinx.coroutines.delay(2_000)
        tapCount = 0
    }

    Row(
        modifier = modifier
            .fillMaxWidth()
            .padding(horizontal = 32.dp, vertical = 20.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        // Left side (in RTL Start): Greeting & Profile + Status Icons
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            // Wifi & Connection Status
            val (wifiTint, statusDotColor) = when (connectionState) {
                ConnectionVisualState.Connected -> Pair(Color(0xFF64748B), StatusOnlineGreen)
                ConnectionVisualState.Waiting -> Pair(SoftOrange, SoftOrange)
                ConnectionVisualState.Offline -> Pair(Error, Error)
                ConnectionVisualState.Provisioning -> Pair(TextTertiary, TextTertiary)
            }
            Icon(
                imageVector = if (isOnline) Icons.Rounded.Wifi else Icons.Rounded.CloudOff,
                contentDescription = if (isOnline) "متصل به اینترنت" else "آفلاین",
                tint = wifiTint,
                modifier = Modifier.size(24.dp),
            )
            Icon(
                imageVector = Icons.Rounded.BatteryFull,
                contentDescription = "باتری",
                tint = Color(0xFF64748B),
                modifier = Modifier.size(24.dp),
            )

            Spacer(modifier = Modifier.width(8.dp))

            // Greeting text
            Text(
                text = greetingText,
                style = MaterialTheme.typography.titleLarge,
                color = TextSlatePrimary,
                fontWeight = FontWeight.Bold,
                fontSize = 22.sp,
            )

            // Online green indicator dot
            Box(
                modifier = Modifier
                    .size(10.dp)
                    .clip(CircleShape)
                    .background(statusDotColor),
            )

            // Circular Elder Avatar
            Surface(
                shape = CircleShape,
                color = CardMedicationBadgeBg,
                border = BorderStroke(2.dp, Color.White),
                shadowElevation = 2.dp,
                modifier = Modifier
                    .size(48.dp)
                    .clickable {
                        tapCount++
                        if (tapCount >= 5) {
                            onLogoTap()
                            tapCount = 0
                        }
                    },
            ) {
                Box(contentAlignment = Alignment.Center) {
                    Icon(
                        imageVector = Icons.Rounded.Person,
                        contentDescription = "پروفایل سالمند",
                        tint = CardMedicationAccent,
                        modifier = Modifier.size(30.dp),
                    )
                }
            }
        }

        // Right side (in RTL End): Clock + Divider + Persian Date
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            Text(
                text = time,
                style = MaterialTheme.typography.displayMedium,
                color = TextSlatePrimary,
                fontWeight = FontWeight.Bold,
                fontSize = 44.sp,
            )
            Box(
                modifier = Modifier
                    .height(38.dp)
                    .width(1.5.dp)
                    .background(Color(0xFFCBD5E1)),
            )
            Column(
                verticalArrangement = Arrangement.Center,
                horizontalAlignment = Alignment.Start,
            ) {
                Text(
                    text = dateDayMonth,
                    style = MaterialTheme.typography.titleMedium,
                    color = TextSlatePrimary,
                    fontWeight = FontWeight.SemiBold,
                    fontSize = 15.sp,
                )
                Text(
                    text = dateYear,
                    style = MaterialTheme.typography.bodyMedium,
                    color = TextSlateSecondary,
                    fontSize = 14.sp,
                )
            }
        }
    }
}

@Composable
fun HubActionCard(
    title: String,
    subtitle: String = "",
    icon: ImageVector,
    iconBgColor: Color,
    bgStartColor: Color,
    bgEndColor: Color,
    borderColor: Color,
    buttonText: String,
    buttonColor: Color,
    onButtonClick: () -> Unit,
    modifier: Modifier = Modifier,
    buttonIcon: ImageVector? = null,
    onCardClick: () -> Unit = onButtonClick,
    customBodyContent: (@Composable () -> Unit)? = null,
    badgeContent: @Composable () -> Unit,
) {
    Surface(
        onClick = onCardClick,
        shape = RoundedCornerShape(32.dp),
        color = Color.Transparent,
        border = BorderStroke(1.5.dp, borderColor),
        shadowElevation = 2.dp,
        modifier = modifier
            .fillMaxWidth()
            .heightIn(min = 380.dp),
    ) {
        Box(
            modifier = Modifier
                .background(Brush.verticalGradient(listOf(bgStartColor, bgEndColor)))
                .padding(horizontal = 22.dp, vertical = 26.dp),
        ) {
            Column(
                modifier = Modifier.fillMaxWidth(),
                horizontalAlignment = Alignment.CenterHorizontally,
            ) {
                // Top Circular Icon (with soft glow / inner circle)
                Surface(
                    shape = CircleShape,
                    color = iconBgColor,
                    shadowElevation = 4.dp,
                    modifier = Modifier.size(76.dp),
                ) {
                    Box(
                        contentAlignment = Alignment.Center,
                        modifier = Modifier.fillMaxSize(),
                    ) {
                        Icon(
                            imageVector = icon,
                            contentDescription = null,
                            tint = Color.White,
                            modifier = Modifier.size(42.dp),
                        )
                    }
                }

                Spacer(modifier = Modifier.height(18.dp))

                // Title
                Text(
                    text = title,
                    style = MaterialTheme.typography.headlineLarge,
                    color = TextSlatePrimary,
                    fontWeight = FontWeight.Bold,
                    fontSize = 32.sp,
                )

                Spacer(modifier = Modifier.height(8.dp))

                // Dynamic Body Content or Fallback Subtitle
                if (customBodyContent != null) {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .heightIn(min = 58.dp),
                        contentAlignment = Alignment.Center,
                    ) {
                        customBodyContent()
                    }
                } else {
                    Text(
                        text = subtitle,
                        style = MaterialTheme.typography.bodyMedium,
                        color = TextSlateSecondary,
                        textAlign = TextAlign.Center,
                        minLines = 2,
                        maxLines = 2,
                        lineHeight = 22.sp,
                        fontSize = 15.sp,
                    )
                }

                Spacer(modifier = Modifier.height(18.dp))

                // Status Badge Pill
                Box(
                    modifier = Modifier.height(44.dp),
                    contentAlignment = Alignment.Center,
                ) {
                    badgeContent()
                }

                Spacer(modifier = Modifier.height(22.dp))

                // Bottom Action Pill Button
                Surface(
                    onClick = onButtonClick,
                    shape = RoundedCornerShape(28.dp),
                    color = buttonColor,
                    shadowElevation = 3.dp,
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(58.dp),
                ) {
                    Row(
                        modifier = Modifier.fillMaxSize(),
                        horizontalArrangement = Arrangement.Center,
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        if (buttonIcon != null) {
                            Icon(
                                imageVector = buttonIcon,
                                contentDescription = null,
                                tint = Color.White,
                                modifier = Modifier.size(24.dp),
                            )
                            Spacer(modifier = Modifier.width(10.dp))
                        }
                        Text(
                            text = buttonText,
                            style = MaterialTheme.typography.titleLarge,
                            color = Color.White,
                            fontWeight = FontWeight.Bold,
                            fontSize = 18.sp,
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun HubFooterBadges(modifier: Modifier = Modifier) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .padding(horizontal = 32.dp, vertical = 8.dp),
        horizontalArrangement = Arrangement.Center,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        FooterBadgeItem(
            icon = Icons.Rounded.Security,
            line1 = "ساده و قابل فهم",
            line2 = "مخصوص سالمندان",
        )
        Box(
            modifier = Modifier
                .padding(horizontal = 24.dp)
                .height(28.dp)
                .width(1.dp)
                .background(Color(0xFFCBD5E1)),
        )
        FooterBadgeItem(
            icon = Icons.Rounded.Favorite,
            line1 = "امن و مطمئن",
            line2 = "با مراقبت خانواده",
        )
        Box(
            modifier = Modifier
                .padding(horizontal = 24.dp)
                .height(28.dp)
                .width(1.dp)
                .background(Color(0xFFCBD5E1)),
        )
        FooterBadgeItem(
            icon = Icons.Rounded.Spa,
            line1 = "طراحی شده برای آرامش شما",
            line2 = "یک زندگی راحت‌تر",
        )
    }
}

@Composable
private fun FooterBadgeItem(
    icon: ImageVector,
    line1: String,
    line2: String,
    modifier: Modifier = Modifier,
) {
    Row(
        modifier = modifier,
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        Surface(
            shape = CircleShape,
            color = Color.White,
            border = BorderStroke(1.dp, Color(0xFFE2E8F0)),
            modifier = Modifier.size(36.dp),
        ) {
            Box(contentAlignment = Alignment.Center) {
                Icon(
                    imageVector = icon,
                    contentDescription = null,
                    tint = CardMedicationAccent,
                    modifier = Modifier.size(20.dp),
                )
            }
        }
        Column {
            Text(
                text = line1,
                style = MaterialTheme.typography.labelMedium,
                color = TextSlatePrimary,
                fontWeight = FontWeight.SemiBold,
                fontSize = 13.sp,
            )
            Text(
                text = line2,
                style = MaterialTheme.typography.bodySmall,
                color = TextSlateSecondary,
                fontSize = 11.sp,
            )
        }
    }
}

@Composable
fun ContactAvatar(
    displayName: String,
    photoReference: String? = null,
    size: Dp = 56.dp,
    unread: Boolean = false,
    isPriority: Boolean = false,
    modifier: Modifier = Modifier,
) {
    val context = LocalContext.current
    val bitmap = remember(photoReference) {
        if (!photoReference.isNullOrBlank()) {
            val directFile = java.io.File(photoReference)
            if (directFile.exists()) {
                BitmapFactory.decodeFile(directFile.absolutePath)?.asImageBitmap()
            } else {
                val dir = java.io.File(context.filesDir, "yara_media/received")
                val file = dir.listFiles()?.firstOrNull { it.name.startsWith(photoReference) }
                if (file != null && file.exists()) {
                    BitmapFactory.decodeFile(file.absolutePath)?.asImageBitmap()
                } else null
            }
        } else null
    }

    val initial = displayName.trim().firstOrNull()?.toString() ?: "خ"
    val bgColor = when {
        unread -> Color(0xFFF3E8FF)
        isPriority -> Color(0xFFECFDF5)
        else -> Color(0xFFEFF6FF)
    }
    val borderColor = when {
        unread -> Color(0xFFD8B4FE)
        isPriority -> Color(0xFFA7F3D0)
        else -> Color(0xFFBFDBFE)
    }
    val textColor = when {
        unread -> Color(0xFF7E22CE)
        isPriority -> Color(0xFF047857)
        else -> Color(0xFF1D4ED8)
    }

    Surface(
        shape = CircleShape,
        color = bgColor,
        border = BorderStroke(1.5.dp, borderColor),
        modifier = modifier.size(size),
    ) {
        Box(contentAlignment = Alignment.Center) {
            if (bitmap != null) {
                Image(
                    bitmap = bitmap,
                    contentDescription = displayName,
                    modifier = Modifier.fillMaxSize(),
                    contentScale = ContentScale.Crop,
                )
            } else {
                Text(
                    text = initial,
                    style = MaterialTheme.typography.titleLarge,
                    color = textColor,
                    fontWeight = FontWeight.Bold,
                    fontSize = (size.value * 0.44f).sp,
                )
            }
        }
    }
}

@Composable
fun HubContactItemCard(
    displayName: String,
    relationship: String?,
    unreadCount: Int,
    onClick: () -> Unit,
    photoReference: String? = null,
    modifier: Modifier = Modifier,
) {
    Surface(
        onClick = onClick,
        shape = RoundedCornerShape(24.dp),
        color = Color.White,
        border = BorderStroke(1.5.dp, if (unreadCount > 0) Color(0xFFC084FC) else Color(0xFFE2E8F0)),
        shadowElevation = 2.dp,
        modifier = modifier
            .fillMaxWidth()
            .heightIn(min = 88.dp),
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 20.dp, vertical = 16.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween,
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(16.dp),
                modifier = Modifier.weight(1f),
            ) {
                ContactAvatar(
                    displayName = displayName,
                    photoReference = photoReference,
                    size = 56.dp,
                    unread = unreadCount > 0,
                    isPriority = !relationship.isNullOrBlank(),
                )

                Column(
                    verticalArrangement = Arrangement.spacedBy(4.dp),
                ) {
                    Text(
                        text = displayName,
                        style = MaterialTheme.typography.titleMedium,
                        color = TextSlatePrimary,
                        fontWeight = FontWeight.Bold,
                        fontSize = 20.sp,
                    )
                    if (!relationship.isNullOrBlank()) {
                        Text(
                            text = relationship,
                            style = MaterialTheme.typography.bodySmall,
                            color = CardCallAccent,
                            fontWeight = FontWeight.SemiBold,
                            fontSize = 13.sp,
                        )
                    }
                }
            }

            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                if (unreadCount > 0) {
                    Surface(
                        shape = CircleShape,
                        color = BadgeRed,
                        modifier = Modifier.size(28.dp),
                    ) {
                        Box(contentAlignment = Alignment.Center) {
                            Text(
                                text = "$unreadCount",
                                color = Color.White,
                                style = MaterialTheme.typography.labelSmall,
                                fontWeight = FontWeight.Bold,
                                fontSize = 14.sp,
                            )
                        }
                    }
                }

                Surface(
                    shape = CircleShape,
                    color = CardMessageAccent.copy(alpha = 0.12f),
                    modifier = Modifier.size(44.dp),
                ) {
                    Box(contentAlignment = Alignment.Center) {
                        Icon(
                            imageVector = Icons.Rounded.Chat,
                            contentDescription = "گفتگو",
                            tint = CardMessageAccent,
                            modifier = Modifier.size(22.dp),
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun ContactSuggestionCard(
    displayName: String,
    relationship: String?,
    photoReference: String?,
    isPriority: Boolean,
    actionButtonText: String,
    actionButtonIcon: androidx.compose.ui.graphics.vector.ImageVector,
    actionButtonColor: Color,
    onActionClick: () -> Unit,
    modifier: Modifier = Modifier,
    unreadCount: Int = 0,
    secondaryButtonText: String? = null,
    secondaryButtonIcon: androidx.compose.ui.graphics.vector.ImageVector? = null,
    onSecondaryClick: (() -> Unit)? = null,
) {
    Surface(
        onClick = onActionClick,
        shape = RoundedCornerShape(28.dp),
        color = Color.White,
        border = BorderStroke(1.5.dp, if (unreadCount > 0) Color(0xFFC084FC) else Color(0xFFE2E8F0)),
        shadowElevation = 3.dp,
        modifier = modifier
            .fillMaxWidth()
            .heightIn(min = 230.dp),
    ) {
        Column(
            modifier = Modifier.padding(18.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.SpaceBetween,
        ) {
            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
            ) {
                // Large circular photo (Instagram style with optional colored ring for priority/unread)
                Box(contentAlignment = Alignment.TopEnd) {
                    ContactAvatar(
                        displayName = displayName,
                        photoReference = photoReference,
                        size = 80.dp,
                        unread = unreadCount > 0,
                        isPriority = isPriority,
                    )
                    if (unreadCount > 0) {
                        Surface(
                            shape = CircleShape,
                            color = BadgeRed,
                            modifier = Modifier.size(24.dp),
                        ) {
                            Box(contentAlignment = Alignment.Center) {
                                Text(
                                    text = "$unreadCount",
                                    color = Color.White,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 12.sp,
                                )
                            }
                        }
                    }
                }

                Spacer(modifier = Modifier.height(10.dp))

                Text(
                    text = displayName,
                    style = MaterialTheme.typography.titleLarge,
                    color = TextSlatePrimary,
                    fontWeight = FontWeight.Bold,
                    fontSize = 20.sp,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )

                Spacer(modifier = Modifier.height(3.dp))

                Text(
                    text = relationship ?: if (isPriority) "مخاطب اصلی" else "خانواده",
                    style = MaterialTheme.typography.bodyMedium,
                    color = TextSlateSecondary,
                    fontSize = 14.sp,
                    maxLines = 1,
                )
            }

            Spacer(modifier = Modifier.height(14.dp))

            Column(
                modifier = Modifier.fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                // Primary Action Button (Call or Message)
                Surface(
                    onClick = onActionClick,
                    shape = RoundedCornerShape(18.dp),
                    color = actionButtonColor,
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(48.dp),
                ) {
                    Row(
                        modifier = Modifier.fillMaxSize(),
                        horizontalArrangement = Arrangement.Center,
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Icon(
                            imageVector = actionButtonIcon,
                            contentDescription = null,
                            tint = Color.White,
                            modifier = Modifier.size(20.dp),
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = actionButtonText,
                            color = Color.White,
                            fontWeight = FontWeight.Bold,
                            fontSize = 15.sp,
                        )
                    }
                }

                if (secondaryButtonText != null && onSecondaryClick != null) {
                    Surface(
                        onClick = onSecondaryClick,
                        shape = RoundedCornerShape(18.dp),
                        color = Color(0xFFF1F5F9),
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(42.dp),
                    ) {
                        Row(
                            modifier = Modifier.fillMaxSize(),
                            horizontalArrangement = Arrangement.Center,
                            verticalAlignment = Alignment.CenterVertically,
                        ) {
                            if (secondaryButtonIcon != null) {
                                Icon(
                                    imageVector = secondaryButtonIcon,
                                    contentDescription = null,
                                    tint = TextSlatePrimary,
                                    modifier = Modifier.size(18.dp),
                                )
                                Spacer(modifier = Modifier.width(6.dp))
                            }
                            Text(
                                text = secondaryButtonText,
                                color = TextSlatePrimary,
                                fontWeight = FontWeight.SemiBold,
                                fontSize = 13.sp,
                            )
                        }
                    }
                }
            }
        }
    }
}

