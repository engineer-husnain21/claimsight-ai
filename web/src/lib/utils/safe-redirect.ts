const DEFAULT_REDIRECT_PATH = "/dashboard";
// Control characters and backslashes can turn "/path" into a protocol-relative URL in browsers.
const UNSAFE_CHARACTERS = /[\u0000-\u001f\u007f\\]/;

/** Returns an internal path that is safe to redirect to, or the default path. Blocks open redirects. */
export function getSafeRedirectPath(
  value: string | string[] | undefined,
  fallback: string = DEFAULT_REDIRECT_PATH,
): string {
  if (typeof value !== "string" || value.length === 0 || value.length > 512) {
    return fallback;
  }
  if (!value.startsWith("/") || value.startsWith("//") || UNSAFE_CHARACTERS.test(value)) {
    return fallback;
  }
  if (value === "/login" || value.startsWith("/login?") || value.startsWith("/api/")) {
    return fallback;
  }
  return value;
}