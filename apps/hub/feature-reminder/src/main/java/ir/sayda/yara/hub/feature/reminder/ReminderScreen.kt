package ir.sayda.yara.hub.feature.reminder

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.AccessTime
import androidx.compose.material.icons.rounded.CheckCircle
import androidx.compose.material.icons.rounded.Medication
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import ir.sayda.yara.hub.ui.components.ReminderLoadingIndicator
import ir.sayda.yara.hub.ui.components.TodayBackground
import ir.sayda.yara.hub.ui.theme.CardMedicationAccent
import ir.sayda.yara.hub.ui.theme.CardMedicationBadgeBg
import ir.sayda.yara.hub.ui.theme.CardMedicationBadgeText
import ir.sayda.yara.hub.ui.theme.CardMedicationBgEnd
import ir.sayda.yara.hub.ui.theme.CardMedicationBgStart
import ir.sayda.yara.hub.ui.theme.CardMedicationBorder
import ir.sayda.yara.hub.ui.theme.CardMedicationIconBg
import ir.sayda.yara.hub.ui.theme.SurfaceGray
import ir.sayda.yara.hub.ui.theme.TabletBg
import ir.sayda.yara.hub.ui.theme.TextSlatePrimary
import ir.sayda.yara.hub.ui.theme.TextSlateSecondary
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

