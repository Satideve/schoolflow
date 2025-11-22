// C:\coding_projects\dev\schoolflow\frontend\src\store\auth.tsx
import React, { createContext, useContext, useState, useEffect } from "react";
import api, { setAuthToken } from "../api/client";
import type { TokenResponse } from "../types/api";

type AuthContext = {
  token?: string | null;
  user?: any | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthCtx = createContext<AuthContext | undefined>(undefined);

/**
 * Decode a JWT payload (very small helper, no external libs).
 * Returns the parsed JSON payload or null if decoding fails.
 */
function decodeJwtPayload(token: string): any | null {
  try {
    const parts = token.split(".");
    if (parts.length < 2) return null;
    const payloadBase64 = parts[1];

    // Handle URL-safe base64 and padding
    const normalized = payloadBase64.replace(/-/g, "+").replace(/_/g, "/");
    const padded = normalized.padEnd(
      Math.ceil(normalized.length / 4) * 4,
      "=",
    );

    const json = atob(padded);
    return JSON.parse(json);
  } catch (err) {
    console.error("[Auth] Failed to decode JWT payload:", err);
    return null;
  }
}

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [token, setTokenState] = useState<string | null>(() =>
    localStorage.getItem("sf_token"),
  );
  const [user, setUser] = useState<any | null>(null);

  useEffect(() => {
    if (token) {
      setAuthToken(token);
      localStorage.setItem("sf_token", token);
      console.debug("[Auth] token set (persisted)");

      // 1) Decode token as quick fallback
      const payload = decodeJwtPayload(token);
      if (payload) {
        const id =
          payload.sub !== undefined && payload.sub !== null
            ? Number(payload.sub)
            : undefined;
        const role = payload.role;
        setUser({
          id,
          role,
          raw: payload,
        });
        console.debug("[Auth] user decoded from token:", { id, role });
      } else {
        setUser(null);
      }

      // 2) Try to load full profile from /auth/me to get canonical user info
      (async () => {
        try {
          const { data } = await api.get("/api/v1/auth/me");
          // Expecting: { id, email, role, is_active }
          setUser((prev: any) => ({
            ...prev,
            ...data,
          }));
          console.debug("[Auth] user loaded from /auth/me:", data);
        } catch (err) {
          console.error("[Auth] failed to load /auth/me:", err);
          // keep fallback from decoded JWT
        }
      })();
    } else {
      setAuthToken(undefined);
      localStorage.removeItem("sf_token");
      setUser(null);
      console.debug("[Auth] token cleared");
    }
  }, [token]);

  /**
   * login - debug version
   * Sends x-www-form-urlencoded body (matches backend expectations).
   */
  const login = async (email: string, password: string) => {
    console.debug("[Auth.login] called", { email });

    const params = new URLSearchParams();
    params.append("grant_type", "password");
    params.append("username", email);
    params.append("password", password);

    const bodyString = params.toString();
    console.debug("[Auth.login] payload (form-url-encoded):", bodyString);

    try {
      const { data } = await api.post<TokenResponse>(
        "/api/v1/auth/login",
        bodyString,
        {
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
        },
      );

      console.debug("[Auth.login] response.data:", data);

      if (!data || !data.access_token) {
        console.error("[Auth.login] no access_token in response", data);
        throw new Error("Login failed: no token received");
      }

      // Setting the token will trigger the useEffect above, which will decode and call /me.
      setTokenState(data.access_token);

      console.info("[Auth.login] login successful");
    } catch (err: any) {
      if (err?.response) {
        console.error("[Auth.login] axios response error:", {
          status: err.response.status,
          data: err.response.data,
          headers: err.response.headers,
        });
      } else {
        console.error("[Auth.login] error:", err);
      }
      throw err;
    }
  };

  const logout = () => {
    setTokenState(null);
    setUser(null);
    console.info("[Auth.logout]");
  };

  return (
    <AuthCtx.Provider value={{ token, user, login, logout }}>
      {children}
    </AuthCtx.Provider>
  );
};

export function useAuth() {
  const ctx = useContext(AuthCtx);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
