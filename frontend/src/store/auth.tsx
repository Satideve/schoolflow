/* C:\coding_projects\dev\schoolflow\frontend\src\store\auth.tsx */
import React, { createContext, useContext, useState, useEffect } from "react";
import api, { setAuthToken } from "../api/client";
import type { TokenResponse, User } from "../types/api";

type AuthContext = {
  token: string | null;
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthCtx = createContext<AuthContext | undefined>(undefined);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [token, setToken] = useState<string | null>(
    localStorage.getItem("sf_token")
  );
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    if (token) {
      localStorage.setItem("sf_token", token);
      setAuthToken(token);
    } else {
      localStorage.removeItem("sf_token");
      setAuthToken(undefined);
      setUser(null);
    }
  }, [token]);

  const login = async (email: string, password: string) => {
    const res = await api.post<TokenResponse>("/api/v1/auth/login", {
      email,
      password,
    });

    setToken(res.data.access_token);
  };

  const logout = () => {
    setToken(null);
    setUser(null);
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
