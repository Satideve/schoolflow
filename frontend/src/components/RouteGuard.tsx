/* C:\coding_projects\dev\schoolflow\frontend\src\components\RouteGuard.tsx */
import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../store/auth";

/**
 * Simple RouteGuard for React Router v6.
 * - If user has an auth token -> render children
 * - Otherwise redirect to /login and preserve next location in state
 */
export default function RouteGuard({ children }: { children: React.ReactNode }) {
  const auth = useAuth();
  const location = useLocation();

  // If token is present, allow
  if (auth.token) {
    return <>{children}</>;
  }

  // Otherwise redirect to login and pass original location so we can navigate back after login
  return <Navigate to="/login" state={{ from: location }} replace />;
}
