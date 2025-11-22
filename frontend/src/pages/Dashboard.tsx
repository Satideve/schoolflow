// C:\coding_projects\dev\schoolflow\frontend\src\pages\Dashboard.tsx
import React from "react";
import { Link } from "react-router-dom";
import Card from "../components/ui/card";
import { useInvoices, useReceipts } from "../api/queries";
import { useAuth } from "../store/auth";

const AdminDashboard: React.FC = () => {
  const {
    data: invoicesData,
    isLoading: invoicesLoading,
    isError: invoicesError,
  } = useInvoices();

  const {
    data: receiptsData,
    isLoading: receiptsLoading,
    isError: receiptsError,
  } = useReceipts();

  const invoices = Array.isArray(invoicesData)
    ? invoicesData
    : invoicesData?.results ?? invoicesData ?? [];

  const receipts = Array.isArray(receiptsData)
    ? receiptsData
    : receiptsData?.results ?? receiptsData ?? [];

  const totalRevenue =
    invoices && Array.isArray(invoices)
      ? invoices.reduce((sum: number, inv: any) => {
          const paid = Number(inv.paid_amount ?? 0);
          return sum + (isNaN(paid) ? 0 : paid);
        }, 0)
      : 0;

  const outstandingCount =
    invoices && Array.isArray(invoices)
      ? invoices.filter((inv: any) => {
          const balance = Number(inv.balance ?? 0);
          return balance > 0;
        }).length
      : 0;

  const lastReceipts =
    receipts && Array.isArray(receipts)
      ? [...receipts]
          .sort((a: any, b: any) => {
            const da = new Date(a.created_at ?? 0).getTime();
            const db = new Date(b.created_at ?? 0).getTime();
            return db - da;
          })
          .slice(0, 5)
      : [];

  const base = import.meta.env.VITE_API_BASE || "http://localhost:8000";

  const loading = invoicesLoading || receiptsLoading;
  const error = invoicesError || receiptsError;

  return (
    <div className="grid grid-cols-1 gap-4">
      {/* Welcome + quick links */}
      <Card>
        <h2 className="text-lg font-semibold mb-2">Welcome</h2>
        <p className="text-sm text-slate-600 dark:text-slate-300 mb-3">
          Quick links:
        </p>
        <div className="flex flex-wrap gap-2">
          <Link
            to="/invoices"
            className="inline-flex items-center px-3 py-1 rounded border border-slate-300 text-sm text-slate-800 hover:bg-slate-100"
          >
            Invoices
          </Link>
          <Link
            to="/receipts"
            className="inline-flex items-center px-3 py-1 rounded border border-slate-300 text-sm text-slate-800 hover:bg-slate-100"
          >
            Receipts
          </Link>
          <Link
            to="/invoices/create"
            className="inline-flex items-center px-3 py-1 rounded border border-slate-300 text-sm text-slate-800 hover:bg-slate-100"
          >
            Create Invoice
          </Link>
        </div>
      </Card>

      {/* Metrics cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <h3 className="text-sm font-medium text-slate-500 mb-1">
            Total Revenue (all time)
          </h3>
          {loading ? (
            <div className="text-slate-400 text-sm">Loading...</div>
          ) : error ? (
            <div className="text-red-600 text-sm">
              Failed to load metrics.
            </div>
          ) : (
            <div className="text-2xl font-semibold">
              ₹
              {totalRevenue.toLocaleString("en-IN", {
                maximumFractionDigits: 2,
              })}
            </div>
          )}
        </Card>

        <Card>
          <h3 className="text-sm font-medium text-slate-500 mb-1">
            Outstanding Invoices
          </h3>
          {loading ? (
            <div className="text-slate-400 text-sm">Loading...</div>
          ) : error ? (
            <div className="text-red-600 text-sm">
              Failed to load metrics.
            </div>
          ) : (
            <div className="text-2xl font-semibold">{outstandingCount}</div>
          )}
        </Card>
      </div>

      {/* Last 5 receipts */}
      <Card>
        <h3 className="text-sm font-medium text-slate-500 mb-3">
          Last 5 receipts
        </h3>
        {receiptsLoading ? (
          <div className="text-slate-400 text-sm">Loading receipts...</div>
        ) : receiptsError ? (
          <div className="text-red-600 text-sm">Failed to load receipts.</div>
        ) : lastReceipts.length === 0 ? (
          <div className="text-slate-500 text-sm">No receipts yet.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr>
                  <th className="p-2 text-left">ID</th>
                  <th className="p-2 text-left">Receipt No</th>
                  <th className="p-2 text-left">Created At</th>
                  <th className="p-2 text-left">Actions</th>
                </tr>
              </thead>
              <tbody>
                {lastReceipts.map((r: any) => (
                  <tr key={r.id} className="border-t">
                    <td className="p-2">{r.id}</td>
                    <td className="p-2">{r.receipt_no ?? "-"}</td>
                    <td className="p-2">{r.created_at ?? "-"}</td>
                    <td className="p-2">
                      <a
                        href={`${base}/api/v1/receipts/${r.id}/download`}
                        target="_blank"
                        rel="noreferrer"
                        className="text-blue-600"
                      >
                        Download
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
};

const StudentParentDashboard: React.FC<{ role: string | undefined }> = ({
  role,
}) => {
  return (
    <div className="grid grid-cols-1 gap-4">
      <Card>
        <h2 className="text-lg font-semibold mb-2">
          Welcome {role ? role.toUpperCase() : "User"}
        </h2>
        <p className="text-sm text-slate-600 dark:text-slate-300 mb-3">
          This is the student/parent dashboard placeholder.
        </p>
        <p className="text-sm text-slate-600 dark:text-slate-300">
          In the next steps, we will add:
        </p>
        <ul className="list-disc list-inside text-sm text-slate-600 dark:text-slate-300 mt-1">
          <li>My invoices</li>
          <li>My receipts</li>
          <li>Outstanding balance summary</li>
        </ul>
      </Card>
    </div>
  );
};

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const role = user?.role;

  const isAdminLike =
    role === "admin" || role === "clerk" || role === "accountant";

  if (isAdminLike) {
    return <AdminDashboard />;
  }

  return <StudentParentDashboard role={role} />;
};

export default Dashboard;
