package ir.sayda.yara.hub.ui.components

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.background
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
import androidx.compose.material.icons.rounded.Medication
import androidx.compose.material.icons.rounded.PlayArrow
import androidx.compose.material.icons.rounded.Settings
import androidx.compose.material.icons.rounded.Spa
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Fill
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import ir.sayda.yara.hub.ui.theme.SoftBlue
import ir.sayda.yara.hub.ui.theme.SoftOrange
import ir.sayda.yara.hub.ui.theme.TextPrimary
import ir.sayda.yara.hub.ui.theme.TextSecondary
import ir.sayda.yara.hub.ui.theme.WarmWhite
import ir.sayda.yara.hub.ui.theme.YaraGreen
import ir.sayda.yara.hub.ui.theme.YaraLightGreen
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
fun BrandHeader(time: String, date: String, modifier: Modifier = Modifier) {
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
                    lineHeight = 16.sp,
                )
            }
            Spacer(modifier = Modifier.width(16.dp))
            Box(
                modifier = Modifier
                    .size(56.dp)
                    .clip(CircleShape)
                    .background(YaraLightGreen),
                contentAlignment = Alignment.Center,
            ) {
                Icon(
                    imageVector = Icons.Rounded.Eco,
                    contentDescription = null,
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
            modifier = Modifier.padding(24.dp),
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

@OptIn(ExperimentalFoundationApi::class)
@Composable
fun SettingsButton(onLongClick: () -> Unit, modifier: Modifier = Modifier) {
    Box(
        modifier = modifier
            .size(64.dp)
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
