package ir.sayda.yara.hub.receiver

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import ir.sayda.yara.hub.MainActivity

class MedicationReminderReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        val medicationId = intent.getStringExtra("MEDICATION_ID") ?: return
        
        // Bring the app to the foreground and show the reminder
        val mainActivityIntent = Intent(context, MainActivity::class.java).apply {
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP)
            addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP)
            putExtra("SHOW_REMINDER_ID", medicationId)
        }
        
        context.startActivity(mainActivityIntent)
    }
}
