package ir.sayda.yara.hub.runtime.scheduling

import ir.sayda.yara.hub.runtime.json.HubJsonReader
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.jsonPrimitive
import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Date
import java.util.Locale
import java.util.TimeZone

data class RecurrenceSlot(
    val originalTimeEpochMillis: Long,
    val originalTimeIsoUtc: String,
)

object RecurrenceEvaluator {

    private val ISO_FORMATTER = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ssXXX", Locale.US).apply {
        timeZone = TimeZone.getTimeZone("UTC")
    }

    fun validateRecurrenceDefinition(recurrenceDefinitionJson: String) {
        val json = HubJsonReader.parseObject(recurrenceDefinitionJson)
        val type = json["type"]?.jsonPrimitive?.content ?: error("Missing type.")
        require(type in setOf("once", "daily", "weekly", "interval")) {
            "type must be one of: once, daily, weekly, interval."
        }
        when (type) {
            "daily", "weekly" -> parseLocalTime(json["time"]?.jsonPrimitive?.content ?: error("Missing time."))
            "weekly" -> require(json.containsKey("days")) { "weekly recurrence requires days." }
            "interval" -> {
                val unit = json["unit"]?.jsonPrimitive?.content ?: error("Missing unit.")
                require(unit in setOf("hours", "days")) { "interval requires unit hours or days." }
                require(HubJsonReader.intField(json, "every") > 0) { "interval requires positive every." }
            }
        }
    }

    fun iterRecurrenceSlots(
        recurrenceDefinitionJson: String,
        timezoneName: String,
        startAtEpochMillis: Long,
        endAtEpochMillis: Long?,
        rangeStartEpochMillis: Long,
        rangeEndEpochMillis: Long,
    ): List<RecurrenceSlot> {
        val json = HubJsonReader.parseObject(recurrenceDefinitionJson)
        validateRecurrenceDefinition(recurrenceDefinitionJson)
        val zone = TimeZone.getTimeZone(timezoneName)
        val effectiveStart = maxOf(startAtEpochMillis, rangeStartEpochMillis)
        val effectiveEnd = minOf(rangeEndEpochMillis, endAtEpochMillis ?: rangeEndEpochMillis)
        if (effectiveStart > effectiveEnd) return emptyList()

        return when (json["type"]!!.jsonPrimitive.content) {
            "once" -> {
                if (startAtEpochMillis in effectiveStart..effectiveEnd) {
                    listOf(toSlot(startAtEpochMillis))
                } else {
                    emptyList()
                }
            }
            "interval" -> iterIntervalSlots(json, startAtEpochMillis, effectiveStart, effectiveEnd)
            else -> iterDailyOrWeeklySlots(json, zone, startAtEpochMillis, effectiveStart, effectiveEnd)
        }
    }

    private fun iterDailyOrWeeklySlots(
        json: JsonObject,
        zone: TimeZone,
        startAtEpochMillis: Long,
        effectiveStart: Long,
        effectiveEnd: Long,
    ): List<RecurrenceSlot> {
        val type = json["type"]!!.jsonPrimitive.content
        val (hour, minute) = parseLocalTime(json["time"]!!.jsonPrimitive.content)
        val calendar = Calendar.getInstance(zone).apply { timeInMillis = startAtEpochMillis }
        val startDay = truncateToDay(calendar)
        val rangeStartDay = Calendar.getInstance(zone).apply { timeInMillis = effectiveStart }
        val rangeEndDay = Calendar.getInstance(zone).apply { timeInMillis = effectiveEnd }
        var currentDay = maxOf(startDay, truncateToDay(rangeStartDay))
        val endDay = truncateToDay(rangeEndDay)
        val slots = mutableListOf<RecurrenceSlot>()
        while (!currentDay.after(endDay)) {
            val includeDay = when (type) {
                "daily" -> !currentDay.before(startDay)
                else -> {
                    val dayCode = arrayOf("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN")[dayOfWeekIndex(currentDay)]
                    HubJsonReader.stringArray(json, "days").contains(dayCode) && !currentDay.before(startDay)
                }
            }
            if (includeDay) {
                val slotCalendar = currentDay.clone() as Calendar
                slotCalendar.set(Calendar.HOUR_OF_DAY, hour)
                slotCalendar.set(Calendar.MINUTE, minute)
                slotCalendar.set(Calendar.SECOND, 0)
                slotCalendar.set(Calendar.MILLISECOND, 0)
                val slotMillis = slotCalendar.timeInMillis
                if (slotMillis in effectiveStart..effectiveEnd) {
                    slots += toSlot(slotMillis)
                }
            }
            currentDay.add(Calendar.DAY_OF_YEAR, 1)
        }
        return slots
    }

    private fun iterIntervalSlots(
        json: JsonObject,
        startAtEpochMillis: Long,
        effectiveStart: Long,
        effectiveEnd: Long,
    ): List<RecurrenceSlot> {
        val every = HubJsonReader.intField(json, "every")
        val unit = json["unit"]!!.jsonPrimitive.content
        val stepMillis = if (unit == "hours") every * 60L * 60L * 1000L else every * 24L * 60L * 60L * 1000L
        var current = startAtEpochMillis
        while (current < effectiveStart) {
            current += stepMillis
        }
        val slots = mutableListOf<RecurrenceSlot>()
        while (current <= effectiveEnd) {
            slots += toSlot(current)
            current += stepMillis
        }
        return slots
    }

    private fun parseLocalTime(value: String): Pair<Int, Int> {
        val parts = value.split(":")
        require(parts.size == 2) { "time must use HH:MM format." }
        return parts[0].toInt() to parts[1].toInt()
    }

    private fun toSlot(epochMillis: Long): RecurrenceSlot {
        val seconds = epochMillis - (epochMillis % 1000)
        return RecurrenceSlot(
            originalTimeEpochMillis = seconds,
            originalTimeIsoUtc = ISO_FORMATTER.format(Date(seconds)),
        )
    }

    private fun truncateToDay(calendar: Calendar): Calendar {
        val copy = calendar.clone() as Calendar
        copy.set(Calendar.HOUR_OF_DAY, 0)
        copy.set(Calendar.MINUTE, 0)
        copy.set(Calendar.SECOND, 0)
        copy.set(Calendar.MILLISECOND, 0)
        return copy
    }

    private fun dayOfWeekIndex(calendar: Calendar): Int {
        return when (calendar.get(Calendar.DAY_OF_WEEK)) {
            Calendar.MONDAY -> 0
            Calendar.TUESDAY -> 1
            Calendar.WEDNESDAY -> 2
            Calendar.THURSDAY -> 3
            Calendar.FRIDAY -> 4
            Calendar.SATURDAY -> 5
            else -> 6
        }
    }
}
