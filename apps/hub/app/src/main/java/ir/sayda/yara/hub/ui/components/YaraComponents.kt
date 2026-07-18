package ir.sayda.yara.hub.ui.components

import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.*
import androidx.compose.material3.*
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
import ir.sayda.yara.hub.ui.theme.*

/**
 * Organic background element with gentle leaf-inspired curves.
 * Creates a sense of "breathing" and premium healthcare atmosphere.
 */
@Composable
fun TodayBackground(modifier: Modifier = Modifier) {
    Canvas(modifier = modifier.fillMaxSize()) {
        val width = size.width
        val height = size.height

        // Top subtle curve line (Yara Light Green)
        val topCurve = Path().apply {
            moveTo(0f, height * 0.22f)
            quadraticBezierTo(width * 0.5f, height * 0.18f, width, height * 0.24f)
        }
        drawPath(
            path = topCurve,
            color = YaraLightGreen.copy(alpha = 0.6f),
            style = Stroke(width = 2.dp.toPx())
        )

        // Bottom large organic wave (Yara Green Identity)
        val bottomPath = Path().apply {
            moveTo(0f, height * 0.85f)
            cubicTo(
                width * 0.35f, height * 0.80f,
                width * 0.65f, height * 0.95f,
                width, height * 0.88f
            )
            lineTo(width, height)
            lineTo(0f, height)
            close()
        }
        drawPath(path = bottomPath, color = YaraGreen, style = Fill)
    }
}

/**
 * Premium header containing branding, slogan, date, and time.
 * RTL logic: Right (Logo/Slogan), Left (Clock/Date).
 */
@Composable
fun BrandHeader(
    time: String,
    date: String,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .padding(horizontal = 32.dp, vertical = 32.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.Top
    ) {
        // Branding (Right side in RTL)
        Row(verticalAlignment = Alignment.CenterVertically) {
            Column(horizontalAlignment = Alignment.End) {
                Text(
                    text = "یارا",
                    style = MaterialTheme.typography.titleLarge,
                    color = YaraGreen,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp
                )
                Text(
                    text = "همدم هوشمند سالمندان",
                    style = MaterialTheme.typography.labelMedium,
                    color = TextSecondary,
                    fontSize = 12.sp,
                    lineHeight = 16.sp
                )
            }
            Spacer(modifier = Modifier.width(16.dp))
            Box(
                modifier = Modifier
                    .size(56.dp)
                    .clip(CircleShape)
                    .background(YaraLightGreen),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = Icons.Rounded.Eco,
                    contentDescription = null,
                    tint = YaraGreen,
                    modifier = Modifier.size(36.dp)
                )
            }
        }

        // Clock & Date (Left side in RTL)
        Column(horizontalAlignment = Alignment.Start) {
            Text(
                text = time,
                style = MaterialTheme.typography.displayMedium,
                color = TextPrimary,
                fontWeight = FontWeight.Medium
            )
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    imageVector = Icons.Rounded.CalendarToday,
                    contentDescription = null,
                    tint = YaraGreen,
                    modifier = Modifier.size(20.dp)
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = date,
                    style = MaterialTheme.typography.labelMedium,
                    color = TextSecondary,
                    fontSize = 16.sp
                )
            }
        }
    }
}

/**
 * Human-centric greeting.
 */
@Composable
fun GreetingSection(name: String, modifier: Modifier = Modifier) {
    Column(
        modifier = modifier.fillMaxWidth(),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            text = "سلام، وقت بخیر",
            style = MaterialTheme.typography.headlineLarge,
            color = TextPrimary
        )
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.Center
        ) {
            Text(
                text = name,
                style = MaterialTheme.typography.headlineMedium,
                color = TextPrimary,
                fontWeight = FontWeight.Medium
            )
            Spacer(modifier = Modifier.width(8.dp))
            Icon(
                imageVector = Icons.Rounded.Spa,
                contentDescription = null,
                tint = YaraGreen,
                modifier = Modifier.size(28.dp)
            )
        }
        Spacer(modifier = Modifier.height(16.dp))
        Text(
            text = "امیدوارم امروز روز خوبی داشته باشید.",
            style = MaterialTheme.typography.bodyLarge,
            color = TextSecondary
        )
    }
}

