/**
 * React Native / Hermes polyfills required by LiveKit and WebRTC client libraries.
 * Must be imported at the very top of the application root layout before other dependencies.
 */

if (typeof globalThis.DOMException === "undefined") {
  class DOMExceptionPolyfill extends Error {
    readonly code: number = 0;
    constructor(message?: string, name?: string) {
      super(message);
      this.name = name || "DOMException";
    }
  }

  (globalThis as unknown as { DOMException: unknown }).DOMException = DOMExceptionPolyfill;
  if (typeof global !== "undefined") {
    (global as unknown as { DOMException: unknown }).DOMException = DOMExceptionPolyfill;
  }
}

// Event / EventTarget / CustomEvent — Hermes has no DOM Event, but livekit-client
// creates `new Event(...)` for track/reconnect/signal paths and abort handling.
// event-target-shim's main entry only exports EventTarget; its dist also defines
// an internal Event. We install a minimal spec-compliant Event that satisfies
// `instanceof Event` and `dispatchEvent(new Event("abort"))` used by abort handling.
if (typeof (globalThis as any).Event === "undefined") {
  class ShimEvent {
    readonly type: string;
    readonly bubbles: boolean;
    readonly cancelable: boolean;
    readonly composed: boolean;
    readonly target: unknown = null;
    readonly currentTarget: unknown = null;
    readonly eventPhase: number = 0;
    readonly isTrusted: boolean = false;
    readonly defaultPrevented: boolean = false;
    readonly timeStamp: number = Date.now();
    constructor(type: string, init?: { bubbles?: boolean; cancelable?: boolean; composed?: boolean }) {
      this.type = type;
      this.bubbles = !!init?.bubbles;
      this.cancelable = !!init?.cancelable;
      this.composed = !!init?.composed;
    }
    stopPropagation() {}
    stopImmediatePropagation() {}
    preventDefault() {}
    composedPath(): unknown[] { return []; }
  }
  (globalThis as any).Event = ShimEvent as unknown as typeof Event;
  (global as any).Event = ShimEvent as unknown as typeof Event;
  const w: any = typeof window !== "undefined" ? (window as any) : undefined;
  if (w && !w.Event) w.Event = ShimEvent;
}
if (typeof (globalThis as any).CustomEvent === "undefined") {
  const Base: any = (globalThis as any).Event;
  class ShimCustomEvent extends Base {
    readonly detail: unknown;
    constructor(type: string, init?: { detail?: unknown; bubbles?: boolean; cancelable?: boolean; composed?: boolean }) {
      super(type, init);
      this.detail = init?.detail;
    }
  }
  (globalThis as any).CustomEvent = ShimCustomEvent as unknown as typeof CustomEvent;
  (global as any).CustomEvent = ShimCustomEvent as unknown as typeof CustomEvent;
  const w: any = typeof window !== "undefined" ? (window as any) : undefined;
  if (w && !w.CustomEvent) w.CustomEvent = ShimCustomEvent;
}
// Ensure EventTarget exists (abort-controller / livekit use it)
if (typeof (globalThis as any).EventTarget === "undefined") {
  try {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const shim: any = require("event-target-shim");
    const ShimEventTarget: any = shim.EventTarget ?? shim.default?.EventTarget;
    if (ShimEventTarget) {
      (globalThis as any).EventTarget = ShimEventTarget;
      (global as any).EventTarget = ShimEventTarget;
      const w: any = typeof window !== "undefined" ? (window as any) : undefined;
      if (w && !w.EventTarget) w.EventTarget = ShimEventTarget;
    }
  } catch {}
}

if (typeof globalThis.window === "undefined" && typeof global !== "undefined") {
  (globalThis as unknown as { window: unknown }).window = globalThis;
}
