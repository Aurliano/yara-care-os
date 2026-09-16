package ir.sayda.yara.hub.ui.presentation

import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

fun formatEpochForDisplay(epochMillis: Long?): String {
    if (epochMillis == null) return "—"
    val formatter = SimpleDateFormat("yyyy/MM/dd HH:mm", Locale("fa", "IR"))
    return formatter.format(Date(epochMillis))
}

fun formatPersianDayAndMonth(date: Date = Date()): String {
    return try {
        val ulocale = android.icu.util.ULocale("fa_IR@calendar=persian")
        val formatter = android.icu.text.SimpleDateFormat("EEEE d MMMM", ulocale)
        formatter.format(date)
    } catch (_: Throwable) {
        val formatter = SimpleDateFormat("EEEE d MMMM", Locale("fa", "IR"))
        formatter.format(date)
    }
}

fun formatPersianYear(date: Date = Date()): String {
    return try {
        val ulocale = android.icu.util.ULocale("fa_IR@calendar=persian")
        val formatter = android.icu.text.SimpleDateFormat("yyyy", ulocale)
        formatter.format(date)
    } catch (_: Throwable) {
        val formatter = SimpleDateFormat("yyyy", Locale("fa", "IR"))
        formatter.format(date)
    }
}
