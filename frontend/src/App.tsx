/* C:\coding_projects\dev\schoolflow\frontend\src\App.tsx */
import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import Shell from "./components/layout/Shell";
import RouteGuard from "./components/RouteGuard";

import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import About from "./pages/About";
import InvoicesList from "./pages/InvoicesList";
import InvoiceDetail from "./pages/InvoiceDetail";
import CreateInvoice from "./pages/CreateInvoice";
import ReceiptsList from "./pages/ReceiptsList";
import MyInvoices from "./pages/MyInvoices";
import MyReceipts from "./pages/MyReceipts";
import FeeAssignments from "./pages/FeeAssignments";
import NotFound from "./pages/NotFound";
import { useAuth } from "./store/auth";

/**
 * AdminRoute: restrict children to admin-like roles only.
 * Admin-like: admin, clerk, accountant.
 */
function AdminRoute({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const role: string | undefined = user?.role;
  const isAdminLike =
    role === "admin" || role === "clerk" || role === "accountant";

  if (!isAdminLike) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      {/* Protected section wrapped with Shell + RouteGuard */}
      <Route
        path="/"
        element={
          <RouteGuard>
            <Shell>
              <Dashboard />
            </Shell>
          </RouteGuard>
        }
      />

      {/* Admin-only invoice/receipt management */}
      <Route
        path="/invoices"
        element={
          <RouteGuard>
            <Shell>
              <AdminRoute>
                <InvoicesList />
              </AdminRoute>
            </Shell>
          </RouteGuard>
        }
      />

      <Route
        path="/invoices/create"
        element={
          <RouteGuard>
            <Shell>
              <AdminRoute>
                <CreateInvoice />
              </AdminRoute>
            </Shell>
          </RouteGuard>
        }
      />

      <Route
        path="/invoices/:id"
        element={
          <RouteGuard>
            <Shell>
              <AdminRoute>
                <InvoiceDetail />
              </AdminRoute>
            </Shell>
          </RouteGuard>
        }
      />

      <Route
        path="/receipts"
        element={
          <RouteGuard>
            <Shell>
              <AdminRoute>
                <ReceiptsList />
              </AdminRoute>
            </Shell>
          </RouteGuard>
        }
      />

      <Route
        path="/fee-assignments"
        element={
          <RouteGuard>
            <Shell>
              <AdminRoute>
                <FeeAssignments />
              </AdminRoute>
            </Shell>
          </RouteGuard>
        }
      />

      {/* Student/parent pages */}
      <Route
        path="/my/invoices"
        element={
          <RouteGuard>
            <Shell>
              <MyInvoices />
            </Shell>
          </RouteGuard>
        }
      />

      <Route
        path="/my/receipts"
        element={
          <RouteGuard>
            <Shell>
              <MyReceipts />
            </Shell>
          </RouteGuard>
        }
      />

      <Route
        path="/about"
        element={
          <RouteGuard>
            <Shell>
              <About />
            </Shell>
          </RouteGuard>
        }
      />

      {/* 404 */}
      <Route
        path="/404"
        element={
          <RouteGuard>
            <Shell>
              <NotFound />
            </Shell>
          </RouteGuard>
        }
      />
      <Route path="*" element={<Navigate to="/404" replace />} />
    </Routes>
  );
}
