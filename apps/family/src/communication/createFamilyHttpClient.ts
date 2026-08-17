import { apiRequest } from "../api/client";
import { ApiError } from "../api/errors";
import type { FamilyHttpClient } from "./CommunicationGateway";

export function createApiFamilyHttpClient(): FamilyHttpClient {
  return {
    async postJson(path, body) {
      const normalized = path.startsWith("/") ? path : `/${path}`;
      try {
        const data = await apiRequest(normalized, { method: "POST", body });
        return { status: 200, body: data };
      } catch (error) {
        if (error instanceof ApiError) {
          return { status: error.status, body: error.body };
        }
        throw error;
      }
    },
  };
}
