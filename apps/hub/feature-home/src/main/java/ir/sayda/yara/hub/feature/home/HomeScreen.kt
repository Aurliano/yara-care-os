package ir.sayda.yara.hub.feature.home

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import ir.sayda.yara.hub.ui.components.BrandHeader
import ir.sayda.yara.hub.ui.components.ContactCard
import ir.sayda.yara.hub.ui.components.GreetingSection
import ir.sayda.yara.hub.ui.components.RuntimeStatusCard
import ir.sayda.yara.hub.ui.components.SettingsButton
import ir.sayda.yara.hub.ui.components.TodayBackground
import ir.sayda.yara.hub.ui.components.TodayReminderCard
import ir.sayda.yara.hub.ui.components.VoiceMessageCard
import ir.sayda.yara.hub.ui.theme.TextSecondary
import ir.sayda.yara.hub.ui.theme.WarmWhite
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

@Composable
fun HomeRoute(
    onSettingsLongPress: () -> Unit,
    modifier: Modifier = Modifier,
    viewModel: HomeViewModel = hiltViewModel(),
) {
    val snapshot by viewModel.snapshot.collectAsStateWithLifecycle()
    val now = Date()
    val timeFormatter = SimpleDateFormat("HH:mm", Locale("fa", "IR"))
    val dateFormatter = SimpleDateFormat("EEEE، d MMMM yyyy", Locale("fa", "IR"))
    val reminderTimeFormatter = SimpleDateFormat("HH:mm", Locale("fa", "IR"))

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
                    )
                    LazyColumn(
                        modifier = Modifier.fillMaxSize(),
                        contentPadding = PaddingValues(
                            start = 24.dp,
                            end = 24.dp,
                            top = 32.dp,
                            bottom = 120.dp,
                        ),
                        verticalArrangement = Arrangement.spacedBy(24.dp),
                        horizontalAlignment = Alignment.CenterHorizontally,
                    ) {
                        item {
                            GreetingSection(name = snapshot.elderDisplayName)
                            Spacer(modifier = Modifier.height(32.dp))
                        }
                        item {
                            RuntimeStatusCard(
                                replicaHealth = snapshot.replicaHealth,
                                runtimeHealth = snapshot.runtimeHealth,
                                lastSyncEpochMillis = snapshot.lastSyncEpochMillis,
                                isOnline = snapshot.isOnline,
                                activeExecutionCount = snapshot.activeExecutions.size,
                                todayReminderCount = snapshot.todayReminders.size,
                            )
                        }
                        if (snapshot.todayReminders.isNotEmpty()) {
                            item {
                                Text(text = "یادآورهای امروز", color = TextSecondary)
                            }
                            items(snapshot.todayReminders) { reminder ->
                                val description = if (reminder.localConfirmationRecorded) {
                                    "${reminder.friendlyDescription}\n✓ ثبت شد · در انتظار همگام‌سازی"
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
                        if (snapshot.activeExecutions.isNotEmpty()) {
                            item {
                                Text(
                                    text = "اجراهای فعال: ${snapshot.activeExecutions.size}",
                                    color = TextSecondary,
                                )
                            }
                        }
                        items(snapshot.priorityContacts) { contact ->
                            ContactCard(name = contact.displayName, onClick = {})
                        }
                        if (snapshot.priorityContacts.isEmpty()) {
                            item {
                                VoiceMessageCard(from = "خانواده", onClick = {})
                            }
                        }
                    }
                }
                Box(
                    modifier = Modifier
                        .align(Alignment.BottomStart)
                        .padding(24.dp),
                ) {
                    SettingsButton(onLongClick = onSettingsLongPress)
                }
            }
        }
    }
}
