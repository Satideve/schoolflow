/* C:\coding_projects\dev\schoolflow\frontend\src\store\auth.tsx */
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

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [token, setTokenState] = useState<string | null>(() => localStorage.getItem("sf_token"));
  const [user, setUser] = useState<any | null>(null);

  useEffect(() => {
    if (token) {
      setAuthToken(token);
      localStorage.setItem("sf_token", token);
      console.debug("[Auth] token set (persisted)");
    } else {
      setAuthToken(undefined);
      localStorage.removeItem("sf_token");
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
      const { data } = await api.post<TokenResponse>("/api/v1/auth/login", bodyString, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        // ensure cookies if backend uses them; api already sets withCredentials: true
      });

      console.debug("[Auth.login] response.data:", data);

      if (!data || !data.access_token) {
        console.error("[Auth.login] no access_token in response", data);
        throw new Error("Login failed: no token received");
      }

      setTokenState(data.access_token);
      // (optional) setUser if backend exposes profile

      console.info("[Auth.login] login successful");
    } catch (err: any) {
      // Log more error detail for debugging
      if (err?.response) {
        console.error("[Auth.login] axios response error:", {
          status: err.response.status,
          data: err.response.data,
          headers: err.response.headers,
        });
      } else {
        console.error("[Auth.login] error:", err);
      }
      throw err; // rethrow so UI sees the failure
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
