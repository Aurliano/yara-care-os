package ir.sayda.yara.hub.data.repository

import ir.sayda.yara.hub.database.HubDatabase
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

data class ReplicaTableCounts(
    val careActivityCount: Int = 0,
    val workflowDefinitionCount: Int = 0,
    val workflowExecutionCount: Int = 0,
    val scheduleDefinitionCount: Int = 0,
    val occurrenceCount: Int = 0,
    val deviceCount: Int = 0,
    val deviceCommandCount: Int = 0,
    val communicationSessionCount: Int = 0,
    val contactCount: Int = 0,
    val outboxPendingCount: Int = 0,
    val syncConflictCount: Int = 0,
    val lastDownloadSessionId: String? = null,
)

@Singleton
class ReplicaDiagnosticsReader @Inject constructor(
    database: HubDatabase,
) {
    private val careActivityDao = database.careActivityDao()
    private val workflowDefinitionDao = database.workflowDefinitionDao()
    private val workflowExecutionDao = database.workflowExecutionDao()
    private val scheduleDefinitionDao = database.scheduleDefinitionDao()
    private val occurrenceDao = database.occurrenceDao()
    private val deviceDao = database.deviceDao()
    private val deviceCommandDao = database.deviceCommandDao()
    private val communicationSessionDao = database.communicationSessionDao()
    private val contactDao = database.contactDao()
    private val outboxDao = database.outboxDao()
    private val syncConflictDao = database.syncConflictDao()
    private val syncSessionLocalDao = database.syncSessionLocalDao()

    fun observeCounts(): Flow<ReplicaTableCounts> {
        val tableCounts = combine(
            combine(
                careActivityDao.observeAll().map { it.size },
                workflowDefinitionDao.observeAll().map { it.size },
                workflowExecutionDao.observeAll().map { it.size },
            ) { care, definitions, executions ->
                Triple(care, definitions, executions)
            },
            combine(
                scheduleDefinitionDao.observeAll().map { it.size },
                occurrenceDao.observeAll().map { it.size },
                communicationSessionDao.observeAll().map { it.size },
            ) { schedules, occurrences, sessions ->
                Triple(schedules, occurrences, sessions)
            },
            combine(
                contactDao.observeAll().map { it.size },
                outboxDao.observePending().map { it.size },
                syncConflictDao.observeAll().map { it.size },
            ) { contacts, outbox, conflicts ->
                Triple(contacts, outbox, conflicts)
            },
        ) { careTriple, scheduleTriple, infraTriple ->
            ReplicaTableCounts(
                careActivityCount = careTriple.first,
                workflowDefinitionCount = careTriple.second,
                workflowExecutionCount = careTriple.third,
                scheduleDefinitionCount = scheduleTriple.first,
                occurrenceCount = scheduleTriple.second,
                communicationSessionCount = scheduleTriple.third,
                contactCount = infraTriple.first,
                outboxPendingCount = infraTriple.second,
                syncConflictCount = infraTriple.third,
            )
        }
        return combine(
            tableCounts,
            syncSessionLocalDao.observeLatestDownload(),
            deviceDao.observeAll().map { it.size },
            deviceCommandDao.observeQueued().map { it.size },
        ) { counts, latestDownload, devices, commands ->
            counts.copy(
                deviceCount = devices,
                deviceCommandCount = commands,
                lastDownloadSessionId = latestDownload?.sessionId,
            )
        }
    }
}
