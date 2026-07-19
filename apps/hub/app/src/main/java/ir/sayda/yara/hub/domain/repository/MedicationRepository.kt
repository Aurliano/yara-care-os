package ir.sayda.yara.hub.domain.repository

import ir.sayda.yara.hub.domain.model.Medication
import kotlinx.coroutines.flow.Flow

/**
 * Interface for managing medication data.
 */
interface MedicationRepository {
    fun getMedications(): Flow<List<Medication>>
    suspend fun markAsCompleted(id: String)
}
