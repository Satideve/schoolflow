/* C:\coding_projects\dev\schoolflow\frontend\src\pages\InvoicesList.tsx */
/**
 * Invoices list. Uses the invoices query and displays a simple table.
 */

import React from "react";
import { Link } from "react-router-dom";
import { useInvoices } from "../api/queries";
import { formatMoney } from "../lib/utils";
import type { Invoice } from "../types/api";

export default function InvoicesList() {
  const { data, isLoading, isError } = useInvoices(1);

  if (isLoading) return <div>Loading invoices…</div>;
  if (isError) return <div className="text-red-600">Failed to load invoices.</div>;

  const invoices: Invoice[] = Array.isArray(data) ? data : (data?.results ?? data ?? []);

  if (!invoices || invoices.length === 0) {
    return (
      <div>
        <div className="flex justify-between items-center mb-4">
          <h1 className="text-2xl font-bold">Invoices</h1>
          <Link to="/invoices/create" className="bg-green-600 text-white px-3 py-1 rounded">Create Invoice</Link>
        </div>
        <div className="bg-white shadow rounded p-6 text-center text-slate-600">No invoices found.</div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">Invoices</h1>
        <Link to="/invoices/create" className="bg-green-600 text-white px-3 py-1 rounded">Create Invoice</Link>
      </div>

      <div className="bg-white shadow rounded overflow-x-auto">
        <table className="w-full table-auto">
          <thead>
            <tr className="text-left">
              <th className="p-2">Invoice No</th>
              <th>Student</th>
              <th>Period</th>
              <th className="text-right">Total Due</th>
              <th className="text-right">Paid</th>
              <th className="text-right">Balance</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {invoices.map((inv) => (
              <tr key={inv.id} className="border-t">
                <td className="p-2">{inv.invoice_no}</td>
                <td className="p-2">{(inv as any).student?.name ?? inv.student_id ?? "—"}</td>
                <td className="p-2">{inv.period ?? "—"}</td>
                <td className="p-2 text-right">{formatMoney(inv.total_due ?? 0)}</td>
                <td className="p-2 text-right">{formatMoney(inv.paid_amount ?? 0)}</td>
                <td className="p-2 text-right font-medium">{formatMoney(inv.balance ?? 0)}</td>
                <td className="p-2">
                  <Link to={`/invoices/${inv.id}`} className="text-blue-600">Open</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
