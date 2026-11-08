package ir.sayda.yara.family.alarm

import android.app.AlarmManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build
import com.facebook.react.bridge.Promise
import com.facebook.react.bridge.ReactApplicationContext
import com.facebook.react.bridge.ReactContextBaseJavaModule
import com.facebook.react.bridge.ReactMethod

class MedicationAlarmModule(reactContext: ReactApplicationContext) :
    ReactContextBaseJavaModule(reactContext) {

    override fun getName(): String = "MedicationAlarmModule"

    @ReactMethod
    fun scheduleAlarm(
        id: String,
        title: String,
        dosage: String,
        timeLabel: String,
        timestampMs: Double,
        promise: Promise,
    ) {
        val targetEpoch = timestampMs.toLong()
        if (targetEpoch <= System.currentTimeMillis()) {
            promise.resolve(false)
            return
        }

        val alarmManager = reactApplicationContext.getSystemService(Context.ALARM_SERVICE) as? AlarmManager
        if (alarmManager == null) {
            promise.reject("E_ALARM_SERVICE", "AlarmManager is not available on this device")
            return
        }

        val intent = Intent(reactApplicationContext, MedicationAlarmReceiver::class.java).apply {
            putExtra(MedicationAlarmReceiver.EXTRA_ID, id)
            putExtra(MedicationAlarmReceiver.EXTRA_TITLE, title)
            putExtra(MedicationAlarmReceiver.EXTRA_DOSAGE, dosage)
            putExtra(MedicationAlarmReceiver.EXTRA_TIME_LABEL, timeLabel)
        }

        val pendingIntent = PendingIntent.getBroadcast(
            reactApplicationContext,
            id.hashCode(),
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )

        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                alarmManager.setExactAndAllowWhileIdle(
                    AlarmManager.RTC_WAKEUP,
                    targetEpoch,
                    pendingIntent,
                )
            } else {
                alarmManager.setExact(
                    AlarmManager.RTC_WAKEUP,
                    targetEpoch,
                    pendingIntent,
                )
            }
            promise.resolve(true)
        } catch (e: Exception) {
            promise.reject("E_SCHEDULE_FAILED", e.message, e)
        }
    }

    @ReactMethod
    fun cancelAlarm(id: String, promise: Promise) {
        val alarmManager = reactApplicationContext.getSystemService(Context.ALARM_SERVICE) as? AlarmManager
        val intent = Intent(reactApplicationContext, MedicationAlarmReceiver::class.java)
        val pendingIntent = PendingIntent.getBroadcast(
            reactApplicationContext,
            id.hashCode(),
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
        alarmManager?.cancel(pendingIntent)
        promise.resolve(true)
    }

    @ReactMethod
    fun canScheduleExactAlarms(promise: Promise) {
        val alarmManager = reactApplicationContext.getSystemService(Context.ALARM_SERVICE) as? AlarmManager
        val canSchedule = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            alarmManager?.canScheduleExactAlarms() ?: false
        } else {
            true
        }
        promise.resolve(canSchedule)
    }
}

