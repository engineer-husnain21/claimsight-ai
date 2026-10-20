export const GENERIC_ERROR_MESSAGE = "Something went wrong. Please try again.";

/** Extracts the safe `error` message from a BFF JSON error body. */
export function readErrorMessage(data: unknown): string {
  if (typeof data === "object" && data !== null && "error" in data) {
    const { error } = data as { error: unknown };
    if (typeof error === "string" && error.length > 0) {
      return error;
    }
  }
  return GENERIC_ERROR_MESSAGE;
}