import { listCareActivities, listPrescriptions } from "../../api/endpoints/care";
import { getWorkflowDefinitionByCode } from "../../api/endpoints/workflow";
import { ApiError } from "../../api/errors";

/**
 * Temporary reuse of the only seeded Hub-dev workflow until a caregiver catalog exists.
 * Never show this code in UI.
 */
export const TEMPORARY_CARE_WORKFLOW_CODE = "wf-hub-dev-medication";

export async function resolveCareWorkflowDefinitionId(elderId: string): Promise<string | null> {
  const [activities, prescriptions] = await Promise.all([
    listCareActivities(elderId),
    listPrescriptions(elderId),
  ]);
  const fromActivity = activities.find((item) => item.workflow_definition_id)?.workflow_definition_id;
  if (fromActivity) {
    return fromActivity;
  }
  const fromPrescription = prescriptions.find((item) => item.care_activity?.workflow_definition_id)
    ?.care_activity.workflow_definition_id;
  if (fromPrescription) {
    return fromPrescription;
  }
  try {
    const definition = await getWorkflowDefinitionByCode(TEMPORARY_CARE_WORKFLOW_CODE);
    return definition.id;
  } catch (error) {
    if (error instanceof ApiError && (error.status === 404 || error.status === 403)) {
      return null;
    }
    throw error;
  }
}
