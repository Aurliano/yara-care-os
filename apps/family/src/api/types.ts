export type UUID = string;
export type ISODateTime = string;
export type ISODate = string;

export type PermissionCode =
  | "VIEW_ELDER_STATUS"
  | "MANAGE_MEDICATION"
  | "MANAGE_CONTACTS"
  | "MANAGE_DEVICES"
  | "INITIATE_CALL"
  | "MANAGE_MEMBERS"
  | "MANAGE_SUBSCRIPTION";

export type EntitlementKey =
  | "MAX_CAREGIVERS"
  | "MAX_HUBS"
  | "MAX_PILLBOXES"
  | "PILLBOX_SUPPORT"
  | "SENSOR_SUPPORT"
  | "VIDEO_CALL";

export type EntitlementMap = Partial<Record<EntitlementKey, number | boolean>>;

export type UserStatus = "ACTIVE" | "SUSPENDED" | "DELETED";
export type ElderStatus = "ACTIVE" | "INACTIVE";
export type MembershipStatus = "INVITED" | "ACTIVE" | "SUSPENDED" | "REVOKED";
export type RoleCode = "PRIMARY_CAREGIVER" | "CAREGIVER" | "VIEWER";
export type InvitationStatus = "PENDING" | "ACCEPTED" | "EXPIRED" | "REVOKED";

export type User = {
  id: UUID;
  phone: string;
  email: string;
  full_name: string;
  status: UserStatus;
  created_at: ISODateTime;
};

export type Elder = {
  id: UUID;
  full_name: string;
  birth_date: ISODate | null;
  status: ElderStatus;
  created_at: ISODateTime;
  updated_at: ISODateTime;
};

export type Membership = {
  id: UUID;
  user_id: UUID;
  user_full_name: string;
  role_code: RoleCode;
  relationship: string;
  status: MembershipStatus;
  is_primary: boolean;
  joined_at: ISODateTime | null;
  ended_at: ISODateTime | null;
};

export type Invitation = {
  id: UUID;
  elder_id: UUID;
  role_code: string;
  invite_code: string;
  status: InvitationStatus;
  expires_at: ISODateTime;
  accepted_at: ISODateTime | null;
  created_at: ISODateTime;
};

export type EmergencyRecipient = {
  id: UUID;
  membership_id: UUID;
  user_id: UUID;
  user_full_name: string;
  priority: number;
  status: "ACTIVE" | "INACTIVE";
};

export type TokenPair = {
  access: string;
  refresh: string;
};

export type CareActivityType = "MEDICATION" | "EXERCISE" | "DAILY_CHECK_IN" | "GENERAL";
export type CareActivityStatus = "ACTIVE" | "PAUSED" | "ENDED" | "CANCELLED";
export type CompletionState =
  | "MEDICATION_TAKEN"
  | "MEDICATION_MISSED"
  | "CARE_ACTIVITY_COMPLETED"
  | "CARE_ACTIVITY_MISSED"
  | "CARE_ACTIVITY_CANCELLED"
  | "CARE_ACTIVITY_FAILED";

export type CareActivity = {
  id: UUID;
  elder_id: UUID;
  activity_type: CareActivityType;
  status: CareActivityStatus;
  schedule_definition_id: UUID;
  workflow_definition_id: UUID;
  display_title: string;
  display_subtitle: string;
  display_icon: string;
  confirmation_requirement: Record<string, unknown>;
  compartment_assignment_reference: string;
  aggregate_version: number;
  created_at: ISODateTime;
  updated_at: ISODateTime;
};

export type Prescription = {
  care_activity_id: UUID;
  care_activity: CareActivity;
  medication_reference: string;
  dosage_information: string;
  elder_friendly_description: string;
  personalized_description: string;
  media_reference: UUID | null;
};

