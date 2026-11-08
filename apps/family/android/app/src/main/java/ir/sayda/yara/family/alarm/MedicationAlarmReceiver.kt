package ir.sayda.yara.family.alarm

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.media.AudioAttributes
import android.media.RingtoneManager
import android.net.Uri
import android.os.Build
import android.os.PowerManager
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import ir.sayda.yara.family.MainActivity
import ir.sayda.yara.family.R

class MedicationAlarmReceiver : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        val id = intent.getStringExtra(EXTRA_ID) ?: return
        val title = intent.getStringExtra(EXTRA_TITLE) ?: "داروی تجویزی"
        val dosage = intent.getStringExtra(EXTRA_DOSAGE) ?: ""
        val timeLabel = intent.getStringExtra(EXTRA_TIME_LABEL) ?: ""

        val powerManager = context.getSystemService(Context.POWER_SERVICE) as? PowerManager
        @Suppress("DEPRECATION")
        val wakeLock = powerManager?.newWakeLock(
            PowerManager.PARTIAL_WAKE_LOCK or PowerManager.ACQUIRE_CAUSES_WAKEUP,
            "SaydaFamily:MedicationWakeLock",
        )
        wakeLock?.acquire(15_000L)

        ensureNotificationChannel(context)

        val deepLinkUri = Uri.parse(
            "sayda-family://program/reminder?medicationTitle=${Uri.encode(title)}&dosage=${Uri.encode(dosage)}&timeLabel=${Uri.encode(timeLabel)}&occurrenceId=${Uri.encode(id)}"
        )
        val activityIntent = Intent(context, MainActivity::class.java).apply {
            action = Intent.ACTION_VIEW
            data = deepLinkUri
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP
            putExtra("medicationTitle", title)
            putExtra("dosage", dosage)
            putExtra("timeLabel", timeLabel)
            putExtra("occurrenceId", id)
        }

        val pendingIntent = PendingIntent.getActivity(
            context,
            id.hashCode(),
            activityIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )

        val alarmSound: Uri = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_ALARM)
            ?: RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION)

        val notification = NotificationCompat.Builder(context, CHANNEL_ID)
            .setSmallIcon(R.mipmap.ic_launcher)
            .setContentTitle("وقت مصرف داروی عزیزتان")
            .setContentText(if (dosage.isNotBlank()) "$title ($dosage)" else title)
            .setPriority(NotificationCompat.PRIORITY_MAX)
            .setCategory(NotificationCompat.CATEGORY_ALARM)
            .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)
            .setSound(alarmSound)
            .setVibrate(longArrayOf(0, 500, 250, 500, 250, 500))
            .setAutoCancel(true)
            .setContentIntent(pendingIntent)
            .setFullScreenIntent(pendingIntent, true)
            .build()

        NotificationManagerCompat.from(context).notify(id.hashCode() and 0x7FFFFFFF, notification)

        try {
            context.startActivity(activityIntent)
        } catch (_: Exception) {
            // Android may restrict background activity launch and rely on full-screen intent
        }
    }

    private fun ensureNotificationChannel(context: Context) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return
        val manager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        val alarmSound: Uri = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_ALARM)
            ?: RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION)
        val audioAttributes = AudioAttributes.Builder()
            .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
            .setUsage(AudioAttributes.USAGE_ALARM)
            .build()

        val channel = NotificationChannel(
            CHANNEL_ID,
            "یادآورهای داروی سایدا",
            NotificationManager.IMPORTANCE_HIGH,
        ).apply {
            description = "هشدار تمام‌صفحه و با صدای آلارم برای یادآوری نوبت‌های دارو"
            lockscreenVisibility = NotificationCompat.VISIBILITY_PUBLIC
            setBypassDnd(true)
            setSound(alarmSound, audioAttributes)
            enableVibration(true)
            vibrationPattern = longArrayOf(0, 500, 250, 500, 250, 500)
        }
        manager.createNotificationChannel(channel)
    }

    companion object {
        const val CHANNEL_ID = "sayda_medication_alarms_v1"
        const val EXTRA_ID = "ir.sayda.yara.family.EXTRA_ID"
        const val EXTRA_TITLE = "ir.sayda.yara.family.EXTRA_TITLE"
        const val EXTRA_DOSAGE = "ir.sayda.yara.family.EXTRA_DOSAGE"
        const val EXTRA_TIME_LABEL = "ir.sayda.yara.family.EXTRA_TIME_LABEL"
    }
}

