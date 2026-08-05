package ir.sayda.yara.hub.database.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
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
import ir.sayda.yara.hub.database.entity.SyncSessionLocalEntity
import ir.sayda.yara.hub.database.entity.WorkflowDefinitionEntity
import ir.sayda.yara.hub.database.entity.WorkflowExecutionEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface CareActivityDao {
    @Query("SELECT * FROM care_activity WHERE elder_id = :elderId AND status = 'ACTIVE' ORDER BY display_title")
    fun observeActiveByElder(elderId: String): Flow<List<CareActivityEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(entity: CareActivityEntity)
}

@Dao
interface PrescriptionDao {
    @Query("SELECT * FROM prescription WHERE care_activity_id = :careActivityId LIMIT 1")
    suspend fun getByCareActivityId(careActivityId: String): PrescriptionEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(entity: PrescriptionEntity)
}

@Dao
interface WorkflowDefinitionDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(entity: WorkflowDefinitionEntity)
}

@Dao
interface WorkflowExecutionDao {
    @Query("SELECT * FROM workflow_execution WHERE status IN ('PENDING', 'ACTIVE') ORDER BY started_at_epoch_millis")
    fun observeActive(): Flow<List<WorkflowExecutionEntity>>

    @Query("SELECT * FROM workflow_execution WHERE id = :executionId LIMIT 1")
    suspend fun getById(executionId: String): WorkflowExecutionEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(entity: WorkflowExecutionEntity)
}

@Dao
interface ScheduleDefinitionDao {
    @Query("SELECT * FROM schedule_definition ORDER BY owner_reference")
    fun observeAll(): Flow<List<ScheduleDefinitionEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(entity: ScheduleDefinitionEntity)
}

@Dao
interface OccurrenceDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(entity: OccurrenceEntity)

    @Query(
        """
        SELECT * FROM occurrence
        WHERE status = 'DUE' AND scheduled_for_epoch_millis <= :epochMillis
        ORDER BY scheduled_for_epoch_millis
        """,
    )
    suspend fun getDueBefore(epochMillis: Long): List<OccurrenceEntity>
}

@Dao
interface DeviceDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(entity: DeviceEntity)
}

@Dao
interface DeviceCommandDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(entity: DeviceCommandEntity)

    @Query("SELECT * FROM device_command WHERE status = 'QUEUED' ORDER BY expires_at_epoch_millis")
    suspend fun getQueued(): List<DeviceCommandEntity>
}

@Dao
interface ContactDao {
    @Query(
        """
        SELECT * FROM contact
        WHERE elder_id = :elderId AND status = 'ACTIVE' AND is_priority = 1
        ORDER BY display_name
        """,
    )
    fun observePriorityByElder(elderId: String): Flow<List<ContactEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(entity: ContactEntity)
}

@Dao
interface CommunicationSessionDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(entity: CommunicationSessionEntity)
}

@Dao
interface ReplicaStateDao {
    @Query("SELECT * FROM replica_state LIMIT 1")
    fun observe(): Flow<ReplicaStateEntity?>

    @Query("SELECT * FROM replica_state LIMIT 1")
    suspend fun get(): ReplicaStateEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(entity: ReplicaStateEntity)
}

@Dao
interface PendingEvidenceDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(entity: PendingEvidenceEntity)

    @Query("SELECT * FROM pending_evidence WHERE id = :id LIMIT 1")
    suspend fun getById(id: String): PendingEvidenceEntity?

    @Query("SELECT * FROM pending_evidence WHERE status = 'PENDING' ORDER BY created_at_epoch_millis LIMIT :limit")
    suspend fun getPending(limit: Int): List<PendingEvidenceEntity>

    @Query(
        """
        UPDATE pending_evidence
        SET status = :status,
            last_attempt_at_epoch_millis = :attemptAt,
            updated_at_epoch_millis = :updatedAt,
            retry_count = :retryCount,
            last_error = :lastError
        WHERE id = :id
        """,
    )
    suspend fun updateStatus(
        id: String,
        status: String,
        attemptAt: Long?,
        updatedAt: Long,
        retryCount: Int,
        lastError: String?,
    )
}

@Dao
interface OutboxDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(entity: OutboxEntryEntity)

    @Query(
        """
        SELECT * FROM outbox_entry
        WHERE status = 'PENDING'
        ORDER BY priority DESC, created_at_epoch_millis ASC
        LIMIT :limit
        """,
    )
    suspend fun getPending(limit: Int): List<OutboxEntryEntity>

    @Query("SELECT * FROM outbox_entry WHERE id = :id LIMIT 1")
    suspend fun getById(id: String): OutboxEntryEntity?

    @Query(
        """
        UPDATE outbox_entry
        SET status = :status,
            last_attempt_at_epoch_millis = :attemptAt,
            updated_at_epoch_millis = :updatedAt,
            retry_count = :retryCount,
            last_error = :lastError
        WHERE id = :id
        """,
    )
    suspend fun updateStatus(
        id: String,
        status: String,
        attemptAt: Long?,
        updatedAt: Long,
        retryCount: Int,
        lastError: String?,
    )
}

@Dao
interface RuntimeStateDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(entity: RuntimeStateEntity)

    @Query("SELECT * FROM runtime_state WHERE component_id = :componentId LIMIT 1")
    suspend fun get(componentId: String): RuntimeStateEntity?

    @Query("SELECT * FROM runtime_state")
    suspend fun getAll(): List<RuntimeStateEntity>
}

@Dao
interface SyncSessionLocalDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(entity: SyncSessionLocalEntity)
}
