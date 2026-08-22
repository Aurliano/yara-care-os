"""Idempotent apply of the medication reminder policy to existing definitions."""

from django.core.management.base import BaseCommand

from domains.care.services.activities import list_medication_workflow_definition_ids
from domains.workflow.exceptions import WorkflowNotFoundError
from domains.workflow.medication_reminder_policy import (
    definition_matches_medication_policy,
    medication_reminder_definition,
)
from domains.workflow.services.executions import (
    get_workflow_definition,
    get_workflow_definition_by_code,
    replace_workflow_definition,
)
from integration.services.hub_dev_seed import DEV_WORKFLOW_CODE


class Command(BaseCommand):
    help = (
        "Apply the canonical medication reminder policy to existing medication "
        "workflow definitions so a lab elder does not need to be recreated."
    )

    def handle(self, *args, **options) -> None:
        definition = medication_reminder_definition()
        target_ids = set(list_medication_workflow_definition_ids())
        try:
            seeded = get_workflow_definition_by_code(DEV_WORKFLOW_CODE)
            target_ids.add(seeded.id)
        except WorkflowNotFoundError:
            pass

        updated = 0
        unchanged = 0
        for definition_id in sorted(target_ids, key=str):
            current = get_workflow_definition(definition_id)
            if definition_matches_medication_policy(current.definition):
                unchanged += 1
                continue
            replace_workflow_definition(
                workflow_definition_id=definition_id,
                definition=definition,
            )
            updated += 1
            self.stdout.write(f"Updated workflow definition {definition_id} ({current.code})")

        self.stdout.write(
            self.style.SUCCESS(
                f"Medication reminder policy: updated={updated} unchanged={unchanged}"
            )
        )
