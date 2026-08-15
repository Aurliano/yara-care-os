package ir.sayda.yara.hub.data.repository

import ir.sayda.yara.hub.core.domain.model.Occurrence
import ir.sayda.yara.hub.core.domain.model.ScheduleDefinition
import ir.sayda.yara.hub.core.domain.repository.SchedulingReplicaRepository
import ir.sayda.yara.hub.database.HubDatabase
import ir.sayda.yara.hub.database.mapper.toDomain
import ir.sayda.yara.hub.database.mapper.toEntity
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class SchedulingReplicaRepositoryImpl @Inject constructor(
    database: HubDatabase,
) : SchedulingReplicaRepository {
    private val scheduleDao = database.scheduleDefinitionDao()
    private val occurrenceDao = database.occurrenceDao()

    override fun observeScheduleDefinitions(): Flow<List<ScheduleDefinition>> =
        scheduleDao.observeAll().map { list -> list.map { it.toDomain() } }

    override fun observeOccurrences(): Flow<List<Occurrence>> =
        occurrenceDao.observeAll().map { list -> list.map { it.toDomain() } }

    override fun observeOccurrencesDueBefore(epochMillis: Long): Flow<List<Occurrence>> =
        occurrenceDao.observeDueBefore(epochMillis).map { list -> list.map { it.toDomain() } }

    override fun observeTodayReminders(endOfDayEpochMillis: Long): Flow<List<Occurrence>> =
        occurrenceDao.observeTodayReminders(endOfDayEpochMillis).map { list -> list.map { it.toDomain() } }

    override suspend fun getOccurrence(occurrenceId: String): Occurrence? =
        occurrenceDao.getById(occurrenceId)?.toDomain()

    override suspend fun upsertScheduleDefinition(schedule: ScheduleDefinition) {
        scheduleDao.upsert(schedule.toEntity())
    }

    override suspend fun upsertOccurrence(occurrence: Occurrence) {
        occurrenceDao.upsert(occurrence.toEntity())
    }

    override suspend fun getOccurrencesDueBefore(epochMillis: Long): List<Occurrence> =
        occurrenceDao.getDueBefore(epochMillis).map { it.toDomain() }

    override suspend fun getScheduledOccurrencesDueBefore(epochMillis: Long): List<Occurrence> =
        occurrenceDao.getScheduledDueBefore(epochMillis).map { it.toDomain() }

    override suspend fun getScheduledOccurrencesAfter(epochMillis: Long): List<Occurrence> =
        occurrenceDao.getScheduledAfter(epochMillis).map { it.toDomain() }

    override suspend fun replaceOccurrencesForSchedule(
        scheduleDefinitionId: String,
        occurrences: List<Occurrence>,
    ) {
        occurrenceDao.deleteByScheduleDefinitionId(scheduleDefinitionId)
        occurrences.forEach { occurrenceDao.upsert(it.toEntity()) }
    }

    override fun observeNextScheduledOccurrence(afterEpochMillis: Long): Flow<Occurrence?> =
        occurrenceDao.observeNextScheduledAfter(afterEpochMillis).map { entity -> entity?.toDomain() }

    override fun observeNextReminderOccurrence(
        nowEpochMillis: Long,
        endOfDayEpochMillis: Long,
    ): Flow<Occurrence?> =
        occurrenceDao.observeNextReminderOccurrence(nowEpochMillis, endOfDayEpochMillis)
            .map { entity -> entity?.toDomain() }
}
