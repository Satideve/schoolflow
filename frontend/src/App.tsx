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

      <Route
        path="/invoices"
        element={
          <RouteGuard>
            <Shell>
              <InvoicesList />
            </Shell>
          </RouteGuard>
        }
      />

      <Route
        path="/invoices/create"
        element={
          <RouteGuard>
            <Shell>
              <CreateInvoice />
            </Shell>
          </RouteGuard>
        }
      />

      <Route
        path="/invoices/:id"
        element={
          <RouteGuard>
            <Shell>
              <InvoiceDetail />
            </Shell>
          </RouteGuard>
        }
      />

      <Route
        path="/receipts"
        element={
          <RouteGuard>
            <Shell>
              <ReceiptsList />
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

      <Route path="/404" element={<div className="p-8">Not found</div>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
