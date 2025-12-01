// C:\coding_projects\dev\schoolflow\frontend\src\pages\Dashboard.tsx
import React, { useMemo } from "react";
import { Link } from "react-router-dom";
import Card from "../components/ui/card";
import {
  useInvoices,
  useReceipts,
  useMyInvoices,
  useStudents,
} from "../api/queries";
import { useAuth } from "../store/auth";
import { formatMoney } from "../lib/utils";

/* ------------------------------------------------------------------
   ADMIN / ACCOUNTANT DASHBOARD
------------------------------------------------------------------- */

const AdminDashboard: React.FC = () => {
  const { user } = useAuth();

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
          const balance = Number(
            inv.balance != null ? inv.balance : inv.total_due ?? 0
          );
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

  const adminLabel = user?.email
    ? `Welcome, ${user.email}`
    : "Welcome to SchoolFlow";

  return (
    <div className="space-y-6">
      {/* Header + quick actions */}
      <Card>
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold mb-1">{adminLabel}</h2>
            <p className="text-sm text-slate-600 dark:text-slate-300">
              Overview of fee invoices, receipts and key metrics.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link
              to="/invoices/create"
              className="inline-flex items-center px-3 py-1.5 rounded-md bg-blue-600 text-white text-sm hover:bg-blue-700"
            >
              + Create Invoice
            </Link>
            <Link
              to="/invoices"
              className="inline-flex items-center px-3 py-1.5 rounded-md border border-slate-300 text-sm text-slate-800 hover:bg-slate-100"
            >
              View Invoices
            </Link>
            <Link
              to="/receipts"
              className="inline-flex items-center px-3 py-1.5 rounded-md border border-slate-300 text-sm text-slate-800 hover:bg-slate-100"
            >
              View Receipts
            </Link>
          </div>
        </div>
      </Card>

      {/* Metric cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <h3 className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-1">
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
              {formatMoney(totalRevenue)}
            </div>
          )}
        </Card>

        <Card>
          <h3 className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-1">
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

        <Card>
          <h3 className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-1">
            Total Receipts Issued
          </h3>
          {receiptsLoading ? (
            <div className="text-slate-400 text-sm">Loading...</div>
          ) : receiptsError ? (
            <div className="text-red-600 text-sm">
              Failed to load receipts.
            </div>
          ) : (
            <div className="text-2xl font-semibold">
              {receipts.length ?? 0}
            </div>
          )}
        </Card>
      </div>

      {/* Last 5 receipts */}
      <Card>
        <h3 className="text-sm font-medium text-slate-700 mb-3">
          Recent Receipts
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
                <tr className="border-b bg-slate-50">
                  <th className="p-2 text-left">Receipt No</th>
                  <th className="p-2 text-left">Invoice ID</th>
                  <th className="p-2 text-right">Amount</th>
                  <th className="p-2 text-left">Created At</th>
                  <th className="p-2 text-left">Actions</th>
                </tr>
              </thead>
              <tbody>
                {lastReceipts.map((r: any) => (
                  <tr key={r.id} className="border-b last:border-b-0">
                    <td className="p-2">{r.receipt_no ?? "-"}</td>
                    <td className="p-2">{r.invoice_id ?? "-"}</td>
                    <td className="p-2 text-right">
                      {formatMoney(Number(r.amount ?? 0) || 0)}
                    </td>
                    <td className="p-2">
                      {r.created_at
                        ? new Date(r.created_at).toLocaleString()
                        : "-"}
                    </td>
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

/* ------------------------------------------------------------------
   STUDENT / PARENT DASHBOARD
------------------------------------------------------------------- */

const StudentParentDashboard: React.FC<{ role: string | undefined }> = ({
  role,
}) => {
  const { user } = useAuth();
  const { data: studentsData } = useStudents();
  const {
    data: myInvoicesData,
    isLoading: myInvoicesLoading,
    isError: myInvoicesError,
  } = useMyInvoices();
  const {
    data: receiptsData,
    isLoading: receiptsLoading,
    isError: receiptsError,
  } = useReceipts();

  const studentId =
    user && typeof (user as any).student_id === "number"
      ? (user as any).student_id
      : undefined;

  const students = Array.isArray(studentsData)
    ? studentsData
    : studentsData ?? [];

  const studentById = useMemo(() => {
    const map = new Map<number, any>();
    students.forEach((s: any) => {
      if (s && typeof s.id === "number") {
        map.set(s.id, s);
      }
    });
    return map;
  }, [students]);

  const displayStudentName =
    typeof studentId === "number"
      ? studentById.get(studentId)?.name ?? `Student #${studentId}`
      : "Student";

  const invoices = Array.isArray(myInvoicesData)
    ? myInvoicesData
    : myInvoicesData?.results ?? myInvoicesData ?? [];

  const receipts = Array.isArray(receiptsData)
    ? receiptsData
    : receiptsData?.results ?? receiptsData ?? [];

  const totalPaid =
    invoices && Array.isArray(invoices)
      ? invoices.reduce((sum: number, inv: any) => {
          const paid = Number(inv.paid_amount ?? 0);
          return sum + (isNaN(paid) ? 0 : paid);
        }, 0)
      : 0;

  const outstandingBalance =
    invoices && Array.isArray(invoices)
      ? invoices.reduce((sum: number, inv: any) => {
          const balance =
            inv.balance != null
              ? Number(inv.balance)
              : Number(inv.total_due ?? inv.amount_due ?? 0) -
                Number(inv.paid_amount ?? 0);
          return sum + (isNaN(balance) ? 0 : balance);
        }, 0)
      : 0;

  const recentReceipts =
    receipts && Array.isArray(receipts)
      ? [...receipts]
          .sort((a: any, b: any) => {
            const da = new Date(a.created_at ?? 0).getTime();
            const db = new Date(b.created_at ?? 0).getTime();
            return db - da;
          })
          .slice(0, 3)
      : [];

  const loading = myInvoicesLoading || receiptsLoading;
  const error = myInvoicesError || receiptsError;

  const base = import.meta.env.VITE_API_BASE || "http://localhost:8000";

  return (
    <div className="space-y-6">
      {/* Header + quick actions */}
      <Card>
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold mb-1">
              Welcome, {displayStudentName}
            </h2>
            <p className="text-sm text-slate-600 dark:text-slate-300">
              This is your SchoolFlow fee account{" "}
              {role ? `(${role} login)` : ""}.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link
              to="/my/invoices"
              className="inline-flex items-center px-3 py-1.5 rounded-md bg-blue-600 text-white text-sm hover:bg-blue-700"
            >
              View My Invoices
            </Link>
            <Link
              to="/my/receipts"
              className="inline-flex items-center px-3 py-1.5 rounded-md border border-slate-300 text-sm text-slate-800 hover:bg-slate-100"
            >
              View My Receipts
            </Link>
          </div>
        </div>
      </Card>

      {/* Metric cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <h3 className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-1">
            Total Paid
          </h3>
          {loading ? (
            <div className="text-slate-400 text-sm">Loading...</div>
          ) : error ? (
            <div className="text-red-600 text-sm">
              Could not load your metrics.
            </div>
          ) : (
            <div className="text-2xl font-semibold">
              {formatMoney(totalPaid)}
            </div>
          )}
        </Card>

        <Card>
          <h3 className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-1">
            Outstanding Balance
          </h3>
          {loading ? (
            <div className="text-slate-400 text-sm">Loading...</div>
          ) : error ? (
            <div className="text-red-600 text-sm">
              Could not load your metrics.
            </div>
          ) : (
            <div className="text-2xl font-semibold">
              {formatMoney(outstandingBalance)}
            </div>
          )}
        </Card>

        <Card>
          <h3 className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-1">
            Receipts Issued
          </h3>
          {receiptsLoading ? (
            <div className="text-slate-400 text-sm">Loading...</div>
          ) : receiptsError ? (
            <div className="text-red-600 text-sm">
              Could not load your receipts.
            </div>
          ) : (
            <div className="text-2xl font-semibold">{receipts.length ?? 0}</div>
          )}
        </Card>
      </div>

      {/* Recent receipts for the student */}
      <Card>
        <h3 className="text-sm font-medium text-slate-700 mb-3">
          Recent Receipts
        </h3>
        {receiptsLoading ? (
          <div className="text-slate-400 text-sm">Loading receipts...</div>
        ) : receiptsError ? (
          <div className="text-red-600 text-sm">
            Could not load your receipts.
          </div>
        ) : recentReceipts.length === 0 ? (
          <div className="text-slate-500 text-sm">
            You do not have any receipts yet.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-slate-50">
                  <th className="p-2 text-left">Receipt No</th>
                  <th className="p-2 text-left">Invoice ID</th>
                  <th className="p-2 text-right">Amount</th>
                  <th className="p-2 text-left">Created At</th>
                  <th className="p-2 text-left">Actions</th>
                </tr>
              </thead>
              <tbody>
                {recentReceipts.map((r: any) => (
                  <tr key={r.id} className="border-b last:border-b-0">
                    <td className="p-2">{r.receipt_no ?? "-"}</td>
                    <td className="p-2">{r.invoice_id ?? "-"}</td>
                    <td className="p-2 text-right">
                      {formatMoney(Number(r.amount ?? 0) || 0)}
                    </td>
                    <td className="p-2">
                      {r.created_at
                        ? new Date(r.created_at).toLocaleString()
                        : "-"}
                    </td>
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

/* ------------------------------------------------------------------
   ROOT DASHBOARD SWITCH
------------------------------------------------------------------- */

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
