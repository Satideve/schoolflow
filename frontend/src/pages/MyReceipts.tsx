// C:\coding_projects\dev\schoolflow\frontend\src\pages\MyReceipts.tsx
import React from "react";
import { useAuth } from "../store/auth";
import { useReceipts } from "../api/queries";

const MyReceipts: React.FC = () => {
  const { user } = useAuth();
  const role = user?.role ?? "user";

  const { data, isLoading, isError } = useReceipts();

  if (isLoading) {
    return <div>Loading my receipts...</div>;
  }

  if (isError) {
    return (
      <div className="text-red-600">
        Failed to load receipts for your account.
      </div>
    );
  }

  const receipts = Array.isArray(data) ? data : (data?.results ?? data ?? []);

  if (!receipts || receipts.length === 0) {
    return (
      <div className="bg-white p-6 rounded shadow space-y-3">
        <h1 className="text-2xl font-bold">My Receipts</h1>
        <p className="text-sm text-slate-600 dark:text-slate-300">
          No receipts found for your account yet.
        </p>
      </div>
    );
  }

  const base = import.meta.env.VITE_API_BASE || "http://localhost:8000";

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">My Receipts</h1>
      <p className="text-sm text-slate-600 dark:text-slate-300">
        Showing receipts linked to your {role} account.
      </p>

      <div className="bg-white rounded shadow overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr>
              <th className="p-2 text-left">Receipt No</th>
              <th className="p-2 text-left">Invoice ID</th>
              <th className="p-2 text-left">Amount</th>
              <th className="p-2 text-left">Created At</th>
              <th className="p-2 text-left">Actions</th>
            </tr>
          </thead>
          <tbody>
            {receipts.map((r: any) => (
              <tr key={r.id} className="border-t">
                <td className="p-2">{r.receipt_no ?? "-"}</td>
                <td className="p-2">{r.invoice_id ?? "-"}</td>
                <td className="p-2">{r.amount ?? "-"}</td>
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
    </div>
  );
};

export default MyReceipts;
