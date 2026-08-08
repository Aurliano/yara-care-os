package ir.sayda.yara.hub.navigation

import android.content.Intent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import ir.sayda.yara.hub.BuildConfig
import ir.sayda.yara.hub.feature.home.HomeViewModel
import ir.sayda.yara.hub.feature.home.presentation.formatEpochForDisplay

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DeveloperSettingsScreen(
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
    viewModel: HomeViewModel = hiltViewModel(),
) {
    val snapshot by viewModel.snapshot.collectAsStateWithLifecycle()
    val context = LocalContext.current
    val diagnosticReport = buildString {
        appendLine("Yara Hub Developer Report")
        appendLine("App version: ${BuildConfig.VERSION_NAME} (${BuildConfig.VERSION_CODE})")
        appendLine("Build variant: ${BuildConfig.BUILD_TYPE}")
        appendLine("Debug: ${BuildConfig.DEBUG}")
        appendLine()
        appendLine("Runtime: ${snapshot.runtimeHealth}")
        appendLine("Replica: ${snapshot.replicaHealth}")
        appendLine("Online: ${snapshot.isOnline}")
        appendLine("Sync available: ${snapshot.synchronizationAvailable}")
        appendLine("Last sync: ${formatEpochForDisplay(snapshot.lastSyncEpochMillis)}")
        appendLine("Pending evidence: ${snapshot.pendingEvidenceCount}")
        appendLine("Registered alarms: ${snapshot.registeredAlarmCount}")
        appendLine("Active executions: ${snapshot.activeExecutions.size}")
        appendLine("Today reminders: ${snapshot.todayReminders.size}")
        appendLine("Database version: 3")
        appendLine("Worker: IntegrationRuntimeWorker (WorkManager)")
    }

    Scaffold(
        modifier = modifier.fillMaxSize(),
        topBar = {
            TopAppBar(title = { Text("Developer Settings") })
        },
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .padding(24.dp)
                .verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            DiagnosticRow("Runtime", snapshot.runtimeHealth)
            DiagnosticRow("Replica", snapshot.replicaHealth)
            DiagnosticRow("Synchronization", if (snapshot.synchronizationAvailable) "AVAILABLE" else "DISABLED")
            DiagnosticRow("Checkpoint / Last sync", formatEpochForDisplay(snapshot.lastSyncEpochMillis))
            DiagnosticRow("PendingEvidence", snapshot.pendingEvidenceCount.toString())
            DiagnosticRow("Alarm count", snapshot.registeredAlarmCount.toString())
            DiagnosticRow("Database version", "3")
            DiagnosticRow("Worker status", "IntegrationRuntimeWorker scheduled")
            DiagnosticRow("App version", "${BuildConfig.VERSION_NAME} (${BuildConfig.VERSION_CODE})")
            DiagnosticRow("Build variant", BuildConfig.BUILD_TYPE)
            Button(
                onClick = {
                    val shareIntent = Intent(Intent.ACTION_SEND).apply {
                        type = "text/plain"
                        putExtra(Intent.EXTRA_SUBJECT, "Yara Hub diagnostics")
                        putExtra(Intent.EXTRA_TEXT, diagnosticReport)
                    }
                    context.startActivity(Intent.createChooser(shareIntent, "Export log"))
                },
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text("Log export")
            }
            Button(onClick = onBack, modifier = Modifier.fillMaxWidth()) {
                Text("بازگشت")
            }
        }
    }
}

@Composable
private fun DiagnosticRow(label: String, value: String) {
    Column(modifier = Modifier.fillMaxWidth()) {
        Text(text = label, style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.primary)
        Text(text = value, style = MaterialTheme.typography.bodyLarge)
    }
}
