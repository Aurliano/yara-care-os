import re

file_path = r"c:\yara-care-os\apps\hub\data\src\main\java\ir\sayda\yara\hub\data\repository\HomeAndConnectivityRepositories.kt"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Fix the combine trailing block to correctly take 5 arguments and compute nextOccurrence
content = re.sub(
    r"\) \{ executionInputs, careInputs, runtimeInputs, diagnostics ->",
    r") { nowEpochMillis: Long, executionInputs, careInputs, runtimeInputs, diagnostics ->",
    content
)

# Then we need to compute nextOccurrence properly
old_destruct = """val (executions, todayOccurrences, nextOccurrence) = executionInputs
                val (careActivities, prescriptions, replicaState) = careInputs"""
new_destruct = """val (executions, todayOccurrences, _) = executionInputs
                val (careActivities, prescriptions, replicaState) = careInputs
                val nextOccurrence = todayOccurrences
                    .filter { it.scheduledForEpochMillis > nowEpochMillis && it.status.name == "SCHEDULED" }
                    .minByOrNull { it.scheduledForEpochMillis }"""

content = content.replace(old_destruct, new_destruct)

# Fix the mapNotNull for building today items
build_old = """val allTodayReminders = todayOccurrences.map { occurrence ->
            val activity = activityBySchedule[occurrence.scheduleDefinitionId]
            val prescription = activity?.let { prescriptionByActivity[it.id] }
            val confirmedAt = executionByOccurrence[occurrence.id]?.id?.let { confirmedAtByExecutionId[it] }"""

build_new = """val allTodayReminders = todayOccurrences.mapNotNull { occurrence ->
            val activity = activityBySchedule[occurrence.scheduleDefinitionId]
            if (activity == null || activity.status != "ACTIVE") {
                return@mapNotNull null
            }
            val prescription = prescriptionByActivity[activity.id]
            val confirmedAt = executionByOccurrence[occurrence.id]?.id?.let { confirmedAtByExecutionId[it] }"""

content = content.replace(build_old, build_new)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("FIXED")
