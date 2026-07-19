package ir.sayda.yara.hub.data.repository

import ir.sayda.yara.hub.domain.model.Medication
import ir.sayda.yara.hub.domain.repository.MedicationRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.map

/**
 * In-memory implementation of MedicationRepository for MVP validation.
 */
object InMemoryMedicationRepository : MedicationRepository {
    private val medications = MutableStateFlow(
        listOf(
            Medication(id = "1", name = "قرص فشار خون", dosageTime = "ساعت ۱۱:۰۰")
        )
    )

    override fun getMedications(): Flow<List<Medication>> = medications

    override suspend fun markAsCompleted(id: String) {
        val currentList = medications.value
        val updatedList = currentList.map {
            if (it.id == id) it.copy(isCompleted = true) else it
        }
        medications.value = updatedList
    }
}
