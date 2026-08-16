import { HttpCommunicationGateway } from "./CommunicationGateway";
import { PersistentCommunicationRepository } from "./CommunicationRepository";
import {
  CommunicationRuntime,
  type CommunicationRuntimeOptions,
} from "./CommunicationRuntime";
import { createApiFamilyHttpClient } from "./createFamilyHttpClient";
import { createRealtimeScheduler } from "./ports";
import { createSecureStoreKeyValueStore } from "./secureKeyValueStore";

export function createFamilyCommunicationRuntime(
  options: CommunicationRuntimeOptions = {},
): CommunicationRuntime {
  return new CommunicationRuntime(
    new HttpCommunicationGateway(createApiFamilyHttpClient()),
    new PersistentCommunicationRepository(createSecureStoreKeyValueStore()),
    createRealtimeScheduler(),
    options,
  );
}
