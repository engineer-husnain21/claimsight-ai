/** Mirrors the backend token response from POST /auth/login and /auth/refresh. */
export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
}

export type UserRole = "submitter" | "reviewer" | "admin";

/** Fields of the backend user response that the frontend uses. */
export interface UserResponse {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
}