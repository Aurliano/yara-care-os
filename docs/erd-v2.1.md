erDiagram

    %% =========================================================
    %% IDENTITY & ACCESS
    %% =========================================================

    USER {
        uuid id PK
        string phone UK
        string email
        string full_name
        string status
        datetime created_at
        datetime updated_at
    }

    ELDER {
        uuid id PK
        string full_name
        date birth_date
        uuid photo_media_id
        string status
        datetime created_at
        datetime updated_at
    }

    ROLE {
        uuid id PK
        string code UK
        string name
    }

    PERMISSION {
        uuid id PK
        string code UK
        string name
    }

    ROLE_PERMISSION {
        uuid role_id PK,FK
        uuid permission_id PK,FK
    }

    MEMBERSHIP {
        uuid id PK
        uuid user_id FK
        uuid elder_id FK
        uuid role_id FK
        string relationship
        string status
        boolean is_primary
        datetime joined_at
        datetime ended_at
    }

    INVITATION {
        uuid id PK
        uuid elder_id FK
        uuid invited_by_user_id FK
        string invite_code UK
        string status
        datetime expires_at
        datetime accepted_at
        datetime created_at
    }

    EMERGENCY_RECIPIENT {
        uuid id PK
        uuid elder_id FK
        uuid membership_id FK
        int priority
        string status
        datetime created_at
    }


    %% =========================================================
    %% LICENSING
    %% =========================================================

    PLAN {
        uuid id PK
        string code UK
        string name
        string status
        datetime created_at
    }

    ENTITLEMENT {
        uuid id PK
        string key UK
        string kind
        string description
    }

    PLAN_ENTITLEMENT {
        uuid id PK
        uuid plan_id FK
        uuid entitlement_id FK
        string value
    }

    LICENSE {
        uuid id PK
        uuid elder_id FK
        uuid plan_id FK
        string status
        datetime valid_from
        datetime valid_until
        datetime created_at
    }

    SUBSCRIPTION {
        uuid id PK
        uuid license_id FK
        string status
        datetime started_at
        datetime expires_at
        datetime created_at
    }


    %% =========================================================
    %% CARE
    %% =========================================================

    CARE_GOAL {
        uuid id PK
        uuid elder_id FK
        string title
        string description
        string status
        datetime created_at
    }

    CARE_PLAN {
        uuid id PK
        uuid elder_id FK
        uuid care_goal_id FK
        string name
        string status
        date start_date
        date end_date
        datetime created_at
    }

    CARE_CUE {
        uuid id PK
        string title
        string subtitle
        string voice_prompt
        uuid image_media_id
        string icon
    }

    CARE_ACTIVITY {
        uuid id PK
        uuid elder_id FK
        uuid care_plan_id FK
        uuid care_cue_id FK
        uuid schedule_definition_id FK
        uuid workflow_definition_id FK
        string activity_type
        string status
        int priority
        datetime created_at
        datetime updated_at
    }

    PRESCRIPTION {
        uuid care_activity_id PK,FK
        uuid medication_catalog_id
        string dosage
        string instructions
        string elder_friendly_text
        uuid medication_image_media_id
    }

    CARE_COMPLETION {
        uuid id PK
        uuid care_activity_id FK
        uuid occurrence_id
        uuid workflow_execution_id
        string completion_state
        datetime interpreted_at
    }


    %% =========================================================
    %% SCHEDULING
    %% =========================================================

    SCHEDULE_DEFINITION {
        uuid id PK
        string owner_reference
        string recurrence_definition
        string timezone
        datetime start_at
        datetime end_at
        string status
        datetime created_at
        datetime updated_at
    }

    SCHEDULE_EXCEPTION {
        uuid id PK
        uuid schedule_definition_id FK
        datetime original_time
        datetime replacement_time
        string exception_type
        string reason
    }

    OCCURRENCE {
        uuid id PK
        uuid schedule_definition_id FK
        datetime scheduled_for
        string status
        datetime created_at
    }


    %% =========================================================
    %% WORKFLOW
    %% =========================================================

    WORKFLOW_DEFINITION {
        uuid id PK
        string code UK
        string name
        string status
        json definition
        datetime created_at
        datetime updated_at
    }

    WORKFLOW_EXECUTION {
        uuid id PK
        uuid occurrence_id FK
        uuid workflow_definition_id FK
        string status
        string current_step
        int postpone_count
        int retry_count
        datetime started_at
        datetime completed_at
    }

    CONFIRMATION_EVIDENCE {
        uuid id PK
        uuid workflow_execution_id FK
        string evidence_type
        string source_type
        string source_reference
        uuid actor_user_id
        json payload
        datetime received_at
    }


    %% =========================================================
    %% DEVICE
    %% =========================================================

    DEVICE_MODEL {
        uuid id PK
        string manufacturer
        string model
        string device_type
        string status
    }

    DEVICE_CAPABILITY {
        uuid id PK
        string code UK
        string name
    }

    DEVICE_MODEL_CAPABILITY {
        uuid device_model_id PK,FK
        uuid device_capability_id PK,FK
    }

    DEVICE {
        uuid id PK
        uuid device_model_id FK
        string serial_number UK
        string nickname
        string status
        datetime last_seen_at
        datetime created_at
    }

    DEVICE_PROFILE {
        uuid id PK
        uuid device_id FK
        json settings
        datetime updated_at
    }

    DEVICE_CAPABILITY_OVERRIDE {
        uuid id PK
        uuid device_id FK
        uuid capability_id FK
        string state
        string reason
        uuid changed_by_user_id
        datetime effective_at
    }

    DEVICE_ASSIGNMENT {
        uuid id PK
        uuid device_id FK
        uuid elder_id FK
        string assignment_type
        string status
        datetime assigned_at
        datetime unassigned_at
    }

    PAIRING {
        uuid id PK
        uuid hub_device_id FK
        uuid peripheral_device_id FK
        string status
        datetime paired_at
        datetime ended_at
    }

    DEVICE_COMMAND {
        uuid id PK
        uuid device_id FK
        string command_code
        string status
        string idempotency_key UK
        string execution_reference
        json parameters
        json result
        string failure_reason
        datetime expires_at
        datetime created_at
        datetime completed_at
    }

    COMPARTMENT {
        uuid id PK
        uuid device_id FK
        int number
        string label
        string status
    }

    COMPARTMENT_ASSIGNMENT {
        uuid id PK
        uuid compartment_id FK
        uuid care_activity_id FK
        string status
        datetime assigned_at
        datetime unassigned_at
    }


    %% =========================================================
    %% COMMUNICATION
    %% =========================================================

    CONTACT {
        uuid id PK
        uuid elder_id FK
        string display_name
        string phone
        uuid photo_media_id
        string preferred_channel
        boolean is_priority
        string status
        datetime created_at
    }

    COMMUNICATION_SESSION {
        uuid id PK
        uuid elder_id FK
        string channel
        string status
        string outcome
        string execution_reference
        datetime initiated_at
        datetime connected_at
        datetime ended_at
    }

    SESSION_PARTICIPANT {
        uuid id PK
        uuid communication_session_id FK
        uuid user_id
        uuid contact_id
        string role
    }

    CALL_ATTEMPT {
        uuid id PK
        uuid communication_session_id FK
        string outcome
        string failure_reason
        datetime started_at
        datetime ended_at
    }


    %% =========================================================
    %% EVENT
    %% =========================================================

    EVENT_RECORD {
        uuid id PK
        string event_type
        int event_version
        string producer
        uuid elder_id
        string correlation_id
        string causation_id
        json payload
        datetime occurred_at
        datetime recorded_at
    }


    %% =========================================================
    %% RELATIONS — IDENTITY
    %% =========================================================

    USER ||--o{ MEMBERSHIP : has
    ELDER ||--o{ MEMBERSHIP : has
    ROLE ||--o{ MEMBERSHIP : assigns

    ROLE ||--o{ ROLE_PERMISSION : contains
    PERMISSION ||--o{ ROLE_PERMISSION : contains

    ELDER ||--o{ INVITATION : has
    USER ||--o{ INVITATION : creates

    ELDER ||--o{ EMERGENCY_RECIPIENT : configures
    MEMBERSHIP ||--o| EMERGENCY_RECIPIENT : may_be


    %% =========================================================
    %% RELATIONS — LICENSING
    %% =========================================================

    PLAN ||--o{ PLAN_ENTITLEMENT : contains
    ENTITLEMENT ||--o{ PLAN_ENTITLEMENT : grants

    ELDER ||--o{ LICENSE : owns
    PLAN ||--o{ LICENSE : applies

    LICENSE ||--o{ SUBSCRIPTION : supported_by


    %% =========================================================
    %% RELATIONS — CARE
    %% =========================================================

    ELDER ||--o{ CARE_GOAL : has
    ELDER ||--o{ CARE_PLAN : has

    CARE_GOAL ||--o{ CARE_PLAN : guides
    CARE_PLAN ||--o{ CARE_ACTIVITY : contains

    ELDER ||--o{ CARE_ACTIVITY : receives
    CARE_CUE ||--o{ CARE_ACTIVITY : presents

    CARE_ACTIVITY ||--o| PRESCRIPTION : specializes
    CARE_ACTIVITY ||--o{ CARE_COMPLETION : produces


    %% =========================================================
    %% RELATIONS — SCHEDULING
    %% =========================================================

    SCHEDULE_DEFINITION ||--o{ SCHEDULE_EXCEPTION : exceptions
    SCHEDULE_DEFINITION ||--o{ OCCURRENCE : generates

    SCHEDULE_DEFINITION ||--o{ CARE_ACTIVITY : schedules


    %% =========================================================
    %% RELATIONS — WORKFLOW
    %% =========================================================

    WORKFLOW_DEFINITION ||--o{ CARE_ACTIVITY : configured_for

    OCCURRENCE ||--o| WORKFLOW_EXECUTION : triggers
    WORKFLOW_DEFINITION ||--o{ WORKFLOW_EXECUTION : executes

    WORKFLOW_EXECUTION ||--o{ CONFIRMATION_EVIDENCE : evaluates


    %% =========================================================
    %% RELATIONS — DEVICE
    %% =========================================================

    DEVICE_MODEL ||--o{ DEVICE : defines

    DEVICE_MODEL ||--o{ DEVICE_MODEL_CAPABILITY : supports
    DEVICE_CAPABILITY ||--o{ DEVICE_MODEL_CAPABILITY : capability

    DEVICE ||--o| DEVICE_PROFILE : configured_by

    DEVICE ||--o{ DEVICE_CAPABILITY_OVERRIDE : overrides
    DEVICE_CAPABILITY ||--o{ DEVICE_CAPABILITY_OVERRIDE : target

    DEVICE ||--o{ DEVICE_ASSIGNMENT : assignment_history
    ELDER ||--o{ DEVICE_ASSIGNMENT : receives

    DEVICE ||--o{ DEVICE_COMMAND : executes

    DEVICE ||--o{ COMPARTMENT : contains
    COMPARTMENT ||--o{ COMPARTMENT_ASSIGNMENT : history
    CARE_ACTIVITY ||--o{ COMPARTMENT_ASSIGNMENT : assigned_to


    %% =========================================================
    %% RELATIONS — COMMUNICATION
    %% =========================================================

    ELDER ||--o{ CONTACT : has

    ELDER ||--o{ COMMUNICATION_SESSION : communication_context

    COMMUNICATION_SESSION ||--o{ SESSION_PARTICIPANT : includes
    COMMUNICATION_SESSION ||--o{ CALL_ATTEMPT : attempts

    USER ||--o{ SESSION_PARTICIPANT : may_participate
    CONTACT ||--o{ SESSION_PARTICIPANT : may_participate