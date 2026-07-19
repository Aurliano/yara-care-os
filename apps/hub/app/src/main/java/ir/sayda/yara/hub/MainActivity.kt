package ir.sayda.yara.hub

import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.runtime.*
import ir.sayda.yara.hub.domain.model.Medication
import ir.sayda.yara.hub.features.home.TodayScreen
import ir.sayda.yara.hub.features.medication.MedicationEditScreen
import ir.sayda.yara.hub.features.medication.MedicationManagementScreen
import ir.sayda.yara.hub.features.medication.MedicationReminderScreen
import ir.sayda.yara.hub.ui.theme.HubTheme
import kotlinx.coroutines.launch
import java.util.Calendar

/**
 * Main entry point managing navigation between Home, Management, and Medication flow.
 */
class MainActivity : ComponentActivity() {

    private val repository get() = (application as YaraApplication).medicationRepository
    
    private var reminderIdToShow = mutableStateOf<String?>(null)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        handleIntent(intent)
        
        enableEdgeToEdge()
        setContent {
            HubTheme {
                AppNavigation(
                    repository = repository,
                    reminderIdFromIntent = reminderIdToShow.value,
                    onReminderConsumed = { reminderIdToShow.value = null }
                )
            }
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        handleIntent(intent)
    }

    private fun handleIntent(intent: Intent?) {
        val reminderId = intent?.getStringExtra("SHOW_REMINDER_ID")
        if (reminderId != null) {
            reminderIdToShow.value = reminderId
        }
    }
}

@Composable
fun AppNavigation(
    repository: ir.sayda.yara.hub.domain.repository.MedicationRepository,
    reminderIdFromIntent: String?,
    onReminderConsumed: () -> Unit
) {
    val scope = rememberCoroutineScope()
    var currentScreen by remember { mutableStateOf<Screen>(Screen.Home) }

    LaunchedEffect(reminderIdFromIntent) {
        if (reminderIdFromIntent != null) {
            val medication = repository.getMedicationById(reminderIdFromIntent)
            if (medication != null && !medication.isCompleted && medication.isEnabled) {
                currentScreen = Screen.MedicationReminder(medication)
            }
            onReminderConsumed()
        }
    }

    when (val screen = currentScreen) {
        is Screen.Home -> {
            TodayScreen(
                repository = repository,
                onMedicationClick = { medication ->
                    if (!medication.isCompleted) {
                        currentScreen = Screen.MedicationReminder(medication)
                    }
                },
                onSettingsClick = {
                    currentScreen = Screen.MedicationManagement
                }
            )
        }
        is Screen.MedicationReminder -> {
            MedicationReminderScreen(
                medication = screen.medication,
                onTaken = {
                    scope.launch {
                        repository.markAsCompleted(screen.medication.id)
                        currentScreen = Screen.Home
                    }
                },
                onBack = {
                    currentScreen = Screen.Home
                }
            )
        }
        is Screen.MedicationManagement -> {
            MedicationManagementScreen(
                repository = repository,
                onAddMedication = {
                    currentScreen = Screen.MedicationEdit(null)
                },
                onEditMedication = { medication ->
                    currentScreen = Screen.MedicationEdit(medication)
                },
                onBack = {
                    currentScreen = Screen.Home
                }
            )
        }
        is Screen.MedicationEdit -> {
            MedicationEditScreen(
                medication = screen.medication,
                onSave = { name, time ->
                    scope.launch {
                        val id = screen.medication?.id ?: "med_${System.currentTimeMillis()}"
                        val scheduledTime = calculateNextOccurrence(time)
                        repository.scheduleMedication(
                            Medication(
                                id = id,
                                name = name,
                                dosageTime = time,
                                scheduledTimeMillis = scheduledTime,
                                isEnabled = screen.medication?.isEnabled ?: true
                            )
                        )
                        currentScreen = Screen.MedicationManagement
                    }
                },
                onDelete = screen.medication?.let { med ->
                    {
                        scope.launch {
                            repository.deleteMedication(med.id)
                            currentScreen = Screen.MedicationManagement
                        }
                    }
                },
                onBack = {
                    currentScreen = Screen.MedicationManagement
                }
            )
        }
    }
}

/**
 * Simple helper to calculate the next occurrence of a HH:mm string.
 */
private fun calculateNextOccurrence(timeStr: String): Long {
    val parts = timeStr.split(":", "：").mapNotNull { it.trim().toIntOrNull() }
    if (parts.size < 2) return System.currentTimeMillis() + 60000 // Fallback to 1 min

    val hour = parts[0]
    val minute = parts[1]

    val calendar = Calendar.getInstance().apply {
        set(Calendar.HOUR_OF_DAY, hour)
        set(Calendar.MINUTE, minute)
        set(Calendar.SECOND, 0)
        set(Calendar.MILLISECOND, 0)
    }

    if (calendar.timeInMillis <= System.currentTimeMillis()) {
        calendar.add(Calendar.DAY_OF_YEAR, 1)
    }
    return calendar.timeInMillis
}

sealed class Screen {
    object Home : Screen()
    data class MedicationReminder(val medication: Medication) : Screen()
    object MedicationManagement : Screen()
    data class MedicationEdit(val medication: Medication?) : Screen()
}
