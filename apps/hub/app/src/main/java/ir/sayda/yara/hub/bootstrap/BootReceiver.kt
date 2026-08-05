package ir.sayda.yara.hub.bootstrap

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import dagger.hilt.android.AndroidEntryPoint
import ir.sayda.yara.hub.core.runtime.RuntimeScheduler
import javax.inject.Inject

@AndroidEntryPoint
class BootReceiver : BroadcastReceiver() {

    @Inject lateinit var runtimeScheduler: RuntimeScheduler

    override fun onReceive(context: Context, intent: Intent?) {
        if (intent?.action != Intent.ACTION_BOOT_COMPLETED &&
            intent?.action != Intent.ACTION_LOCKED_BOOT_COMPLETED
        ) {
            return
        }
        runtimeScheduler.scheduleOneTimeRuntimeWork()
    }
}
