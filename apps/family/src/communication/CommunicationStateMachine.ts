import { IllegalTransitionError } from "./result";
import type { CallRuntimeState } from "./model";

const ALLOWED: Record<CallRuntimeState, readonly CallRuntimeState[]> = {
  Idle: ["Connecting"],
  Connecting: ["Connected", "ConnectionLost", "Finished"],
  Connected: ["ConnectionLost", "Finished"],
  ConnectionLost: ["Reconnecting", "Finished"],
  Reconnecting: ["Connected", "ConnectionLost", "Finished"],
  Finished: ["Idle"],
};

export class CommunicationStateMachine {
  constructor(private state: CallRuntimeState = "Idle") {}

  current(): CallRuntimeState {
    return this.state;
  }

  canTransition(to: CallRuntimeState): boolean {
    return ALLOWED[this.state].includes(to);
  }

  transition(to: CallRuntimeState): CallRuntimeState {
    if (!this.canTransition(to)) {
      throw new IllegalTransitionError(this.state, to);
    }
    this.state = to;
    return this.state;
  }

  restore(state: CallRuntimeState): void {
    this.state = state;
  }

  resetToIdle(): void {
    this.state = "Idle";
  }
}
