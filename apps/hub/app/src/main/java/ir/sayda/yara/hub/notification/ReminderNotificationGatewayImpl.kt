package ir.sayda.yara.hub.notification

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import dagger.hilt.android.qualifiers.ApplicationContext
import ir.sayda.yara.hub.MainActivity
import ir.sayda.yara.hub.R
import ir.sayda.yara.hub.core.runtime.ReminderNotificationGateway
import ir.sayda.yara.hub.presentation.ReminderIntentExtras
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ReminderNotificationGatewayImpl @Inject constructor(
    @ApplicationContext private val context: Context,
) : ReminderNotificationGateway {

    override suspend fun showReminderNotification(executionId: String, occurrenceId: String) {
        ensureChannel()
        val contentIntent = PendingIntent.getActivity(
            context,
            executionId.hashCode(),
            reminderIntent(executionId, occurrenceId),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
        val fullScreenIntent = PendingIntent.getActivity(
            context,
            executionId.hashCode() + 1,
            reminderIntent(executionId, occurrenceId),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
        val notification = NotificationCompat.Builder(context, CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_launcher_foreground)
            .setContentTitle("یادآور دارو")
            .setContentText("زمان مصرف دارو رسیده است")
            .setPriority(NotificationCompat.PRIORITY_MAX)
            .setCategory(NotificationCompat.CATEGORY_ALARM)
            .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)
            .setAutoCancel(true)
            .setContentIntent(contentIntent)
            .setFullScreenIntent(fullScreenIntent, true)
            .build()
        notification.flags = notification.flags or Notification.FLAG_INSISTENT
        NotificationManagerCompat.from(context).notify(notificationId(executionId), notification)
    }

    override fun cancelReminderNotification(executionId: String) {
        NotificationManagerCompat.from(context).cancel(notificationId(executionId))
    }

    private fun reminderIntent(executionId: String, occurrenceId: String): Intent =
        Intent(context, MainActivity::class.java).apply {
            action = ReminderIntentExtras.ACTION_OPEN_REMINDER
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP
            putExtra(ReminderIntentExtras.EXTRA_EXECUTION_ID, executionId)
            putExtra(ReminderIntentExtras.EXTRA_OCCURRENCE_ID, occurrenceId)
        }

    private fun ensureChannel() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return
        val manager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        val channel = NotificationChannel(
            CHANNEL_ID,
            "یادآورها",
            NotificationManager.IMPORTANCE_HIGH,
        ).apply {
            description = "یادآورهای مصرف دارو"
            lockscreenVisibility = Notification.VISIBILITY_PUBLIC
            setBypassDnd(true)
        }
        manager.createNotificationChannel(channel)
    }

    private fun notificationId(executionId: String): Int = executionId.hashCode() and 0x7FFFFFFF

    companion object {
        const val CHANNEL_ID = "yara_reminders"
    }
}
