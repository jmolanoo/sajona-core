import React, { createContext, useCallback, useContext, useEffect, useState } from "react";
import { apiClient, type AuthSessionPayload } from "../api/client";
import { db } from "../db/schema";
import { syncNow } from "../db/syncEngine";
import type { CoreEntityType, UserProfile } from "../domain/types";

interface AuthContextValue {
  user: UserProfile | null;
  loading: boolean;
  offlineGraceExpired: boolean;
  login: (identifier: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  can: (entity: CoreEntityType, action: "read" | "write" | "delete") => boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [offlineGraceExpired, setOfflineGraceExpired] = useState<boolean>(false);

  const persistOfflineProfile = useCallback(async (profile: UserProfile) => {
    const now = new Date();
    const grace = new Date(now.getTime() + 7 * 86400 * 1000).toISOString();
    await db.offline_session.put({
      id: "current",
      user: profile,
      last_online_login: now.toISOString(),
      offline_grace_until: grace,
    });
  }, []);

  useEffect(() => {
    let active = true;
    (async () => {
      const online = typeof navigator === "undefined" || navigator.onLine;
      if (online) {
        const refreshed = await apiClient.refreshAccessToken();
        if (refreshed && active) {
          setUser(refreshed.user);
          await persistOfflineProfile(refreshed.user);
          await syncNow(true);
          if (active) setLoading(false);
          return;
        }
      }
      const cached = await db.offline_session.get("current");
      if (cached && active) {
        if (new Date(cached.offline_grace_until).getTime() > Date.now()) {
          setUser(cached.user);
        } else {
          setOfflineGraceExpired(true);
        }
      }
      if (active) setLoading(false);
    })();

    const onOnline = () => {
      void syncNow();
    };
    window.addEventListener("online", onOnline);
    return () => {
      active = false;
      window.removeEventListener("online", onOnline);
    };
  }, [persistOfflineProfile]);

  const login = useCallback(
    async (identifier: string, password: string) => {
      const resp = await apiClient.request<AuthSessionPayload>("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify({ identifier, password }),
      });
      apiClient.setAccessToken(resp.access_token);
      setUser(resp.user);
      setOfflineGraceExpired(false);
      await persistOfflineProfile(resp.user);
      await syncNow(true);
    },
    [persistOfflineProfile]
  );

  const logout = useCallback(async () => {
    await apiClient.request("/api/v1/auth/logout", { method: "POST" }).catch(() => undefined);
    apiClient.setAccessToken(null);
    await db.offline_session.delete("current");
    setUser(null);
  }, []);

  const can = useCallback(
    (entity: CoreEntityType, action: "read" | "write" | "delete"): boolean => {
      if (!user) return false;
      return Boolean(user.permissions[entity]?.includes(action));
    },
    [user]
  );

  return (
    <AuthContext.Provider value={{ user, loading, offlineGraceExpired, login, logout, can }}>
      {children}
    </AuthContext.Provider>
  );
};

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth debe ejecutarse dentro de AuthProvider.");
  return ctx;
}
