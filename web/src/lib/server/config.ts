import "server-only";

interface ServerConfig {
  apiBaseUrl: string;
  requestTimeoutMs: number;
}

let cachedConfig: ServerConfig | null = null;

function readRequiredEnv(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}

function parseBaseUrl(raw: string): string {
  const url = new URL(raw);
  if (url.protocol !== "http:" && url.protocol !== "https:") {
    throw new Error("API_BASE_URL must use http or https.");
  }
  return raw.replace(/\/+$/, "");
}

/** Returns validated server-side configuration. Read lazily so builds do not need runtime env. */
export function getServerConfig(): ServerConfig {
  if (cachedConfig === null) {
    cachedConfig = {
      apiBaseUrl: parseBaseUrl(readRequiredEnv("API_BASE_URL")),
      // AI reviews can take up to ~15 seconds, so allow some headroom.
      requestTimeoutMs: 30_000,
    };
  }
  return cachedConfig;
}