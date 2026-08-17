import { apiRequest } from "../client";

export type WorkflowDefinition = {
  id: string;
  code: string;
  name: string;
  status: string;
};

export function getWorkflowDefinitionByCode(code: string): Promise<WorkflowDefinition> {
  return apiRequest(`/workflow-definitions/by-code/${encodeURIComponent(code)}/`);
}
