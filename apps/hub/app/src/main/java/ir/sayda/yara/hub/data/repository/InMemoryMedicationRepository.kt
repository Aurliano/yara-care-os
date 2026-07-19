package ir.sayda.yara.hub.data.repository

import android.content.Context
import ir.sayda.yara.hub.data.scheduler.AndroidMedicationScheduler
import ir.sayda.yara.hub.domain.model.Medication
import ir.sayda.yara.hub.domain.repository.MedicationRepository
import ir.sayda.yara.hub.domain.repository.MedicationScheduler
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow

/**
 * In-memory implementation of MedicationRepository for MVP validation.
 * Handles CRUD and coordinates with the scheduler to manage alarms.
 */
class InMemoryMedicationRepository(context: Context) : MedicationRepository {
    
    private val scheduler: MedicationScheduler = AndroidMedicationScheduler(context)
    
    private val medications = MutableStateFlow(
        listOf(
            Medication(id = "1", name = "قرص فشار خون", dosageTime = "ساعت ۱۱:۰۰")
        )
    )

    override fun getMedications(): Flow<List<Medication>> = medications

    override suspend fun getMedicationById(id: String): Medication? {
        return medications.value.find { it.id == id }
    }

    override suspend fun markAsCompleted(id: String) {
        val currentList = medications.value
        val updatedList = currentList.map {
            if (it.id == id) it.copy(isCompleted = true) else it
        }
        medications.value = updatedList
    }

    override suspend fun scheduleMedication(medication: Medication) {
        val currentList = medications.value
        val existing = currentList.find { it.id == medication.id }
        
        if (existing == null) {
            medications.value = currentList + medication
        } else {
            medications.value = currentList.map { if (it.id == medication.id) medication else it }
        }
        
        if (medication.isEnabled) {
            scheduler.schedule(medication)
        } else {
            scheduler.cancel(medication)
        }
    }

    override suspend fun deleteMedication(id: String) {
        val medication = medications.value.find { it.id == id } ?: return
        scheduler.cancel(medication)
        medications.value = medications.value.filter { it.id != id }
    }

    override suspend fun toggleMedication(id: String, enabled: Boolean) {
        val currentList = medications.value
        val updatedList = currentList.map {
            if (it.id == id) {
                val updated = it.copy(isEnabled = enabled)
                if (enabled) scheduler.schedule(updated) else scheduler.cancel(updated)
                updated
            } else it
        }
        medications.value = updatedList
    }
}
