package ir.sayda.yara.hub.runtime.identity

import ir.sayda.yara.hub.core.identity.computeOccurrenceId as coreComputeOccurrenceId
import ir.sayda.yara.hub.core.identity.computeExecutionId as coreComputeExecutionId
import ir.sayda.yara.hub.core.identity.uuid5 as coreUuid5
import java.util.UUID

fun computeOccurrenceId(scheduleDefinitionId: String, originalTimeIsoUtc: String): String =
    coreComputeOccurrenceId(scheduleDefinitionId, originalTimeIsoUtc)

fun computeExecutionId(occurrenceId: String): String =
    coreComputeExecutionId(occurrenceId)

fun uuid5(namespace: UUID, name: String): UUID =
    coreUuid5(namespace, name)