@Composable
fun ReminderRoute(
    executionId: String,
    onFinished: () -> Unit,
    modifier: Modifier = Modifier,
    viewModel: ReminderViewModel = hiltViewModel(),
) {
    val presentation by viewModel.presentation.collectAsStateWithLifecycle()
    val confirmationState by viewModel.confirmationState.collectAsStateWithLifecycle()
    val postponeState by viewModel.postponeState.collectAsStateWithLifecycle()

    LaunchedEffect(executionId) {
        viewModel.load(executionId)
    }

    LaunchedEffect(confirmationState) {
        if (confirmationState is ReminderViewModel.ConfirmationState.Completed) {
            onFinished()
        }
    }

    LaunchedEffect(postponeState) {
        if (postponeState is ReminderViewModel.PostponeState.Completed) {
            onFinished()
        }
    }

    LaunchedEffect(presentation) {
        val reminder = presentation
        if (reminder != null && reminder.localConfirmationRecorded) {
            onFinished()
        }
    }

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
                        .padding(innerPadding)
                        .padding(24.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center,
                ) {
                    val reminder = presentation
                    if (reminder == null) {
                        ReminderLoadingIndicator()
                    } else {
                        val time = SimpleDateFormat("HH:mm", Locale("fa", "IR"))
                            .format(Date(reminder.scheduledForEpochMillis))
                        val actionBusy = confirmationState is ReminderViewModel.ConfirmationState.Submitting ||
                            postponeState is ReminderViewModel.PostponeState.Submitting
                        val locallyConfirmed = reminder.localConfirmationRecorded ||
                            confirmationState is ReminderViewModel.ConfirmationState.Completed

                        Surface(
                            shape = RoundedCornerShape(36.dp),
                            color = Color.Transparent,
                            border = BorderStroke(2.dp, CardMedicationBorder),
                            shadowElevation = 6.dp,
                            modifier = Modifier
                                .widthIn(max = 560.dp)
                                .fillMaxWidth(),
                        ) {
                            Box(
                                modifier = Modifier
                                    .background(
                                        Brush.verticalGradient(
                                            listOf(CardMedicationBgStart, CardMedicationBgEnd),
                                        ),
                                    )
                                    .padding(horizontal = 36.dp, vertical = 36.dp),
                            ) {
                                Column(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalAlignment = Alignment.CenterHorizontally,
                                ) {
                                    // Top Medicine Icon
                                    Surface(
                                        shape = CircleShape,
                                        color = CardMedicationIconBg,
                                        shadowElevation = 4.dp,
                                        modifier = Modifier.size(80.dp),
                                    ) {
                                        Box(
                                            contentAlignment = Alignment.Center,
                                            modifier = Modifier.fillMaxSize(),
                                        ) {
                                            Icon(
                                                imageVector = Icons.Rounded.Medication,
                                                contentDescription = null,
                                                tint = Color.White,
                                                modifier = Modifier.size(44.dp),
                                            )
                                        }
                                    }

                                    Spacer(modifier = Modifier.height(16.dp))

                                    Text(
                                        text = "وقت مصرف دارو",
                                        style = MaterialTheme.typography.titleMedium,
                                        color = TextSlateSecondary,
                                        fontSize = 18.sp,
                                    )

                                    Spacer(modifier = Modifier.height(8.dp))

                                    Text(
                                        text = reminder.title,
                                        style = MaterialTheme.typography.headlineLarge,
                                        color = TextSlatePrimary,
                                        fontWeight = FontWeight.Bold,
                                        fontSize = 32.sp,
                                        textAlign = TextAlign.Center,
                                    )

                                    Spacer(modifier = Modifier.height(12.dp))

                                    // Scheduled Time Badge
                                    Surface(
                                        shape = RoundedCornerShape(16.dp),
                                        color = CardMedicationBadgeBg,
                                        modifier = Modifier.height(36.dp),
                                    ) {
                                        Row(
                                            modifier = Modifier.padding(horizontal = 14.dp),
                                            verticalAlignment = Alignment.CenterVertically,
                                            horizontalArrangement = Arrangement.spacedBy(6.dp),
                                        ) {
                                            Icon(
                                                imageVector = Icons.Rounded.AccessTime,
                                                contentDescription = null,
                                                tint = CardMedicationBadgeText,
                                                modifier = Modifier.size(18.dp),
                                            )
                                            Text(
                                                text = "ساعت $time",
                                                style = MaterialTheme.typography.labelMedium,
                                                color = CardMedicationBadgeText,
                                                fontWeight = FontWeight.SemiBold,
                                                fontSize = 15.sp,
                                            )
                                        }
                                    }

                                    if (reminder.friendlyDescription.isNotBlank()) {
                                        Spacer(modifier = Modifier.height(14.dp))
                                        Text(
                                            text = reminder.friendlyDescription,
                                            style = MaterialTheme.typography.bodyLarge,
                                            color = TextSlateSecondary,
                                            textAlign = TextAlign.Center,
                                            fontSize = 18.sp,
                                            lineHeight = 26.sp,
                                        )
                                    }

                                    if (locallyConfirmed) {
                                        Spacer(modifier = Modifier.height(16.dp))
                                        Surface(
                                            shape = RoundedCornerShape(16.dp),
                                            color = CardMedicationBadgeBg,
                                            modifier = Modifier.padding(horizontal = 16.dp, vertical = 4.dp),
                                        ) {
                                            Row(
                                                modifier = Modifier.padding(horizontal = 14.dp, vertical = 6.dp),
                                                verticalAlignment = Alignment.CenterVertically,
                                                horizontalArrangement = Arrangement.spacedBy(8.dp),
                                            ) {
                                                Icon(
                                                    imageVector = Icons.Rounded.CheckCircle,
                                                    contentDescription = null,
                                                    tint = CardMedicationAccent,
                                                    modifier = Modifier.size(20.dp),
                                                )
                                                Text(
                                                    text = "مصرف دارو ثبت شد ✓",
                                                    color = CardMedicationAccent,
                                                    style = MaterialTheme.typography.titleMedium,
                                                    fontWeight = FontWeight.Bold,
                                                )
                                            }
                                        }
                                    }

                                    val postponeFailed = postponeState as? ReminderViewModel.PostponeState.Failed
                                    if (postponeFailed != null) {
                                        Spacer(modifier = Modifier.height(8.dp))
                                        Text(
                                            text = postponeFailed.message,
                                            color = MaterialTheme.colorScheme.error,
                                            style = MaterialTheme.typography.bodyMedium,
                                        )
                                    }

                                    Spacer(modifier = Modifier.height(28.dp))

                                    // Action 1: Confirm Taken (Primary green pill)
                                    Surface(
                                        onClick = { viewModel.confirm(reminder.executionId) },
                                        enabled = !locallyConfirmed && !actionBusy,
                                        shape = RoundedCornerShape(28.dp),
                                        color = if (!locallyConfirmed && !actionBusy) CardMedicationAccent else TextSlateSecondary.copy(alpha = 0.2f),
                                        shadowElevation = if (!locallyConfirmed && !actionBusy) 3.dp else 0.dp,
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
                                                imageVector = Icons.Rounded.CheckCircle,
                                                contentDescription = null,
                                                tint = if (!locallyConfirmed && !actionBusy) Color.White else TextSlateSecondary,
                                                modifier = Modifier.size(26.dp),
                                            )
                                            Spacer(modifier = Modifier.width(10.dp))
                                            Text(
                                                text = if (locallyConfirmed) "ثبت شد" else "تأیید مصرف دارو",
                                                style = MaterialTheme.typography.titleLarge,
                                                color = if (!locallyConfirmed && !actionBusy) Color.White else TextSlateSecondary,
                                                fontWeight = FontWeight.Bold,
                                                fontSize = 20.sp,
                                            )
                                        }
                                    }

                                    // Action 2: Postpone
                                    if (reminder.postponeAllowed && !locallyConfirmed) {
                                        Spacer(modifier = Modifier.height(14.dp))
                                        val postponeLabel = if (reminder.postponeDelayMinutes > 0) {
                                            "به بعد انداختن (${reminder.postponeDelayMinutes} دقیقه)"
                                        } else {
                                            "به بعد انداختن"
                                        }
                                        Surface(
                                            onClick = { viewModel.postpone(reminder.executionId) },
                                            enabled = !actionBusy,
                                            shape = RoundedCornerShape(28.dp),
                                            color = SurfaceGray,
                                            border = BorderStroke(1.5.dp, Color(0xFFE2E8F0)),
                                            modifier = Modifier
                                                .fillMaxWidth()
                                                .height(54.dp),
                                        ) {
                                            Row(
                                                modifier = Modifier.fillMaxSize(),
                                                horizontalArrangement = Arrangement.Center,
                                                verticalAlignment = Alignment.CenterVertically,
                                            ) {
                                                Icon(
                                                    imageVector = Icons.Rounded.AccessTime,
                                                    contentDescription = null,
                                                    tint = TextSlateSecondary,
                                                    modifier = Modifier.size(20.dp),
                                                )
                                                Spacer(modifier = Modifier.width(8.dp))
                                                Text(
                                                    text = postponeLabel,
                                                    style = MaterialTheme.typography.titleMedium,
                                                    color = TextSlatePrimary,
                                                    fontWeight = FontWeight.SemiBold,
                                                    fontSize = 16.sp,
                                                )
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
