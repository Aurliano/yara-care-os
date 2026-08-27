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

if (typeof globalThis.window === "undefined" && typeof global !== "undefined") {
  (globalThis as unknown as { window: unknown }).window = globalThis;
}
