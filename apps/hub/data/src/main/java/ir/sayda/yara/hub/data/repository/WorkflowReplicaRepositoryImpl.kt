package ir.sayda.yara.hub.data.repository

import ir.sayda.yara.hub.core.domain.model.WorkflowDefinition
import ir.sayda.yara.hub.core.domain.model.WorkflowExecution
import ir.sayda.yara.hub.core.domain.repository.WorkflowReplicaRepository
import ir.sayda.yara.hub.database.HubDatabase
import ir.sayda.yara.hub.database.mapper.toDomain
import ir.sayda.yara.hub.database.mapper.toEntity
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class WorkflowReplicaRepositoryImpl @Inject constructor(
    database: HubDatabase,
) : WorkflowReplicaRepository {
    private val executionDao = database.workflowExecutionDao()
    private val definitionDao = database.workflowDefinitionDao()

    override fun observeActiveExecutions(): Flow<List<WorkflowExecution>> =
        executionDao.observeActive().map { list -> list.map { it.toDomain() } }

    override fun observeDefinitions(): Flow<List<WorkflowDefinition>> =
        definitionDao.observeAll().map { list -> list.map { it.toDomain() } }

    override suspend fun getDefinition(definitionId: String): WorkflowDefinition? =
        definitionDao.getById(definitionId)?.toDomain()

    override suspend fun getExecutionByOccurrence(occurrenceId: String): WorkflowExecution? =
        executionDao.getByOccurrenceId(occurrenceId)?.toDomain()

    override suspend fun upsertExecution(execution: WorkflowExecution) {
        executionDao.upsert(execution.toEntity())
    }

    override suspend fun getExecution(executionId: String): WorkflowExecution? =
        executionDao.getById(executionId)?.toDomain()

    override suspend fun upsertDefinition(definition: WorkflowDefinition) {
        definitionDao.upsert(definition.toEntity())
    }
}
