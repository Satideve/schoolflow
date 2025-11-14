/* C:\coding_projects\dev\schoolflow\frontend\src\pages\InvoiceDetail.tsx */
/**
 * Invoice detail page — displays invoice header, line items, totals,
 * PDF download link, and a placeholder for payments/receipts.
 */

import React from "react";
import { useParams } from "react-router-dom";
import { useInvoice } from "../api/queries";
import { formatMoney } from "../lib/utils";

export default function InvoiceDetail() {
  const { id } = useParams();
  const { data, isLoading, isError } = useInvoice(id);

  if (isLoading) return <div>Loading invoice…</div>;
  if (isError) return <div className="text-red-600">Failed to load invoice.</div>;
  if (!data) return <div>Invoice not found</div>;

  const inv: any = data;
  const items = Array.isArray(inv.items) ? inv.items : [];

  const base = import.meta.env.VITE_API_BASE || "http://localhost:8000";

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h1 className="text-2xl font-bold">Invoice {inv.invoice_no ?? "—"}</h1>
          <p className="text-sm text-gray-600">ID: {inv.id ?? "—"} — Period: {inv.period ?? "—"}</p>
          <p className="text-sm text-gray-600">Due: {inv.due_date ?? "—"}</p>
        </div>

        <div className="space-x-2">
          <a
            href={`${base}/api/v1/invoices/${inv.id}/download`}
            target="_blank"
            rel="noreferrer"
            className="px-3 py-1 rounded bg-gray-800 text-white"
          >
            Download PDF
          </a>
          {/* Collect Payment currently client-side (Razorpay or simulate) */}
          <button className="px-3 py-1 rounded bg-blue-600 text-white">Collect Payment</button>
        </div>
      </div>

      <div className="mt-2 bg-white p-4 rounded shadow">
        <h3 className="font-semibold">Line Items</h3>
        <div className="overflow-x-auto">
          <table className="w-full mt-2">
            <thead>
              <tr className="text-left">
                <th className="p-2">Title</th>
                <th className="p-2">Qty</th>
                <th className="p-2 text-right">Amount</th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 ? (
                <tr>
                  <td colSpan={3} className="p-2 text-sm text-slate-500">No items</td>
                </tr>
              ) : (
                items.map((it: any, idx: number) => (
                  <tr key={idx} className="border-t">
                    <td className="p-2 align-top">{it.title ?? "—"}</td>
                    <td className="p-2 align-top">{it.quantity ?? "-"}</td>
                    <td className="p-2 text-right align-top">{formatMoney(it.amount ?? 0)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <div className="mt-4 text-right space-y-1">
          <div>Items total: {formatMoney(inv.items_total ?? 0)}</div>
          <div>Total due: {formatMoney(inv.total_due ?? 0)}</div>
          <div>Paid: {formatMoney(inv.paid_amount ?? 0)}</div>
          <div className="font-bold">Balance: {formatMoney(inv.balance ?? 0)}</div>
        </div>

        {Array.isArray(inv.receipts) && inv.receipts.length > 0 && (
          <div className="mt-4">
            <h4 className="font-medium">Receipts</h4>
            <ul className="mt-2 space-y-1">
              {inv.receipts.map((r: any) => (
                <li key={r.id} className="text-sm">
                  <a
                    className="text-blue-600"
                    href={`${base}/api/v1/receipts/${r.id}/download`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    {r.receipt_no ?? r.id} — {formatMoney(r.amount ?? 0)}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
