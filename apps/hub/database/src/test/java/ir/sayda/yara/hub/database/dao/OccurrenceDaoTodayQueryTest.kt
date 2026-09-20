package ir.sayda.yara.hub.database.dao

import android.content.Context
import androidx.room.Room
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import ir.sayda.yara.hub.database.HubDatabase
import ir.sayda.yara.hub.database.entity.OccurrenceEntity
import ir.sayda.yara.hub.database.entity.ScheduleDefinitionEntity
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import java.util.Calendar
import java.util.TimeZone

@RunWith(AndroidJUnit4::class)
class OccurrenceDaoTodayQueryTest {

    private lateinit var database: HubDatabase
    private lateinit var occurrenceDao: OccurrenceDao
    private lateinit var scheduleDao: ScheduleDefinitionDao

    @Before
    fun setup() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        database = Room.inMemoryDatabaseBuilder(context, HubDatabase::class.java)
            .allowMainThreadQueries()
            .build()
        occurrenceDao = database.occurrenceDao()
        scheduleDao = database.scheduleDefinitionDao()

        // Insert parent schedule definitions to satisfy foreign keys / valid entities
        runBlocking {
            scheduleDao.upsert(
                ScheduleDefinitionEntity(
                    id = "sched-1",
                    ownerReference = "act-1",
                    recurrenceDefinitionJson = "{}",
                    timezone = "Asia/Tehran",
                    startAtEpochMillis = 0L,
                    endAtEpochMillis = null,
                    status = "ACTIVE",
                    updatedAtEpochMillis = 1000L,
                )
            )
        }
    }

    @After
    fun teardown() {
        database.close()
    }

    @Test
    fun observeTodayReminders_correctlyFiltersWithinStartAndEndOfDay_andPreservesHistory() = runBlocking {
        // Setup local calendar day boundary using Asia/Tehran
        val tz = TimeZone.getTimeZone("Asia/Tehran")
        val calendar = Calendar.getInstance(tz).apply {
            set(Calendar.HOUR_OF_DAY, 0)
            set(Calendar.MINUTE, 0)
            set(Calendar.SECOND, 0)
            set(Calendar.MILLISECOND, 0)
        }
        val startOfDayEpochMillis = calendar.timeInMillis

        calendar.set(Calendar.HOUR_OF_DAY, 23)
        calendar.set(Calendar.MINUTE, 59)
        calendar.set(Calendar.SECOND, 59)
        calendar.set(Calendar.MILLISECOND, 999)
        val endOfDayEpochMillis = calendar.timeInMillis

        // 1. Occurrence before today's start (yesterday 23:59:59)
        val beforeTodayDue = OccurrenceEntity(
            id = "occ-before-due",
            scheduleDefinitionId = "sched-1",
            scheduledForEpochMillis = startOfDayEpochMillis - 1000,
            status = "DUE",
            updatedAtEpochMillis = startOfDayEpochMillis - 1000,
        )
        val beforeTodayScheduled = OccurrenceEntity(
            id = "occ-before-sched",
            scheduleDefinitionId = "sched-1",
            scheduledForEpochMillis = startOfDayEpochMillis - 5000,
            status = "SCHEDULED",
            updatedAtEpochMillis = startOfDayEpochMillis - 5000,
        )

        // 2. Occurrence exactly at today's start (00:00:00.000)
        val atStartOfToday = OccurrenceEntity(
            id = "occ-start",
            scheduleDefinitionId = "sched-1",
            scheduledForEpochMillis = startOfDayEpochMillis,
            status = "SCHEDULED",
            updatedAtEpochMillis = startOfDayEpochMillis,
        )

        // 3. Occurrence during today (12:00:00)
        val duringTodayDue = OccurrenceEntity(
            id = "occ-during-due",
            scheduleDefinitionId = "sched-1",
            scheduledForEpochMillis = startOfDayEpochMillis + (12 * 3600 * 1000),
            status = "DUE",
            updatedAtEpochMillis = startOfDayEpochMillis,
        )

        // 4. Occurrence exactly at today's end (23:59:59.999)
        val atEndOfToday = OccurrenceEntity(
            id = "occ-end",
            scheduleDefinitionId = "sched-1",
            scheduledForEpochMillis = endOfDayEpochMillis,
            status = "SCHEDULED",
            updatedAtEpochMillis = endOfDayEpochMillis,
        )

        // 5. Occurrence after today's end (tomorrow 00:00:01)
        val afterToday = OccurrenceEntity(
            id = "occ-after",
            scheduleDefinitionId = "sched-1",
            scheduledForEpochMillis = endOfDayEpochMillis + 1001,
            status = "SCHEDULED",
            updatedAtEpochMillis = endOfDayEpochMillis + 1001,
        )

        // Insert all occurrences into Room
        listOf(beforeTodayDue, beforeTodayScheduled, atStartOfToday, duringTodayDue, atEndOfToday, afterToday).forEach {
            occurrenceDao.upsert(it)
        }

        // Execute today's reminder query
        val todayResults = occurrenceDao.observeTodayReminders(startOfDayEpochMillis, endOfDayEpochMillis).first()
        val todayIds = todayResults.map { it.id }.toSet()

        // 1. Before today's start -> excluded
        assertTrue("Occurrences before today must be excluded", !todayIds.contains("occ-before-due"))
        assertTrue("Occurrences before today must be excluded", !todayIds.contains("occ-before-sched"))

        // 2. Exactly at today's start -> included
        assertTrue("Occurrence at exact start of today must be included", todayIds.contains("occ-start"))

        // 3. During today -> included
        assertTrue("Occurrence during today must be included", todayIds.contains("occ-during-due"))

        // 4. Exactly at today's end -> included
        assertTrue("Occurrence at exact end of today must be included", todayIds.contains("occ-end"))

        // 5. After today's end -> excluded
        assertTrue("Occurrence after today must be excluded", !todayIds.contains("occ-after"))

        assertEquals("Exactly 3 occurrences should be returned for today", 3, todayResults.size)

        // 6 & 7. Verify that old historical occurrences are still intact and preserved in Room
        val retrievedBeforeDue = occurrenceDao.getById("occ-before-due")
        assertNotNull("Historical DUE occurrence before today must remain stored in database", retrievedBeforeDue)
        assertEquals("DUE", retrievedBeforeDue?.status)

        val retrievedBeforeSched = occurrenceDao.getById("occ-before-sched")
        assertNotNull("Historical SCHEDULED occurrence before today must remain stored in database", retrievedBeforeSched)
        assertEquals("SCHEDULED", retrievedBeforeSched?.status)

        val allInDb = occurrenceDao.observeAll().first()
        assertEquals("All 6 occurrences must remain intact in Room without deletion", 6, allInDb.size)
    }
}
