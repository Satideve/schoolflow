/* C:\coding_projects\dev\schoolflow\frontend\src\components\RouteGuard.tsx */
import React from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../store/auth";

export default function RouteGuard({ children }: { children: React.ReactNode }) {
  const { token } = useAuth();

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}
