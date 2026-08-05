package ir.sayda.yara.hub.data.repository

import ir.sayda.yara.hub.core.domain.model.CareActivity
import ir.sayda.yara.hub.core.domain.model.Prescription
import ir.sayda.yara.hub.core.domain.repository.CareReplicaRepository
import ir.sayda.yara.hub.database.HubDatabase
import ir.sayda.yara.hub.database.mapper.toDomain
import ir.sayda.yara.hub.database.mapper.toEntity
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class CareReplicaRepositoryImpl @Inject constructor(
    database: HubDatabase,
) : CareReplicaRepository {
    private val careActivityDao = database.careActivityDao()
    private val prescriptionDao = database.prescriptionDao()

    override fun observeActiveCareActivities(elderId: String): Flow<List<CareActivity>> =
        careActivityDao.observeActiveByElder(elderId).map { entities -> entities.map { it.toDomain() } }

    override fun observeAllCareActivities(): Flow<List<CareActivity>> =
        careActivityDao.observeAll().map { entities -> entities.map { it.toDomain() } }

    override suspend fun getCareActivityByScheduleDefinition(scheduleDefinitionId: String): CareActivity? =
        careActivityDao.getByScheduleDefinitionId(scheduleDefinitionId)?.toDomain()

    override suspend fun upsertCareActivity(activity: CareActivity) {
        careActivityDao.upsert(activity.toEntity())
    }

    override fun observePrescriptions(): Flow<List<Prescription>> =
        prescriptionDao.observeAll().map { entities -> entities.map { it.toDomain() } }

    override suspend fun getPrescription(careActivityId: String): Prescription? =
        prescriptionDao.getByCareActivityId(careActivityId)?.toDomain()

    override suspend fun upsertPrescription(prescription: Prescription) {
        prescriptionDao.upsert(prescription.toEntity())
    }
}
