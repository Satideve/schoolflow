/* C:\coding_projects\dev\schoolflow\frontend\src\pages\ReceiptsList.tsx */
/**
 * Receipts list page
 */

import React from "react";
import { useReceipts } from "../api/queries";
import { formatMoney } from "../lib/utils";

export default function ReceiptsList() {
  const { data, isLoading, isError } = useReceipts();

  if (isLoading) return <div>Loading receipts…</div>;
  if (isError) return <div className="text-red-600">Failed to load receipts.</div>;

  const receipts = Array.isArray(data) ? data : (data?.results ?? data ?? []);

  if (!receipts || receipts.length === 0) {
    return <div className="bg-white p-6 rounded shadow text-center">No receipts found.</div>;
  }

  const base = import.meta.env.VITE_API_BASE || "http://localhost:8000";

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Receipts</h1>
      <div className="bg-white rounded shadow overflow-x-auto">
        <table className="w-full">
          <thead><tr><th className="p-2 text-left">ID</th><th className="p-2 text-left">Receipt No</th><th className="p-2 text-left">Invoice</th><th className="p-2 text-right">Amount</th><th></th></tr></thead>
          <tbody>
            {receipts.map((r: any) => (
              <tr key={r.id} className="border-t">
                <td className="p-2">{r.id}</td>
                <td className="p-2">{r.receipt_no ?? "—"}</td>
                <td className="p-2">{r.invoice_id ?? "—"}</td>
                <td className="p-2 text-right">{formatMoney(r.amount ?? 0)}</td>
                <td className="p-2"><a href={`${base}/api/v1/receipts/${r.id}/download`} target="_blank" rel="noreferrer" className="text-blue-600">Download</a></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