/**
 * Reusable Base Card for the Yara Design System.
 * Ensures 100% consistency across Medication, Voice Messages, and Contacts.
 */
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
    modifier: Modifier = Modifier
) {
    Surface(
        onClick = onClick,
        shape = RoundedCornerShape(24.dp),
        color = Color.White,
        border = if (borderColor != Color.Transparent) BorderStroke(2.dp, borderColor) else null,
        shadowElevation = 4.dp,
        modifier = modifier
            .fillMaxWidth()
            .heightIn(min = 120.dp)
    ) {
        Row(
            modifier = Modifier.padding(24.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Icon (Right side in RTL)
            Box(
                modifier = Modifier
                    .size(80.dp)
                    .clip(CircleShape)
                    .background(iconBackground),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = icon,
                    contentDescription = null,
                    tint = iconColor,
                    modifier = Modifier.size(48.dp)
                )
            }
            
            Spacer(modifier = Modifier.width(24.dp))
            
            // Text Content (Middle)
            Column(modifier = Modifier.weight(1f), horizontalAlignment = Alignment.Start) {
                Text(
                    text = title,
                    style = MaterialTheme.typography.labelMedium,
                    color = TextSecondary
                )
                Text(
                    text = subtitle,
                    style = MaterialTheme.typography.titleLarge,
                    color = TextPrimary,
                    fontWeight = FontWeight.Bold
                )
                if (description != null) {
                    Text(
                        text = description,
                        style = MaterialTheme.typography.bodyLarge,
                        color = TextPrimary
                    )
                }
            }
            
            Spacer(modifier = Modifier.width(16.dp))
            
            // Navigation Arrow (Left side in RTL)
            Icon(
                imageVector = Icons.Rounded.ChevronLeft,
                contentDescription = null,
                tint = TextSecondary.copy(alpha = 0.3f),
                modifier = Modifier.size(32.dp)
            )
        }
    }
}

@Composable
fun MedicationCard(
    medicationName: String,
    time: String,
    isOverdue: Boolean = false,
    onClick: () -> Unit
) {
    YaraBaseCard(
        onClick = onClick,
        icon = Icons.Rounded.Medication,
        iconColor = if (isOverdue) SoftOrange else YaraGreen,
        iconBackground = if (isOverdue) SoftOrange.copy(alpha = 0.1f) else YaraLightGreen,
        title = "وقت مصرف دارو",
        subtitle = medicationName,
        description = time,
        borderColor = if (isOverdue) SoftOrange else YaraGreen.copy(alpha = 0.4f)
    )
}

@Composable
fun VoiceMessageCard(
    from: String,
    onClick: () -> Unit
) {
    YaraBaseCard(
        onClick = onClick,
        icon = Icons.Rounded.PlayArrow,
        iconColor = SoftBlue,
        iconBackground = SoftBlue.copy(alpha = 0.1f),
        title = "پیام صوتی جدید",
        subtitle = from
    )
}

@Composable
fun ContactCard(
    name: String,
    onClick: () -> Unit
) {
    YaraBaseCard(
        onClick = onClick,
        icon = Icons.Rounded.Call,
        iconColor = YaraGreen,
        iconBackground = YaraLightGreen,
        title = "تماس با خانواده",
        subtitle = name
    )
}

@OptIn(ExperimentalFoundationApi::class)
@Composable
fun SettingsButton(
    onLongClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Box(
        modifier = modifier
            .size(64.dp)
            .clip(RoundedCornerShape(24.dp))
            .combinedClickable(
                onClick = {},
                onLongClick = onLongClick
            ),
        contentAlignment = Alignment.Center
    ) {
        Icon(
            imageVector = Icons.Rounded.Settings,
            contentDescription = "تنظیمات",
            tint = Color.White.copy(alpha = 0.8f),
            modifier = Modifier.size(32.dp)
        )
    }
}
