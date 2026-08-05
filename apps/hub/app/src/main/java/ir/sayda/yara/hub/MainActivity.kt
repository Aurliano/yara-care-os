package ir.sayda.yara.hub

import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.ui.Modifier
import dagger.hilt.android.AndroidEntryPoint
import ir.sayda.yara.hub.core.runtime.ReminderPresentationGateway
import ir.sayda.yara.hub.navigation.HubNavHost
import ir.sayda.yara.hub.presentation.ReminderIntentExtras
import ir.sayda.yara.hub.ui.theme.HubTheme
import javax.inject.Inject
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch

@AndroidEntryPoint
class MainActivity : ComponentActivity() {

    @Inject lateinit var reminderPresentationGateway: ReminderPresentationGateway

    private val activityScope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            HubTheme {
                HubNavHost(modifier = Modifier.fillMaxSize())
            }
        }
        handleReminderIntent(intent)
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        handleReminderIntent(intent)
    }

    private fun handleReminderIntent(intent: Intent?) {
        if (intent?.action != ReminderIntentExtras.ACTION_OPEN_REMINDER) return
        val executionId = intent.getStringExtra(ReminderIntentExtras.EXTRA_EXECUTION_ID) ?: return
        val occurrenceId = intent.getStringExtra(ReminderIntentExtras.EXTRA_OCCURRENCE_ID) ?: return
        activityScope.launch {
            reminderPresentationGateway.openReminder(executionId, occurrenceId)
        }
    }
}
