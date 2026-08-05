package ir.sayda.yara.hub.data.repository

import androidx.room.withTransaction
import ir.sayda.yara.hub.core.domain.model.SyncSession
import ir.sayda.yara.hub.core.domain.repository.ReplicaSnapshotWriter
import ir.sayda.yara.hub.core.domain.repository.ReplicaSnapshotBundle
import ir.sayda.yara.hub.core.domain.repository.SyncConflictRepository
import ir.sayda.yara.hub.core.domain.repository.SyncSessionLocalRepository
import ir.sayda.yara.hub.core.sync.SyncConflictRecord
import ir.sayda.yara.hub.database.HubDatabase
import ir.sayda.yara.hub.database.mapper.toDomain
import ir.sayda.yara.hub.database.mapper.toEntity
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class SyncSessionLocalRepositoryImpl @Inject constructor(
    database: HubDatabase,
) : SyncSessionLocalRepository {
    private val dao = database.syncSessionLocalDao()

    override suspend fun save(session: SyncSession) {
        dao.upsert(session.toEntity())
    }

    override suspend fun getActive(): SyncSession? = dao.getActive()?.toDomain()

    override suspend fun getById(sessionId: String): SyncSession? = dao.getById(sessionId)?.toDomain()

    override suspend fun updateStatus(sessionId: String, status: String) {
        dao.updateStatus(sessionId, status)
    }

    override suspend fun clear(sessionId: String) {
        dao.delete(sessionId)
    }
}

@Singleton
class SyncConflictRepositoryImpl @Inject constructor(
    database: HubDatabase,
) : SyncConflictRepository {
    private val dao = database.syncConflictDao()

    override suspend fun record(conflict: SyncConflictRecord) {
        dao.insert(conflict.toEntity())
    }

    override suspend fun listOpen(): List<SyncConflictRecord> =
        dao.getAll().map { it.toDomain() }
}

@Singleton
class ReplicaSnapshotWriterImpl @Inject constructor(
    private val database: HubDatabase,
) : ReplicaSnapshotWriter {

    override suspend fun replaceReplicaTables(bundle: ReplicaSnapshotBundle) {
        database.withTransaction {
            database.careActivityDao().deleteAll()
            database.prescriptionDao().deleteAll()
            database.workflowDefinitionDao().deleteAll()
            database.workflowExecutionDao().deleteAll()
            database.scheduleDefinitionDao().deleteAll()
            database.occurrenceDao().deleteAll()
            database.deviceDao().deleteAll()
            database.deviceCommandDao().deleteAll()
            database.communicationSessionDao().deleteAll()
            database.contactDao().deleteAll()

            bundle.careActivities.forEach { database.careActivityDao().upsert(it.toEntity()) }
            bundle.prescriptions.forEach { database.prescriptionDao().upsert(it.toEntity()) }
            bundle.workflowDefinitions.forEach { database.workflowDefinitionDao().upsert(it.toEntity()) }
            bundle.workflowExecutions.forEach { database.workflowExecutionDao().upsert(it.toEntity()) }
            bundle.scheduleDefinitions.forEach { database.scheduleDefinitionDao().upsert(it.toEntity()) }
            bundle.occurrences.forEach { database.occurrenceDao().upsert(it.toEntity()) }
            bundle.devices.forEach { database.deviceDao().upsert(it.toEntity()) }
            bundle.deviceCommands.forEach { database.deviceCommandDao().upsert(it.toEntity()) }
            bundle.communicationSessions.forEach { database.communicationSessionDao().upsert(it.toEntity()) }
            bundle.contacts.forEach { database.contactDao().upsert(it.toEntity()) }
        }
    }
}
