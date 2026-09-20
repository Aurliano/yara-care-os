package ir.sayda.yara.hub.core.scheduling

import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.SimpleTimeZone
import java.util.TimeZone

/**
 * Iran permanently abolished Daylight Saving Time (DST) starting autumn 2022 (1401-06-31).
 * Epoch millis for 2022-09-22 00:00:00 UTC = 1663804800000L.
 */
const val IRAN_DST_ABOLITION_EPOCH_MILLIS: Long = 1_663_804_800_000L

/**
 * Resolves a TimeZone safely across legacy and modern Android devices.
 *
 * Devices running Android <= 9 (such as Samsung Galaxy Tab S2 on Android 7.0) have outdated
 * system tzdata (e.g. tzdata2017b) that incorrectly applies +04:30 DST to Asia/Tehran during summer.
 * For dates on or after September 22, 2022 in Asia/Tehran, this returns a fixed UTC+03:30 TimeZone
 * without DST, aligning with Iranian law and modern backend tzdata.
 */
fun resolveSchedulingTimeZone(
    timezoneName: String? = null,
    epochMillis: Long = System.currentTimeMillis(),
): TimeZone {
    val targetZone = timezoneName ?: TimeZone.getDefault().id
    if (targetZone.equals("Asia/Tehran", ignoreCase = true) && epochMillis >= IRAN_DST_ABOLITION_EPOCH_MILLIS) {
        return SimpleTimeZone(12_600_000, "Asia/Tehran")
    }
    return if (timezoneName != null) TimeZone.getTimeZone(timezoneName) else TimeZone.getDefault()
}

/**
 * Formats an instant in canonical UTC ISO-8601 with trailing "+00:00".
 * Matches Python's datetime.isoformat() exactly to guarantee 100% deterministic UUIDv5
 * occurrence identities across Backend and Android Hub.
 */
fun formatCanonicalUtcIso(epochMillis: Long): String {
    val formatter = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.US).apply {
        timeZone = TimeZone.getTimeZone("UTC")
    }
    return formatter.format(Date(epochMillis)) + "+00:00"
}
