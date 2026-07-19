package ir.sayda.yara.hub

import android.app.Application
import ir.sayda.yara.hub.data.repository.InMemoryMedicationRepository
import ir.sayda.yara.hub.domain.repository.MedicationRepository

class YaraApplication : Application() {
    
    // Simple manual DI for MVP
    lateinit var medicationRepository: MedicationRepository
        private set

    override fun onCreate() {
        super.onCreate()
        medicationRepository = InMemoryMedicationRepository(this)
    }
}
