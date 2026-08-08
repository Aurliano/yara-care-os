package ir.sayda.yara.hub.ui.presentation

import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

fun formatEpochForDisplay(epochMillis: Long?): String {
    if (epochMillis == null) return "—"
    val formatter = SimpleDateFormat("yyyy/MM/dd HH:mm", Locale("fa", "IR"))
    return formatter.format(Date(epochMillis))
}
