from django.db import migrations
import uuid

STEP_TIMEOUT_SECONDS = 900
RETRY_MAX = 2
RETRY_TIMEOUT_SECONDS = 900
NOTIFY_TIMEOUT_SECONDS = 900
POSTPONE_MAX_COUNT = 2
POSTPONE_DELAY_SECONDS = 300


def get_default_definition():
    return {
        "initial_action": {"type": "SHOW_REMINDER"},
        "confirmation_policy": {"accepted_evidence_types": ["HUB_CONFIRMATION"]},
        "step_timeout_seconds": STEP_TIMEOUT_SECONDS,
        "retry": {
            "max_retries": RETRY_MAX,
            "action": {"type": "SHOW_REMINDER"},
            "timeout_seconds": RETRY_TIMEOUT_SECONDS,
        },
        "postpone": {
            "allowed": True,
            "max_count": POSTPONE_MAX_COUNT,
            "delay_seconds": POSTPONE_DELAY_SECONDS,
        },
        "escalation_steps": [
            {"action": {"type": "NOTIFY_CAREGIVER"}, "timeout_seconds": NOTIFY_TIMEOUT_SECONDS},
        ],
    }


def seed_workflows(apps, schema_editor):
    WorkflowDefinition = apps.get_model("workflow", "WorkflowDefinition")
    definition = get_default_definition()

    # Seed wf-hub-dev-medication
    if not WorkflowDefinition.objects.filter(code="wf-hub-dev-medication").exists():
        WorkflowDefinition.objects.create(
            id=uuid.uuid4(),
            code="wf-hub-dev-medication",
            name="Hub Dev Medication Reminder",
            status="ACTIVE",
            definition=definition,
        )

    # Seed wf-canonical-medication-reminder
    if not WorkflowDefinition.objects.filter(code="wf-canonical-medication-reminder").exists():
        WorkflowDefinition.objects.create(
            id=uuid.uuid4(),
            code="wf-canonical-medication-reminder",
            name="Canonical Medication Reminder",
            status="ACTIVE",
            definition=definition,
        )


def unseed_workflows(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("workflow", "0003_workflowexecution_aggregate_version"),
    ]

    operations = [
        migrations.RunPython(seed_workflows, unseed_workflows),
    ]

