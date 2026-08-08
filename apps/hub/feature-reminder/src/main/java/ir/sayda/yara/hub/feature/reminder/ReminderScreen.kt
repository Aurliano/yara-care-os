package ir.sayda.yara.hub.feature.reminder

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import ir.sayda.yara.hub.ui.components.ReminderActionButton
import ir.sayda.yara.hub.ui.components.ReminderLoadingIndicator
import ir.sayda.yara.hub.ui.components.TodayBackground
import ir.sayda.yara.hub.ui.theme.TextPrimary
import ir.sayda.yara.hub.ui.theme.TextSecondary
import ir.sayda.yara.hub.ui.theme.WarmWhite
import ir.sayda.yara.hub.ui.theme.YaraGreen
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

    LaunchedEffect(executionId) {
        viewModel.load(executionId)
    }

    LaunchedEffect(confirmationState) {
        if (confirmationState is ReminderViewModel.ConfirmationState.Completed) {
            onFinished()
        }
    }

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
                        val locallyConfirmed = reminder.localConfirmationRecorded ||
                            confirmationState is ReminderViewModel.ConfirmationState.Completed
                        Text(text = "وقت مصرف دارو", color = TextSecondary)
                        Spacer(modifier = Modifier.height(12.dp))
                        Text(
                            text = reminder.title,
                            color = TextPrimary,
                            style = MaterialTheme.typography.headlineMedium,
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(text = reminder.friendlyDescription, color = TextPrimary)
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(text = "ساعت $time", color = TextSecondary)
                        if (locallyConfirmed) {
                            Spacer(modifier = Modifier.height(16.dp))
                            Text(
                                text = "ثبت شد ✓",
                                color = YaraGreen,
                                style = MaterialTheme.typography.titleMedium,
                            )
                        }
                        Spacer(modifier = Modifier.height(32.dp))
                        ReminderActionButton(
                            label = if (locallyConfirmed) "ثبت شد" else "تأیید مصرف",
                            enabled = !locallyConfirmed &&
                                confirmationState !is ReminderViewModel.ConfirmationState.Submitting,
                            onClick = { viewModel.confirm(reminder.executionId) },
                            modifier = Modifier.fillMaxWidth(),
                        )
                        Spacer(modifier = Modifier.height(16.dp))
                        ReminderActionButton(
                            label = "به بعد انداختن",
                            enabled = false,
                            onClick = {},
                            modifier = Modifier.fillMaxWidth(),
                        )
                        Spacer(modifier = Modifier.height(16.dp))
                        ReminderActionButton(
                            label = "رد کردن",
                            enabled = false,
                            onClick = {},
                            modifier = Modifier.fillMaxWidth(),
                        )
                    }
                }
            }
        }
    }
}
