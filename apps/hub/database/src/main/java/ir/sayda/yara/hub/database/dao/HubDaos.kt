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

    @Query("SELECT * FROM care_activity ORDER BY display_title")
    fun observeAll(): Flow<List<CareActivityEntity>>

    @Query("SELECT * FROM care_activity WHERE schedule_definition_id = :scheduleDefinitionId LIMIT 1")
    suspend fun getByScheduleDefinitionId(scheduleDefinitionId: String): CareActivityEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(entity: CareActivityEntity)

    @Query("DELETE FROM care_activity")
    suspend fun deleteAll()
}

@Dao
interface PrescriptionDao {
    @Query("SELECT * FROM prescription ORDER BY care_activity_id")
    fun observeAll(): Flow<List<PrescriptionEntity>>

    @Query("SELECT * FROM prescription WHERE care_activity_id = :careActivityId LIMIT 1")
    suspend fun getByCareActivityId(careActivityId: String): PrescriptionEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(entity: PrescriptionEntity)

    @Query("DELETE FROM prescription")
    suspend fun deleteAll()
}

@Dao
interface WorkflowDefinitionDao {
    @Query("SELECT * FROM workflow_definition ORDER BY name")
    fun observeAll(): Flow<List<WorkflowDefinitionEntity>>

    @Query("SELECT * FROM workflow_definition WHERE id = :definitionId LIMIT 1")
    suspend fun getById(definitionId: String): WorkflowDefinitionEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(entity: WorkflowDefinitionEntity)

    @Query("DELETE FROM workflow_definition")
    suspend fun deleteAll()
}

@Dao
interface WorkflowExecutionDao {
    @Query("SELECT * FROM workflow_execution WHERE status IN ('PENDING', 'ACTIVE') ORDER BY started_at_epoch_millis")
    fun observeActive(): Flow<List<WorkflowExecutionEntity>>

    @Query("SELECT * FROM workflow_execution WHERE id = :executionId LIMIT 1")
    suspend fun getById(executionId: String): WorkflowExecutionEntity?

    @Query("SELECT * FROM workflow_execution WHERE occurrence_id = :occurrenceId LIMIT 1")
    suspend fun getByOccurrenceId(occurrenceId: String): WorkflowExecutionEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(entity: WorkflowExecutionEntity)

    @Query("DELETE FROM workflow_execution")
    suspend fun deleteAll()
}

@Dao
interface ScheduleDefinitionDao {
    @Query("SELECT * FROM schedule_definition ORDER BY owner_reference")
    fun observeAll(): Flow<List<ScheduleDefinitionEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(entity: ScheduleDefinitionEntity)

    @Query("DELETE FROM schedule_definition")
    suspend fun deleteAll()
}

@Dao
interface OccurrenceDao {
    @Query("SELECT * FROM occurrence ORDER BY scheduled_for_epoch_millis")
    fun observeAll(): Flow<List<OccurrenceEntity>>

    @Query("SELECT * FROM occurrence WHERE id = :occurrenceId LIMIT 1")
    suspend fun getById(occurrenceId: String): OccurrenceEntity?

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

    @Query(
        """
        SELECT * FROM occurrence
        WHERE status = 'DUE' AND scheduled_for_epoch_millis <= :epochMillis
        ORDER BY scheduled_for_epoch_millis
        """,
    )
    fun observeDueBefore(epochMillis: Long): Flow<List<OccurrenceEntity>>

    @Query(
        """
        SELECT * FROM occurrence
        WHERE status = 'SCHEDULED' AND scheduled_for_epoch_millis <= :epochMillis
        ORDER BY scheduled_for_epoch_millis
        """,
    )
    suspend fun getScheduledDueBefore(epochMillis: Long): List<OccurrenceEntity>

