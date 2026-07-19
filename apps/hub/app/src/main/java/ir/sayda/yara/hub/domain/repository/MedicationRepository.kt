package ir.sayda.yara.hub.domain.repository

import ir.sayda.yara.hub.domain.model.Medication
import kotlinx.coroutines.flow.Flow

/**
 * Interface for managing medication data.
 */
interface MedicationRepository {
    fun getMedications(): Flow<List<Medication>>
    suspend fun getMedicationById(id: String): Medication?
    suspend fun markAsCompleted(id: String)
    suspend fun scheduleMedication(medication: Medication)
    suspend fun deleteMedication(id: String)
    suspend fun toggleMedication(id: String, enabled: Boolean)
}
