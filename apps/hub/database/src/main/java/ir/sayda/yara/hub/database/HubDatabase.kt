package ir.sayda.yara.hub.database

import androidx.room.Database
import androidx.room.RoomDatabase
import ir.sayda.yara.hub.database.dao.CareActivityDao
import ir.sayda.yara.hub.database.dao.CommunicationSessionDao
import ir.sayda.yara.hub.database.dao.ContactDao
import ir.sayda.yara.hub.database.dao.DeviceCommandDao
import ir.sayda.yara.hub.database.dao.DeviceDao
import ir.sayda.yara.hub.database.dao.OccurrenceDao
import ir.sayda.yara.hub.database.dao.OutboxDao
import ir.sayda.yara.hub.database.dao.PendingEvidenceDao
import ir.sayda.yara.hub.database.dao.PrescriptionDao
import ir.sayda.yara.hub.database.dao.ReplicaStateDao
import ir.sayda.yara.hub.database.dao.RuntimeStateDao
import ir.sayda.yara.hub.database.dao.ScheduleDefinitionDao
import ir.sayda.yara.hub.database.dao.SyncConflictDao
import ir.sayda.yara.hub.database.dao.SyncSessionLocalDao
import ir.sayda.yara.hub.database.dao.WorkflowDefinitionDao
import ir.sayda.yara.hub.database.dao.WorkflowExecutionDao
import ir.sayda.yara.hub.database.entity.CareActivityEntity
import ir.sayda.yara.hub.database.entity.CommunicationSessionEntity
import ir.sayda.yara.hub.database.entity.ContactEntity
import ir.sayda.yara.hub.database.entity.DeviceCommandEntity
import ir.sayda.yara.hub.database.entity.DeviceEntity
import ir.sayda.yara.hub.database.entity.OccurrenceEntity
import ir.sayda.yara.hub.database.entity.OutboxEntryEntity
import ir.sayda.yara.hub.database.entity.PendingEvidenceEntity
import ir.sayda.yara.hub.database.entity.PrescriptionEntity
import ir.sayda.yara.hub.database.entity.ReplicaStateEntity
import ir.sayda.yara.hub.database.entity.RuntimeStateEntity
import ir.sayda.yara.hub.database.entity.ScheduleDefinitionEntity
import ir.sayda.yara.hub.database.entity.SyncConflictEntity
import ir.sayda.yara.hub.database.entity.SyncSessionLocalEntity
import ir.sayda.yara.hub.database.entity.WorkflowDefinitionEntity
import ir.sayda.yara.hub.database.entity.WorkflowExecutionEntity

@Database(
    entities = [
        CareActivityEntity::class,
        PrescriptionEntity::class,
        WorkflowDefinitionEntity::class,
        WorkflowExecutionEntity::class,
        ScheduleDefinitionEntity::class,
        OccurrenceEntity::class,
        DeviceEntity::class,
        DeviceCommandEntity::class,
        CommunicationSessionEntity::class,
        ContactEntity::class,
        ReplicaStateEntity::class,
        PendingEvidenceEntity::class,
        OutboxEntryEntity::class,
        RuntimeStateEntity::class,
        SyncSessionLocalEntity::class,
        SyncConflictEntity::class,
    ],
    version = 3,
    exportSchema = true,
    autoMigrations = [],
)
abstract class HubDatabase : RoomDatabase() {
    abstract fun careActivityDao(): CareActivityDao
    abstract fun prescriptionDao(): PrescriptionDao
    abstract fun workflowDefinitionDao(): WorkflowDefinitionDao
    abstract fun workflowExecutionDao(): WorkflowExecutionDao
    abstract fun scheduleDefinitionDao(): ScheduleDefinitionDao
    abstract fun occurrenceDao(): OccurrenceDao
    abstract fun deviceDao(): DeviceDao
    abstract fun deviceCommandDao(): DeviceCommandDao
    abstract fun contactDao(): ContactDao
    abstract fun communicationSessionDao(): CommunicationSessionDao
    abstract fun replicaStateDao(): ReplicaStateDao
    abstract fun pendingEvidenceDao(): PendingEvidenceDao
    abstract fun outboxDao(): OutboxDao
    abstract fun runtimeStateDao(): RuntimeStateDao
    abstract fun syncSessionLocalDao(): SyncSessionLocalDao
    abstract fun syncConflictDao(): SyncConflictDao
}
