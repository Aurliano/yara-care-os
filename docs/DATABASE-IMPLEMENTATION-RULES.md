YARA DATABASE IMPLEMENTATION RULES — ERD V2.1

1. Domain boundaries are architectural boundaries.
   Do not merge models from different domains merely because their fields look similar.

2. Cross-domain references are NOT automatically database foreign keys.

3. DeviceCommand.execution_reference:
   - nullable
   - stores WorkflowExecution.id when command originates from Workflow
   - MUST NOT be a database FK
   - Device must not query Workflow to execute the command

4. CommunicationSession.execution_reference:
   - same semantics as DeviceCommand.execution_reference
   - MUST NOT be a database FK

5. EventRecord:
   - MUST NOT contain nullable FK columns for every possible producer entity
   - domain-specific references belong in payload
   - elder_id is contextual and may be retained
   - correlation_id is for tracing only
   - causation_id is for direct causal tracing only
   - neither is a domain identity or idempotency key

6. CareActivity:
   - belongs to CarePlan
   - MUST NOT duplicate care_goal_id
   - goal is resolved through CarePlan -> CareGoal

7. Prescription:
   - is a true specialization of CareActivity
   - uses shared primary key:
     Prescription.care_activity_id = CareActivity.id

8. Scheduling owns recurrence evaluation.
   Care and Workflow MUST NOT parse/evaluate recurrence independently.

9. Occurrence has stable identity.
   One logical occurrence must not be duplicated during offline/backend reconciliation.

10. Workflow owns:
    - WorkflowExecution
    - ConfirmationPolicy
    - ConfirmationEvidence evaluation
    - retry
    - postpone
    - escalation decisions

11. Workflow does NOT own:
    - DeviceCommand lifecycle
    - CommunicationSession lifecycle
    - Care meaning

12. Device reports physical facts.
    CompartmentClosed does NOT mean MedicationTaken.

13. Care interprets workflow results.
    MedicationTaken is a Care fact.

14. ConfirmationEvidence can originate from:
    - Domain Event
    - Direct Interaction such as Hub UI / Family App

15. DeviceModel defines capabilities.
    DeviceCapabilityOverride is an audited exception, not the normal configuration path.

16. DeviceAssignment must preserve history.
    Device is not permanently owned by an Elder.
    Support OWNED, RENTED and LOANER assignment types.

17. Pairing represents lifecycle relationship between Hub and peripheral.
    It is not the same as current BLE connectivity.

18. DeviceCommand is distinct from synchronization transport.
    Delivery retry does not mean physical command execution retry.

19. DeviceCommand must be idempotent.

20. EmergencyRecipient is separate from Contact/Priority Contact.
    EmergencyRecipient belongs to Identity & Access.
    Priority Contact belongs to Communication.

21. Licensing consumers query entitlements.
    Never implement:
        if plan == PREMIUM
    Prefer:
        has_entitlement("VIDEO_CALL")
        get_limit("MAX_CAREGIVERS")

22. Care has no Licensing dependency in MVP unless a real Care-specific paid feature is introduced.

23. Synchronization, Notification, Monitoring, Media, Firmware/OTA, Billing and Audit
    should be implemented from their own Domain Contracts.
    Do not invent their physical schema from this ERD alone.

24. Use PostgreSQL UUID primary keys.

25. Use PostgreSQL JSONB rather than JSON for implementation fields such as:
    EventRecord.payload,
    WorkflowDefinition.definition,
    DeviceCommand.parameters/result,
    ConfirmationEvidence.payload,
    DeviceProfile.settings.

26. Add database constraints for actual invariants, not only application validation.

27. Do not introduce polymorphic foreign keys such as:
    subject_type + subject_id
    unless explicitly defined by a Domain Contract.

28. Do not add Organization/B2B tenancy yet.

29. Do not introduce microservices.
    Domain boundary != deployment boundary.
    Initial backend is a modular monolith.

30. Do not redesign this schema during implementation without documenting the architectural reason.