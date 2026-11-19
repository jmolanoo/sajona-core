import type { UserProfile } from "../domain/types";

export interface AuthSessionPayload {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
  user: UserProfile;
}

class ApiClient {
  private accessToken: string | null = null;
  private refreshPromise: Promise<AuthSessionPayload | null> | null = null;

  setAccessToken(token: string | null): void {
    this.accessToken = token;
  }

  getAccessToken(): string | null {
    return this.accessToken;
  }

  async request<T>(path: string, init: RequestInit = {}, retryOn401 = true): Promise<T> {
    const headers = new Headers(init.headers);
    if (!headers.has("Content-Type") && init.body) {
      headers.set("Content-Type", "application/json");
    }
    headers.set("X-Correlation-ID", crypto.randomUUID());
    if (this.accessToken) {
      headers.set("Authorization", `Bearer ${this.accessToken}`);
    }

    const resp = await fetch(path, { ...init, headers, credentials: "include" });
    if (resp.status === 401 && retryOn401 && !path.includes("/auth/login") && !path.includes("/auth/refresh")) {
      const refreshed = await this.refreshAccessToken();
      if (refreshed) {
        return this.request<T>(path, init, false);
      }
    }

    if (!resp.ok) {
      let msg = `Error HTTP ${resp.status}`;
      try {
        const errBody = (await resp.json()) as { error?: { message?: string }; detail?: string };
        msg = errBody.error?.message || errBody.detail || msg;
      } catch {
        // cuerpo no JSON
      }
      throw new Error(msg);
    }

    if (resp.status === 204) {
      return undefined as T;
    }
    return (await resp.json()) as T;
  }

  async refreshAccessToken(): Promise<AuthSessionPayload | null> {
    if (this.refreshPromise) {
      return this.refreshPromise;
    }
    this.refreshPromise = (async () => {
      try {
        const resp = await fetch("/api/v1/auth/refresh", {
          method: "POST",
          credentials: "include",
          headers: { "X-Correlation-ID": crypto.randomUUID() },
        });
        if (!resp.ok) {
          this.accessToken = null;
          return null;
        }
        const data = (await resp.json()) as AuthSessionPayload;
        this.accessToken = data.access_token;
        return data;
      } catch {
        return null;
      } finally {
        this.refreshPromise = null;
      }
    })();
    return this.refreshPromise;
  }
}

export const apiClient = new ApiClient();
