/* C:\coding_projects\dev\schoolflow\frontend\src\pages\InvoiceDetail.tsx */
/**
 * Invoice detail page � defensive rendering of line items (handles multiple possible keys)
 * and PaymentDialog integration.
 *
 * Fixes applied:
 * - use simple punctuation (middle dot) between ID and Period to avoid replacement glyphs
 * - add top padding to avoid overlap with fixed header
 * - ensure action buttons container has a higher z-index so buttons remain clickable
 */

import React, { useState } from "react";
import { useParams } from "react-router-dom";
import { useQueryClient, useMutation } from "@tanstack/react-query";
import { useInvoice } from "../api/queries";
import { formatMoney } from "../lib/utils";
import { createPaymentOrder, CreatePaymentPayload } from "../api/payments";
import PaymentDialog from "../components/PaymentDialog";

export default function InvoiceDetail() {
  const { id } = useParams();
  const queryClient = useQueryClient();
  const { data, isLoading, isError } = useInvoice(id);

  const [openPayment, setOpenPayment] = useState(false);

  const paymentMutation = useMutation({
    mutationFn: (payload: CreatePaymentPayload) =>
      createPaymentOrder(id as string, payload),
    onSuccess: () => {
      queryClient.invalidateQueries(["invoice", id]);
      queryClient.invalidateQueries(["receipts"]);
      setOpenPayment(false);
    },
    onError: (err: any) => {
      console.error("Payment creation failed", err);
    },
  });

  if (isLoading) return <div>Loading invoice�</div>;
  if (isError) return <div className="text-red-600">Failed to load invoice.</div>;
  if (!data) return <div>Invoice not found</div>;

  const inv: any = data;

  // Defensive: support multiple possible fields where the backend may return items
  const items =
    Array.isArray(inv.items) && inv.items.length > 0
      ? inv.items
      : Array.isArray(inv.line_items) && inv.line_items.length > 0
      ? inv.line_items
      : Array.isArray(inv.components) && inv.components.length > 0
      ? inv.components
      : Array.isArray(inv.fee_components) && inv.fee_components.length > 0
      ? inv.fee_components
      : [];

  // Helper to pick a human-friendly title from item object
  function itemTitle(it: any) {
    return (
      it.title ??
      it.name ??
      it.description ??
      (it.fee_component && it.fee_component.name) ??
      (it.component && it.component.name) ??
      "Item"
    );
  }

  const base = import.meta.env.VITE_API_BASE || "http://localhost:8000";

  function handlePaymentSubmit(values: { amount: number; provider: string; note?: string }) {
    paymentMutation.mutate({
      amount: Number(values.amount),
      provider: values.provider,
      note: values.note?.trim() || undefined,
    });
  }

  return (
    // add padding-top to avoid fixed header overlap (adjust if your navbar is taller)
    <div className="max-w-3xl mx-auto pt-16">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h1 className="text-2xl font-bold">Invoice {inv.invoice_no ?? "�"}</h1>
          {/* use a simple middle dot to separate fields (no weird glyphs) */}
          <p className="text-sm text-gray-600">Invoice ID: {inv.id} : Period: {inv.period ?? "�"}</p>
          <p className="text-sm text-gray-600">Due: {inv.due_date ?? "�"}</p>
        </div>

        {/* ensure action buttons sit above header if z-index overlapping occurs */}
        <div className="space-x-2 relative z-20">
          <a
            href={`${base}/api/v1/invoices/${inv.id}/download`}
            target="_blank"
            rel="noreferrer"
            className="px-3 py-1 rounded bg-gray-800 text-white"
          >
            Download PDF
          </a>
          <button
            className="px-3 py-1 rounded bg-blue-600 text-white"
            onClick={() => setOpenPayment(true)}
          >
            Collect Payment
          </button>
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
                  <td colSpan={3} className="p-2 text-sm text-slate-500">
                    No items
                  </td>
                </tr>
              ) : (
                items.map((it: any, idx: number) => (
                  <tr key={idx} className="border-t">
                    <td className="p-2 align-top">{itemTitle(it)}</td>
                    <td className="p-2 align-top">{it.quantity ?? "-"}</td>
                    <td className="p-2 text-right align-top">{formatMoney(it.amount ?? it.price ?? 0)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <div className="mt-4 text-right space-y-1">
          <div>Items total: {formatMoney(inv.items_total ?? inv.items_total_amount ?? 0)}</div>
          <div>Total due: {formatMoney(inv.total_due ?? inv.amount_due ?? 0)}</div>
          <div>Paid: {formatMoney(inv.paid_amount ?? inv.paid ?? 0)}</div>
          <div className="font-bold">Balance: {formatMoney(inv.balance ?? inv.amount_due ?? 0 - (inv.paid_amount ?? inv.paid ?? 0))}</div>
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
                    {r.receipt_no ?? r.id} : {formatMoney(r.amount ?? 0)}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <PaymentDialog
        open={openPayment}
        onOpenChange={setOpenPayment}
        onSubmit={handlePaymentSubmit}
        loading={paymentMutation.isLoading}
      />
    </div>
  );
}
