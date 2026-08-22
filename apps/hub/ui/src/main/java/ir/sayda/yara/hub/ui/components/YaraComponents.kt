package ir.sayda.yara.hub.ui.components

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.ExperimentalFoundationApi
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
import androidx.compose.material.icons.rounded.CalendarToday
import androidx.compose.material.icons.rounded.Call
import androidx.compose.material.icons.rounded.Check
import androidx.compose.material.icons.rounded.CheckCircle
import androidx.compose.material.icons.rounded.ChevronLeft
import androidx.compose.material.icons.rounded.Eco
import androidx.compose.material.icons.rounded.Cloud
import androidx.compose.material.icons.rounded.CloudOff
import androidx.compose.material.icons.rounded.CloudQueue
import androidx.compose.material.icons.rounded.Medication
import androidx.compose.material.icons.rounded.PlayArrow
import androidx.compose.material.icons.rounded.Settings
import androidx.compose.material.icons.rounded.Spa
import androidx.compose.material.icons.rounded.Wifi
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Fill
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import ir.sayda.yara.hub.ui.presentation.ConnectionVisualState
import ir.sayda.yara.hub.ui.presentation.formatEpochForDisplay
import ir.sayda.yara.hub.ui.theme.Error
import ir.sayda.yara.hub.ui.theme.SoftBlue
import ir.sayda.yara.hub.ui.theme.SoftOrange
import ir.sayda.yara.hub.ui.theme.Success
import ir.sayda.yara.hub.ui.theme.SurfaceGray
import ir.sayda.yara.hub.ui.theme.TextPrimary
import ir.sayda.yara.hub.ui.theme.TextSecondary
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

@OptIn(ExperimentalFoundationApi::class)
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
        Row(verticalAlignment = Alignment.CenterVertically) {
            Column(horizontalAlignment = Alignment.End) {
                Text(
                    text = "یارا",
                    style = MaterialTheme.typography.titleLarge,
                    color = YaraGreen,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp,
                )
                Text(
                    text = "همدم هوشمند سالمندان",
                    style = MaterialTheme.typography.labelMedium,
                    color = TextSecondary,
                    fontSize = 12.sp,
                    lineHeight = 18.sp,
                )
            }
            Spacer(modifier = Modifier.width(16.dp))
            Box(
                modifier = Modifier
                    .size(56.dp)
                    .clip(CircleShape)
                    .background(YaraLightGreen)
                    .clickable {
                        logoTapCount++
                        if (logoTapCount >= 5) {
                            onLogoActivated()
                            logoTapCount = 0
                        }
                    },
                contentAlignment = Alignment.Center,
            ) {
                Icon(
                    imageVector = Icons.Rounded.Eco,
                    contentDescription = "لوگوی یارا",
                    tint = YaraGreen,
                    modifier = Modifier.size(36.dp),
                )
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
fun ContactCard(name: String, onClick: () -> Unit) {
    YaraBaseCard(
        onClick = onClick,
        icon = Icons.Rounded.Call,
        iconColor = YaraGreen,
        iconBackground = YaraLightGreen,
        title = "تماس با خانواده",
        subtitle = name,
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
    val tokens = YaraTheme.colors
    val initial = name.trim().firstOrNull()?.toString().orEmpty()
    Box(
        modifier = modifier
            .size(size)
            .clip(CircleShape)
            .background(tokens.wash),
        contentAlignment = Alignment.Center,
    ) {
        Text(
            text = initial,
            style = MaterialTheme.typography.displayMedium,
            color = tokens.primary,
            fontWeight = FontWeight.Bold,
        )
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
