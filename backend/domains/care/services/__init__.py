"""Public Care domain service interface.

Contract mapping (Frozen Care Domain Contract V1.1):

Commands:
- CreateCareActivity -> create_care_activity
- UpdateCareActivity -> update_care_activity
- PauseCareActivity -> pause_care_activity
- ResumeCareActivity -> resume_care_activity
- EndCareActivity -> end_care_activity
- CreatePrescription -> create_prescription
- UpdatePrescription -> update_prescription
- InterpretExecutionResult -> interpret_execution_result

Queries:
- GetCareActivity -> get_care_activity
- GetElderCareActivities -> get_elder_care_activities
- GetPrescription -> get_prescription
- GetActivePrescriptions -> get_active_prescriptions
- GetCareCompletionHistory -> get_care_completion_history
- GetCareActivityStatus -> get_care_activity_status
"""

from domains.care.services.activities import (
    create_care_activity,
    end_care_activity,
    get_care_activity,
    get_care_activity_status,
    get_elder_care_activities,
    pause_care_activity,
    resume_care_activity,
    update_care_activity,
)
from domains.care.services.interpretation import get_care_completion_history, interpret_execution_result
from domains.care.services.occurrence_due import handle_occurrence_due_event
from domains.care.services.prescriptions import create_prescription, get_active_prescriptions, get_prescription, update_prescription
from domains.care.services.sync_export import build_care_activity_sync_delta

__all__ = [
    "build_care_activity_sync_delta",
    "create_care_activity",
    "create_prescription",
    "end_care_activity",
    "get_active_prescriptions",
    "get_care_activity",
    "get_care_activity_status",
    "get_care_completion_history",
    "get_elder_care_activities",
    "get_prescription",
    "handle_occurrence_due_event",
    "interpret_execution_result",
    "pause_care_activity",
    "resume_care_activity",
    "update_care_activity",
    "update_prescription",
]
