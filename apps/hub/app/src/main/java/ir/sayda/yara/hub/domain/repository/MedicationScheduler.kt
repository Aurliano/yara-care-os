package ir.sayda.yara.hub.domain.repository

import ir.sayda.yara.hub.domain.model.Medication

/**
 * Interface for scheduling medication reminders.
 */
interface MedicationScheduler {
    fun schedule(medication: Medication)
    fun cancel(medication: Medication)
}