export type CareCompletion = {
  id: UUID;
  care_activity_id: UUID;
  occurrence_id: UUID;
  workflow_execution_id: UUID;
  completion_state: CompletionState;
  interpreted_at: ISODateTime;
  created_at: ISODateTime;
};

export type ScheduleStatus = "ACTIVE" | "PAUSED" | "ENDED" | "CANCELLED";
export type OccurrenceStatus = "SCHEDULED" | "DUE" | "CANCELLED" | "SKIPPED";
export type ScheduleExceptionType = "SKIP" | "CANCEL" | "RESCHEDULE";

export type ScheduleDefinition = {
  id: UUID;
  owner_reference: string;
  recurrence_definition: unknown;
  timezone: string;
  start_at: ISODateTime;
  end_at: ISODateTime | null;
  status: ScheduleStatus;
  created_at: ISODateTime;
  updated_at: ISODateTime;
};

export type Occurrence = {
  id: UUID;
  schedule_definition: UUID;
  scheduled_for: ISODateTime;
  status: OccurrenceStatus;
  created_at: ISODateTime;
};

export type ScheduleException = {
  id: UUID;
  schedule_definition: UUID;
  original_time: ISODateTime;
  replacement_time: ISODateTime | null;
  exception_type: ScheduleExceptionType;
  reason: string;
};

export type DeviceOperationalStatus = "INVENTORY" | "ACTIVE" | "INACTIVE" | "REVOKED";
export type PairingStatus = "PAIRING" | "ACTIVE" | "DISCONNECTED" | "REVOKED";
export type AssignmentType = "OWNED" | "RENTED" | "LOANER";
export type AssignmentStatus = "INVENTORY" | "ASSIGNED" | "RETURNED" | "REFURBISHED";
export type CommandType =
  | "OPEN_COMPARTMENT"
  | "CLOSE_COMPARTMENT"
  | "PLAY_AUDIO"
  | "SHOW_DISPLAY"
  | "DIAGNOSTIC";
export type CommandStatus =
  | "QUEUED"
  | "DELIVERED"
  | "EXECUTING"
  | "SUCCEEDED"
  | "FAILED"
  | "EXPIRED"
  | "CANCELLED";

export type Device = {
  id: UUID;
  device_model_id: UUID;
  serial_number: string;
  operational_status: DeviceOperationalStatus;
  current_state: Record<string, unknown>;
  configuration: Record<string, unknown>;
  last_seen_at: ISODateTime | null;
  aggregate_version: number;
  created_at: ISODateTime;
  updated_at: ISODateTime;
};

export type DeviceState = {
  device_id: UUID;
  operational_status: DeviceOperationalStatus;
  current_state: Record<string, unknown>;
  last_seen_at: ISODateTime | null;
};

export type Pairing = {
  id: UUID;
  hub_device_id: UUID;
  peripheral_device_id: UUID;
  status: PairingStatus;
  paired_at: ISODateTime | null;
  ended_at: ISODateTime | null;
  created_at: ISODateTime;
  updated_at: ISODateTime;
};

export type Plan = {
  id: UUID;
  code: string;
  name: string;
  status: "ACTIVE" | "INACTIVE";
  created_at: ISODateTime;
};

export type License = {
  id: UUID;
  elder_id: UUID;
  plan_code: string;
  status: "ACTIVE" | "SUSPENDED" | "EXPIRED" | "REVOKED";
  valid_from: ISODateTime;
  valid_until: ISODateTime | null;
  created_at: ISODateTime;
};

export type Contact = {
  id: UUID;
  elder_id: UUID;
  display_name: string;
  phone: string;
  communication_identities: Record<string, unknown>[];
  preferred_channel: "VOICE" | "VIDEO" | "MESSAGE";
  photo_reference: UUID | null;
  is_priority: boolean;
  status: string;
  archived_at: ISODateTime | null;
  created_at: ISODateTime;
  updated_at: ISODateTime;
};

export type ApiErrorBody = {
  detail?: string;
  [field: string]: unknown;
};
