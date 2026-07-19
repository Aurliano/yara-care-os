package ir.sayda.yara.hub

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.runtime.*
import ir.sayda.yara.hub.data.repository.InMemoryMedicationRepository
import ir.sayda.yara.hub.domain.model.Medication
import ir.sayda.yara.hub.features.home.TodayScreen
import ir.sayda.yara.hub.features.medication.MedicationReminderScreen
import ir.sayda.yara.hub.ui.theme.HubTheme
import kotlinx.coroutines.launch

/**
 * Main entry point managing navigation between Home and Medication flow.
 */
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            HubTheme {
                AppNavigation()
            }
        }
    }
}

@Composable
fun AppNavigation() {
    val repository = InMemoryMedicationRepository
    val scope = rememberCoroutineScope()
    
    // Simple state-based navigation for MVP
    var currentScreen by remember { mutableStateOf<Screen>(Screen.Home) }

    when (val screen = currentScreen) {
        is Screen.Home -> {
            TodayScreen(
                repository = repository,
                onMedicationClick = { medication ->
                    if (!medication.isCompleted) {
                        currentScreen = Screen.MedicationReminder(medication)
                    }
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
    }
}

sealed class Screen {
    object Home : Screen()
    data class MedicationReminder(val medication: Medication) : Screen()
}
