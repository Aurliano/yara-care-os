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
import ir.sayda.yara.hub.core.domain.model.ProvisioningState
import ir.sayda.yara.hub.feature.home.HomeViewModel
import ir.sayda.yara.hub.feature.home.presentation.formatEpochForDisplay

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DeveloperSettingsScreen(
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
    viewModel: HomeViewModel = hiltViewModel(),
    devViewModel: DeveloperSettingsViewModel = hiltViewModel(),
) {
    val snapshot by viewModel.snapshot.collectAsStateWithLifecycle()
    val context = LocalContext.current
    val diagnosticReport = buildString {
        appendLine("Yara Hub Developer Report")
        appendLine("App version: ${BuildConfig.VERSION_NAME} (${BuildConfig.VERSION_CODE})")
        appendLine("Build variant: ${BuildConfig.BUILD_TYPE}")
        appendLine("Debug: ${BuildConfig.DEBUG}")
        appendLine()
        appendLine("Backend URL: ${snapshot.backendUrl ?: "—"}")
        appendLine("Device ID: ${snapshot.deviceId ?: "—"}")
        appendLine("Replica ID: ${snapshot.replicaId ?: "—"}")
        appendLine("Provisioning state: ${snapshot.provisioningState}")
        appendLine("Provisioning error: ${snapshot.lastProvisioningError ?: "—"}")
        appendLine("Authenticated: ${snapshot.isAuthenticated}")
        appendLine("JWT expiration: ${formatEpochForDisplay(snapshot.tokenExpiresAtEpochMillis)}")
        appendLine("Last authentication: ${formatEpochForDisplay(snapshot.lastAuthenticatedAtEpochMillis)}")
        appendLine("Connection type: ${snapshot.connectionType}")
        appendLine("Connectivity: ${snapshot.connectivityState}")
        appendLine()
        appendLine("Runtime kernel: ${snapshot.runtimeHealth}")
        appendLine("Replica health: ${snapshot.replicaHealth}")
        appendLine("Checkpoint sequence: ${snapshot.checkpointSequence}")
        appendLine("Online: ${snapshot.isOnline}")
        appendLine("Sync available: ${snapshot.synchronizationAvailable}")
        appendLine("Last sync: ${formatEpochForDisplay(snapshot.lastSyncEpochMillis)}")
        appendLine("Last download session: ${snapshot.lastDownloadSessionId ?: "—"}")
        appendLine("Pending evidence: ${snapshot.pendingEvidenceCount}")
        appendLine("Outbox pending: ${snapshot.outboxPendingCount}")
        appendLine("Sync conflicts: ${snapshot.syncConflictCount}")
        appendLine("Registered alarms: ${snapshot.registeredAlarmCount}")
        appendLine("Active executions: ${snapshot.activeExecutions.size}")
        appendLine("Today reminders: ${snapshot.todayReminders.size}")
        appendLine("Care activities: ${snapshot.careActivityCount}")
        appendLine("Workflow definitions: ${snapshot.workflowDefinitionCount}")
        appendLine("Workflow executions: ${snapshot.workflowExecutionCount}")
        appendLine("Schedules: ${snapshot.scheduleDefinitionCount}")
        appendLine("Occurrences: ${snapshot.occurrenceCount}")
        appendLine("Devices: ${snapshot.deviceCount}")
        appendLine("Device commands: ${snapshot.deviceCommandCount}")
        appendLine("Communication sessions: ${snapshot.communicationSessionCount}")
        appendLine("Contacts: ${snapshot.contactCount}")
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
            DiagnosticRow("Backend URL", snapshot.backendUrl ?: "—")
            DiagnosticRow("Device ID", snapshot.deviceId ?: "—")
            DiagnosticRow("Replica ID", snapshot.replicaId ?: "—")
            DiagnosticRow("Provisioning", snapshot.provisioningState.name)
            DiagnosticRow("Provisioning error", snapshot.lastProvisioningError ?: "—")
            DiagnosticRow("Authenticated", snapshot.isAuthenticated.toString())
            DiagnosticRow("JWT expiration", formatEpochForDisplay(snapshot.tokenExpiresAtEpochMillis))
            DiagnosticRow("Last authentication", formatEpochForDisplay(snapshot.lastAuthenticatedAtEpochMillis))
            DiagnosticRow("Connection type", snapshot.connectionType)
            DiagnosticRow("Connectivity", snapshot.connectivityState.name)
            DiagnosticRow("Runtime kernel", snapshot.runtimeHealth)
            DiagnosticRow("Replica health", snapshot.replicaHealth)
            DiagnosticRow("Checkpoint", snapshot.checkpointSequence.toString())
            DiagnosticRow(
                "Synchronization",
                if (snapshot.synchronizationAvailable) "AVAILABLE" else "DISABLED",
            )
            DiagnosticRow("Last sync", formatEpochForDisplay(snapshot.lastSyncEpochMillis))
            DiagnosticRow("Last download session", snapshot.lastDownloadSessionId ?: "—")
            DiagnosticRow("PendingEvidence", snapshot.pendingEvidenceCount.toString())
            DiagnosticRow("Outbox", snapshot.outboxPendingCount.toString())
            DiagnosticRow("Sync conflicts", snapshot.syncConflictCount.toString())
            DiagnosticRow("Alarm count", snapshot.registeredAlarmCount.toString())
            DiagnosticRow("Care activities", snapshot.careActivityCount.toString())
            DiagnosticRow("Workflow definitions", snapshot.workflowDefinitionCount.toString())
            DiagnosticRow("Workflow executions", snapshot.workflowExecutionCount.toString())
            DiagnosticRow("Schedules", snapshot.scheduleDefinitionCount.toString())
            DiagnosticRow("Occurrences", snapshot.occurrenceCount.toString())
            DiagnosticRow("Devices", snapshot.deviceCount.toString())
            DiagnosticRow("Device commands", snapshot.deviceCommandCount.toString())
            DiagnosticRow("Communication sessions", snapshot.communicationSessionCount.toString())
            DiagnosticRow("Contacts", snapshot.contactCount.toString())
            DiagnosticRow("Database version", "3")
            DiagnosticRow("Worker status", "IntegrationRuntimeWorker scheduled")
            DiagnosticRow("App version", "${BuildConfig.VERSION_NAME} (${BuildConfig.VERSION_CODE})")
            DiagnosticRow("Build variant", BuildConfig.BUILD_TYPE)
            if (snapshot.provisioningState == ProvisioningState.READY && snapshot.isAuthenticated) {
                DiagnosticRow("Status", "READY — device provisioned")
            }
            if (snapshot.provisioningState == ProvisioningState.READY && snapshot.isAuthenticated) {
                Button(
                    onClick = { devViewModel.scheduleTestReminderInOneMinute() },
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Text("Schedule local test (1 min)")
                }
                Button(
                    onClick = { devViewModel.forceSynchronization() },
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Text("Force sync now")
                }
            }
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
