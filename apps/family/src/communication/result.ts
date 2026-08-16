export type AppResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: Error; message: string };

export function ok<T>(data: T): AppResult<T> {
  return { ok: true, data };
}

export function err(error: Error, message = error.message): AppResult<never> {
  return { ok: false, error, message };
}

export class ActiveCallExistsError extends Error {
  constructor(message = "An active communication session already exists.") {
    super(message);
    this.name = "ActiveCallExistsError";
  }
}

export class IllegalTransitionError extends Error {
  constructor(from: string, to: string) {
    super(`Illegal call transition: ${from} → ${to}`);
    this.name = "IllegalTransitionError";
  }
}
