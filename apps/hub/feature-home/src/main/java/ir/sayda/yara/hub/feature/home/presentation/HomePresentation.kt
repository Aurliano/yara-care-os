package ir.sayda.yara.hub.feature.home.presentation

import ir.sayda.yara.hub.core.domain.model.HomeRuntimeSnapshot
import ir.sayda.yara.hub.core.domain.model.ProvisioningState
import ir.sayda.yara.hub.core.domain.model.TodayReminderItem
import ir.sayda.yara.hub.ui.presentation.ConnectionVisualState
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

data class ConnectionPresentation(
    val state: ConnectionVisualState,
    val title: String,
    val subtitle: String,
)

data class NextReminderPresentation(
    val title: String,
    val subtitle: String,
    val description: String?,
    val scheduledTime: String?,
)

fun HomeRuntimeSnapshot.toConnectionPresentation(): ConnectionPresentation {
    when (provisioningState) {
        ProvisioningState.UNPROVISIONED -> return ConnectionPresentation(
            state = ConnectionVisualState.Provisioning,
            title = "در حال راه‌اندازی دستگاه",
            subtitle = "لطفاً چند لحظه صبر کنید",
        )
        ProvisioningState.REGISTERING -> return ConnectionPresentation(
            state = ConnectionVisualState.Provisioning,
            title = "در حال ثبت دستگاه",
            subtitle = "در حال ثبت دستگاه",
        )
        ProvisioningState.AUTHENTICATING -> return ConnectionPresentation(
            state = ConnectionVisualState.Provisioning,
            title = "در حال اتصال",
            subtitle = "در حال اتصال",
        )
        ProvisioningState.READY -> return ConnectionPresentation(
            state = ConnectionVisualState.Connected,
            title = "دستگاه آماده است",
            subtitle = "دستگاه آماده است",
        )
        ProvisioningState.ERROR -> return ConnectionPresentation(
            state = ConnectionVisualState.Offline,
            title = "راه‌اندازی ناموفق بود",
            subtitle = "راه‌اندازی ناموفق بود",
        )
        ProvisioningState.REGISTERED -> return ConnectionPresentation(
            state = ConnectionVisualState.Provisioning,
            title = "ورود مراقب",
            subtitle = "با همان حساب اپ مراقب وارد شوید",
        )
    }

    return when {
        !isOnline -> ConnectionPresentation(
            state = ConnectionVisualState.Offline,
            title = "بدون اینترنت",
            subtitle = "اتصال اینترنت برقرار نیست",
        )
        pendingEvidenceCount > 0 -> ConnectionPresentation(
            state = ConnectionVisualState.Waiting,
            title = "در حال ارسال",
            subtitle = "در حال همگام‌سازی...",
        )
        !synchronizationAvailable -> ConnectionPresentation(
            state = ConnectionVisualState.Waiting,
            title = "در انتظار اتصال",
            subtitle = "در انتظار اتصال",
        )
        else -> ConnectionPresentation(
            state = ConnectionVisualState.Connected,
            title = "متصل",
            subtitle = "همه چیز آماده است",
        )
    }
}

fun HomeRuntimeSnapshot.toNextReminderPresentation(
    timeFormatter: SimpleDateFormat,
): NextReminderPresentation {
    val soonestToday = todayReminders.minByOrNull { it.scheduledForEpochMillis }
    if (soonestToday != null) {
        return soonestToday.toPresentation(timeFormatter)
    }
    val nextMillis = nextReminderEpochMillis
    if (nextMillis != null) {
        return NextReminderPresentation(
            title = nextReminderTitle ?: "یادآور بعدی",
            subtitle = timeFormatter.format(Date(nextMillis)),
            description = null,
            scheduledTime = timeFormatter.format(Date(nextMillis)),
        )
    }
    return NextReminderPresentation(
        title = "یادآوری فعالی وجود ندارد",
        subtitle = "امروز یادآوری ندارید 🌿",
        description = null,
        scheduledTime = null,
    )
}

fun HomeRuntimeSnapshot.todayRemindersSectionTitle(): String? =
    if (todayReminders.size > 1) "یادآورهای دیگر امروز" else null

fun HomeRuntimeSnapshot.needsCaregiverLogin(): Boolean {
    if (deviceId.isNullOrBlank()) return false
    return provisioningState == ProvisioningState.REGISTERED ||
        provisioningState == ProvisioningState.AUTHENTICATING ||
        provisioningState == ProvisioningState.ERROR
}

fun HomeRuntimeSnapshot.emptyMedicationMessage(): String? = when {
    provisioningState != ProvisioningState.READY -> null
    todayReminders.isNotEmpty() -> null
    nextReminderEpochMillis != null -> null
    !isOnline -> null
    replicaHealth.equals("UNKNOWN", ignoreCase = true) -> null
    else -> "برنامه دارویی هنوز دریافت نشده است."
}

fun HomeRuntimeSnapshot.showFamilyMessagesPlaceholder(): Boolean =
    priorityContacts.isEmpty()

fun TodayReminderItem.toPresentation(
    timeFormatter: SimpleDateFormat,
): NextReminderPresentation {
    val description = if (localConfirmationRecorded) {
        "ثبت شد ✓"
    } else {
        friendlyDescription
    }
    return NextReminderPresentation(
        title = title,
        subtitle = timeFormatter.format(Date(scheduledForEpochMillis)),
        description = description,
        scheduledTime = timeFormatter.format(Date(scheduledForEpochMillis)),
    )
}

fun formatEpochForDisplay(epochMillis: Long?): String =
    ir.sayda.yara.hub.ui.presentation.formatEpochForDisplay(epochMillis)
