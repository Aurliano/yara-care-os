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

    override suspend fun upsertScheduleDefinition(schedule: ScheduleDefinition) {
        scheduleDao.upsert(schedule.toEntity())
    }

    override suspend fun upsertOccurrence(occurrence: Occurrence) {
        occurrenceDao.upsert(occurrence.toEntity())
    }

    override suspend fun getOccurrencesDueBefore(epochMillis: Long): List<Occurrence> =
        occurrenceDao.getDueBefore(epochMillis).map { it.toDomain() }
}
