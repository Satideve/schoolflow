/* C:\coding_projects\dev\schoolflow\frontend\src\App.tsx */
import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login";
import InvoicesList from "./pages/InvoicesList";
import InvoiceDetail from "./pages/InvoiceDetail";
import CreateInvoice from "./pages/CreateInvoice";
import ReceiptsList from "./pages/ReceiptsList";
import { AuthProvider, useAuth } from "./store/auth";
import Navbar from "./components/Navbar";

function Protected({ children }: { children: JSX.Element }) {
  const { token } = useAuth();
  if (!token) return <Navigate to="/login" replace />;
  return children;
}

export default function App() {
  return (
    <AuthProvider>
      <div className="min-h-screen">
        <Navbar />
        <main className="container mx-auto p-4">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route
              path="/invoices"
              element={
                <Protected>
                  <InvoicesList />
                </Protected>
              }
            />
            <Route
              path="/invoices/create"
              element={
                <Protected>
                  <CreateInvoice />
                </Protected>
              }
            />
            <Route
              path="/invoices/:id"
              element={
                <Protected>
                  <InvoiceDetail />
                </Protected>
              }
            />
            <Route
              path="/receipts"
              element={
                <Protected>
                  <ReceiptsList />
                </Protected>
              }
            />
            <Route path="/" element={<Navigate to="/invoices" replace />} />
          </Routes>
        </main>
      </div>
    </AuthProvider>
  );
}
