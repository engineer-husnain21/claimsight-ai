import "server-only";

import { getServerConfig } from "@/lib/server/config";

/** Error raised when the backend call fails. The message is always safe to show. */
export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

type HttpMethod = "GET" | "POST" | "PATCH" | "DELETE";

interface ApiRequestOptions {
  method?: HttpMethod;
  body?: unknown;
  accessToken?: string;
}

/** Calls the FastAPI backend from the Next.js server. Never import this in client components. */
export async function apiRequest<T>(
  path: string,
  options: ApiRequestOptions = {},
): Promise<T> {
  if (!path.startsWith("/") || path.includes("..")) {
    throw new Error("API path must be relative and start with '/'.");
  }

  const { apiBaseUrl, requestTimeoutMs } = getServerConfig();

  const headers: Record<string, string> = { Accept: "application/json" };
  if (options.body !== undefined) {
    headers["Content-Type"] = "application/json";
  }
  if (options.accessToken) {
    headers.Authorization = `Bearer ${options.accessToken}`;
  }

  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl}${path}`, {
      method: options.method ?? "GET",
      headers,
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
      cache: "no-store",
      redirect: "error",
      signal: AbortSignal.timeout(requestTimeoutMs),
    });
  } catch {
    throw new ApiError(503, "Backend service is unavailable.");
  }

  if (!response.ok) {
    throw new ApiError(response.status, "Backend request failed.");
  }

  if (response.status === 204) {
    return undefined as T;
  }

  try {
    return (await response.json()) as T;
  } catch {
    throw new ApiError(502, "Backend returned an invalid response.");
  }
}