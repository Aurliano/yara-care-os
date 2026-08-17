import { CommunicationStateMachine } from "../communication/CommunicationStateMachine";
import { IllegalTransitionError } from "../communication/result";
import type { CallRuntimeState } from "../communication/model";

const LEGAL: [CallRuntimeState, CallRuntimeState][] = [
  ["Idle", "Connecting"],
  ["Connecting", "Connected"],
  ["Connecting", "ConnectionLost"],
  ["Connecting", "Finished"],
  ["Connected", "ConnectionLost"],
  ["Connected", "Finished"],
  ["ConnectionLost", "Reconnecting"],
  ["ConnectionLost", "Finished"],
  ["Reconnecting", "Connected"],
  ["Reconnecting", "ConnectionLost"],
  ["Reconnecting", "Finished"],
  ["Finished", "Idle"],
];

describe("CommunicationStateMachine", () => {
  it.each(LEGAL)("allows %s → %s", (from, to) => {
    const machine = new CommunicationStateMachine(from);
    expect(machine.canTransition(to)).toBe(true);
    expect(machine.transition(to)).toBe(to);
    expect(machine.current()).toBe(to);
  });

  it("rejects Connected → Reconnecting", () => {
    const machine = new CommunicationStateMachine("Connected");
    expect(machine.canTransition("Reconnecting")).toBe(false);
    expect(() => machine.transition("Reconnecting")).toThrow(IllegalTransitionError);
  });

  it("rejects Idle → Connected", () => {
    const machine = new CommunicationStateMachine();
    expect(() => machine.transition("Connected")).toThrow(/Idle → Connected/);
  });

  it("restores a persisted state after process death", () => {
    const machine = new CommunicationStateMachine();
    machine.restore("ConnectionLost");
    expect(machine.current()).toBe("ConnectionLost");
    expect(machine.transition("Reconnecting")).toBe("Reconnecting");
  });

  it("resets to Idle for cleanup", () => {
    const machine = new CommunicationStateMachine("Finished");
    machine.resetToIdle();
    expect(machine.current()).toBe("Idle");
  });
});