    @Query(
        """
        SELECT * FROM occurrence
        WHERE status = 'SCHEDULED' AND scheduled_for_epoch_millis > :epochMillis
        ORDER BY scheduled_for_epoch_millis
        """,
    )
    suspend fun getScheduledAfter(epochMillis: Long): List<OccurrenceEntity>

    @Query(
        """
        SELECT * FROM occurrence
        WHERE status = 'SCHEDULED' AND scheduled_for_epoch_millis > :epochMillis
        ORDER BY scheduled_for_epoch_millis
        LIMIT 1
        """,
    )
    fun observeNextScheduledAfter(epochMillis: Long): Flow<OccurrenceEntity?>

    @Query("DELETE FROM occurrence")
    suspend fun deleteAll()
}

@Dao
interface DeviceDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(entity: DeviceEntity)

    @Query("DELETE FROM device")
    suspend fun deleteAll()
}

@Dao
interface DeviceCommandDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(entity: DeviceCommandEntity)

    @Query("SELECT * FROM device_command WHERE status = 'QUEUED' ORDER BY expires_at_epoch_millis")
    suspend fun getQueued(): List<DeviceCommandEntity>

    @Query("DELETE FROM device_command")
    suspend fun deleteAll()
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

    @Query("DELETE FROM contact")
    suspend fun deleteAll()
}

@Dao
interface CommunicationSessionDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(entity: CommunicationSessionEntity)

    @Query("DELETE FROM communication_session")
    suspend fun deleteAll()
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

    @Query("SELECT * FROM pending_evidence WHERE status = 'IN_FLIGHT' ORDER BY created_at_epoch_millis LIMIT :limit")
    suspend fun getInFlight(limit: Int): List<PendingEvidenceEntity>

    @Query(
        """
        SELECT * FROM pending_evidence
        WHERE workflow_execution_id = :workflowExecutionId
          AND evidence_type = 'HUB_CONFIRMATION'
        ORDER BY created_at_epoch_millis DESC
        LIMIT 1
        """,
    )
    suspend fun getHubConfirmationByExecution(workflowExecutionId: String): PendingEvidenceEntity?

    @Query(
        """
        SELECT * FROM pending_evidence
        WHERE evidence_type = 'HUB_CONFIRMATION'
        ORDER BY created_at_epoch_millis DESC
        """,
    )
    fun observeHubConfirmationEvidence(): kotlinx.coroutines.flow.Flow<List<PendingEvidenceEntity>>

    @Query("SELECT COUNT(*) FROM pending_evidence WHERE status = 'PENDING'")
    fun observePendingCount(): Flow<Int>

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

    @Query("SELECT * FROM runtime_state WHERE component_id = :componentId LIMIT 1")
    fun observe(componentId: String): Flow<RuntimeStateEntity?>
}

@Dao
interface SyncSessionLocalDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(entity: SyncSessionLocalEntity)

    @Query(
        """
        SELECT * FROM sync_session_local
        WHERE status NOT IN ('SESSION_COMPLETED', 'SESSION_CANCELLED')
        ORDER BY started_at_epoch_millis DESC
        LIMIT 1
        """,
    )
    suspend fun getActive(): SyncSessionLocalEntity?

    @Query("SELECT * FROM sync_session_local WHERE session_id = :sessionId LIMIT 1")
    suspend fun getById(sessionId: String): SyncSessionLocalEntity?

    @Query("UPDATE sync_session_local SET status = :status WHERE session_id = :sessionId")
    suspend fun updateStatus(sessionId: String, status: String)

    @Query("DELETE FROM sync_session_local WHERE session_id = :sessionId")
    suspend fun delete(sessionId: String)
}

@Dao
interface SyncConflictDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(entity: ir.sayda.yara.hub.database.entity.SyncConflictEntity)

    @Query("SELECT * FROM sync_conflict ORDER BY detected_at_epoch_millis DESC")
    suspend fun getAll(): List<ir.sayda.yara.hub.database.entity.SyncConflictEntity>
}
