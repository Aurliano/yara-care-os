package ir.sayda.yara.hub.alarm

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import dagger.hilt.android.AndroidEntryPoint
import ir.sayda.yara.hub.core.runtime.RuntimeScheduler
import javax.inject.Inject

@AndroidEntryPoint
class OccurrenceAlarmReceiver : BroadcastReceiver() {

    @Inject lateinit var runtimeScheduler: RuntimeScheduler

    override fun onReceive(context: Context, intent: Intent?) {
        if (intent?.action != ACTION_OCCURRENCE_ALARM) return
        val occurrenceId = intent.getStringExtra(EXTRA_OCCURRENCE_ID) ?: return
        runtimeScheduler.scheduleOneTimeRuntimeWork(occurrenceId)
    }

    companion object {
        const val ACTION_OCCURRENCE_ALARM = "ir.sayda.yara.hub.action.OCCURRENCE_ALARM"
        const val EXTRA_OCCURRENCE_ID = "occurrence_id"
    }
}
