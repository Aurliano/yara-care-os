Decision 1
CareActivity owns exactly one ScheduleDefinition.
Reason:
Owner resolution must remain deterministic.
Decision 2
WorkflowDefinition is referenced by FK.
Reason:
Reusable immutable policy template.
Decision 3
OccurrenceDue management command
is a temporary operational shim.
Reason:
Until Synchronization/Event consumers exist.