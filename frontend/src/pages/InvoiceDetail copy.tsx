/* C:\coding_projects\dev\schoolflow\frontend\src\pages\InvoiceDetail.tsx */
/**
 * Invoice detail page � uses app toast for success/error and shows latest receipt summary.
 */

import React, { useState } from "react";
import { useParams } from "react-router-dom";
import { useQueryClient, useMutation } from "@tanstack/react-query";
import { useInvoice, useStudents } from "../api/queries";
import { formatMoney } from "../lib/utils";
import { createPaymentOrder, CreatePaymentPayload } from "../api/payments";
import PaymentDialog from "../components/PaymentDialog";
import { useToast } from "../components/ui/use-toast";

export default function InvoiceDetail() {
  const { id } = useParams();
  const queryClient = useQueryClient();
  const { data, isLoading, isError } = useInvoice(id);
  const { data: students } = useStudents();
  const { toast } = useToast();

  const [openPayment, setOpenPayment] = useState(false);

  const paymentMutation = useMutation({
    mutationFn: (payload: CreatePaymentPayload) =>
      createPaymentOrder(id as string, payload),
    onSuccess: async () => {
      try {
        await queryClient.refetchQueries({ queryKey: ["invoice", id], exact: true });
        await queryClient.refetchQueries({ queryKey: ["receipts"], exact: false });
        setOpenPayment(false);
        toast({ title: "Payment recorded", description: "Invoice and receipts refreshed." });
      } catch {
        toast({
          title: "Payment recorded (partial)",
          description: "Payment created but failed to refresh data.",
          variant: "destructive",
        });
      }
    },
    onError: () => {
      toast({
        title: "Payment failed",
        description: "Failed to create payment.",
        variant: "destructive",
      });
    },
  });

  if (isLoading) return <div>Loading invoice...</div>;
  if (isError) return <div className="text-red-600">Failed to load invoice.</div>;
  if (!data) return <div>Invoice not found</div>;

  const inv: any = data;

  // Student label
  const studentNameById = new Map<number, string>();
  students?.forEach((s: any) => {
    if (s && typeof s.id === "number") {
      studentNameById.set(s.id, s.name ?? `Student #${s.id}`);
    }
  });
  const studentLabel =
    studentNameById.get(inv.student_id) ?? inv.student?.name ?? `Student #${inv.student_id}`;

  // Line items
  const items =
    inv.items && inv.items.length > 0
      ? inv.items
      : inv.line_items && inv.line_items.length > 0
      ? inv.line_items
      : inv.components && inv.components.length > 0
      ? inv.components
      : inv.fee_components && inv.fee_components.length > 0
      ? inv.fee_components
      : [];

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

  // Latest receipt
  const latestReceipt =
    Array.isArray(inv.receipts) && inv.receipts.length > 0
      ? [...inv.receipts].sort(
          (a: any, b: any) =>
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        )[0]
      : null;

  return (
    <div className="max-w-3xl mx-auto pt-20">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h1 className="text-2xl font-bold">Invoice {inv.invoice_no ?? "-"}</h1>
          <p className="text-sm text-gray-600">Invoice ID: {inv.id} � Period: {inv.period ?? "-"}</p>
          <p className="text-sm text-gray-600">Student: {studentLabel}</p>
          <p className="text-sm text-gray-600">Due: {inv.due_date ?? "-"}</p>
        </div>

        <div className="flex flex-wrap gap-2 relative z-50">
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
                <th className="p-2 text-right">Amount</th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 ? (
                <tr>
                  <td colSpan={2} className="p-2 text-sm text-slate-500">
                    No items
                  </td>
                </tr>
              ) : (
                items.map((it: any, idx: number) => (
                  <tr key={idx} className="border-t">
                    <td className="p-2 align-top">{itemTitle(it)}</td>
                    <td className="p-2 text-right align-top">
                      {formatMoney(it.amount ?? it.price ?? 0)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <div className="mt-4 text-right space-y-1">
          <div>Items total: {formatMoney(inv.items_total ?? 0)}</div>
          <div>Total due: {formatMoney(inv.total_due ?? inv.amount_due ?? 0)}</div>
          <div>
            Paid:{" "}
            {formatMoney(
              inv.paid_amount ??
                inv.paid ??
                (Array.isArray(inv.receipts)
                  ? inv.receipts.reduce((s: any, r: any) => s + (r.amount ?? 0), 0)
                  : 0)
            )}
          </div>
          <div className="font-bold">
            Balance:{" "}
            {formatMoney(
              inv.balance ?? (inv.amount_due ?? 0) - (inv.paid_amount ?? inv.paid ?? 0)
            )}
          </div>
        </div>

        {latestReceipt && (
          <div className="mt-4 p-3 border rounded bg-gray-50">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-600">Latest receipt</div>
                <div className="font-medium">
                  {latestReceipt.receipt_no ?? latestReceipt.id}
                </div>
                <div className="text-sm">{formatMoney(latestReceipt.amount ?? 0)}</div>
              </div>
              <div>
                <a
                  className="px-2 py-1 rounded bg-white border text-sm"
                  href={`${base}/api/v1/receipts/${latestReceipt.id}/download`}
                  target="_blank"
                  rel="noreferrer"
                >
                  Download
                </a>
              </div>
            </div>
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
