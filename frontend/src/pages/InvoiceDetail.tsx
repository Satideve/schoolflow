// C:\coding_projects\dev\schoolflow\frontend\src\pages\InvoiceDetail.tsx
/**
 * Invoice detail page – uses app toast for success/error and shows latest receipt summary.
 */

import React, { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQueryClient, useMutation } from "@tanstack/react-query";
import { formatMoney } from "../lib/utils";
import { createPaymentOrder, CreatePaymentPayload } from "../api/payments";
import PaymentDialog from "../components/PaymentDialog";
import { useToast } from "../components/ui/use-toast";
import { useAuth } from "../store/auth";
import { downloadWithAuth } from "../lib/download";
import {
  useInvoice,
  useStudents,
  useReceipts,
  emailInvoice,
  emailReceipt,
} from "../api/queries";



const isDev =
  import.meta.env.DEV || import.meta.env.VITE_ENV === "development";
const enableEmail =
  String(import.meta.env.VITE_ENABLE_EMAIL) === "true";


export default function InvoiceDetail() {
  const { id } = useParams();
  const queryClient = useQueryClient();
  const { data, isLoading, isError } = useInvoice(id);

  const { data: students } = useStudents();
  const toast = useToast();
  const { user, token, authReady } = useAuth();
  const base =
    import.meta.env.VITE_API_BASE || "http://localhost:8000";


  const role = user?.role;
  const isAdminLike =
    role === "admin" || role === "clerk" || role === "accountant";
  const isStudentLike = role === "student" || role === "parent";

  const [openPayment, setOpenPayment] = useState(false);
  const { data: allReceipts = [] } = useReceipts(authReady && !!user);

  const paymentMutation = useMutation({
    mutationFn: (payload: CreatePaymentPayload) =>
      createPaymentOrder(id as string, payload),
    onSuccess: async () => {
      try {
        await queryClient.refetchQueries({
          queryKey: ["invoice", id],
          exact: true,
        });
        await queryClient.refetchQueries({
          queryKey: ["receipts"],
          exact: false,
        });
        setOpenPayment(false);
        toast.push("Payment recorded: invoice updated.");
      } catch {
        toast.push("Payment recorded, but failed to refresh invoice.");
      }
    },
    onError: () => {
      toast.push("Payment failed.");
    },
  });

  if (isLoading) return <div>Loading invoice...</div>;
  if (isError) return <div className="text-red-600">Failed to load invoice.</div>;
  if (!data) return <div>Invoice not found</div>;

  const inv: any = data;

  // -------------------------------------------------
  // Derived payment state (SINGLE source of truth)
  // -------------------------------------------------

  const totalDue =
    inv.total_due != null
      ? Number(inv.total_due)
      : Number(inv.amount_due ?? 0);

  const paidAmount =
    inv.paid_amount != null
      ? Number(inv.paid_amount)
      : Array.isArray(inv.receipts)
      ? inv.receipts.reduce(
          (sum: number, r: any) => sum + (Number(r.amount ?? 0) || 0),
          0,
        )
      : 0;

  const balance =
    inv.balance != null
      ? Number(inv.balance)
      : Math.max(totalDue - paidAmount, 0);

  function paymentStatus(): "PAID" | "PARTIALLY PAID" | "UNPAID" {
    if (balance <= 0 && totalDue > 0) return "PAID";
    if (paidAmount > 0) return "PARTIALLY PAID";
    return "UNPAID";
  }
     
  function statusClasses() {
    const status = paymentStatus();
    if (status === "PAID") return "bg-green-100 text-green-800";
    if (status === "PARTIALLY PAID") return "bg-yellow-100 text-yellow-800";
    return "bg-red-100 text-red-800";
  }

  // -------------------------------------------------
  // Student label
  // -------------------------------------------------

  const studentNameById = new Map<number, string>();
  students?.forEach((s: any) => {
    if (typeof s.id === "number") {
      studentNameById.set(s.id, s.name ?? `Student #${s.id}`);
    }
  });

  const studentLabel =
    studentNameById.get(inv.student_id) ??
    inv.student?.name ??
    `Student #${inv.student_id}`;

  // -------------------------------------------------
  // Line items
  // -------------------------------------------------

  const items =
    Array.isArray(inv.items) && inv.items.length > 0
      ? inv.items
      : Array.isArray(inv.line_items)
      ? inv.line_items
      : [];

  function itemTitle(it: any) {
    return (
      it.title ??
      it.name ??
      it.description ??
      it.fee_component?.name ??
      it.component?.name ??
      "Item"
    );
  }

  async function handleEmailInvoice() {
    const toEmail = window.prompt("Send invoice to email:");
    if (!toEmail) return;

    try {
      await emailInvoice(inv.id, toEmail);
      toast.push("Invoice emailed successfully");
    } catch (err: any) {
      toast.push(err?.message || "Failed to email invoice");
    }
  }


  function handleSimulatePayment() {
    if (!inv || balance <= 0) return;

    paymentMutation.mutate({
      amount: Number(balance),
      provider: "manual",
      note: "DEV simulated final payment",
    });
  }

  async function handleEmailReceipt(receiptId: number) {
    const toEmail = window.prompt("Send receipt to email:");
    if (!toEmail) return;

    try {
      await emailReceipt(receiptId, toEmail);
      toast.push("Receipt emailed successfully");
    } catch (err: any) {
      toast.push(err?.message || "Failed to email receipt");
    }
  }

  function handlePaymentSubmit(values: {
    amount: number;
    provider: string;
    note?: string;
  }) {
    paymentMutation.mutate({
      amount: Number(values.amount),
      provider: values.provider,
      note: values.note?.trim() || undefined,
    });
  }

  const latestReceipt =
    Array.isArray(inv.receipts) && inv.receipts.length > 0
      ? [...inv.receipts].sort(
          (a: any, b: any) =>
            new Date(b.created_at).getTime() -
            new Date(a.created_at).getTime(),
        )[0]
      : null;

  const receiptHistory = Array.isArray(allReceipts)
    ? allReceipts
        .filter((r: any) => r.invoice_id === inv.id)
        .sort(
          (a: any, b: any) =>
            new Date(b.created_at).getTime() -
            new Date(a.created_at).getTime(),
        )
    : [];

  // TEMP DEBUG — REMOVE AFTER CONFIRMATION
  const __debugEnv = {
    enableEmail,
    role,
    isAdminLike,
    rawEnableEmail: import.meta.env.VITE_ENABLE_EMAIL,
  };    

  // -------------------------------------------------
  // UI
  // -------------------------------------------------

  return (
    <div className="w-full max-w-5xl mx-auto px-4 py-4 sm:px-6 sm:py-6">

      {/* TEMP DEBUG — REMOVE AFTER CONFIRMATION */}
      <div className="mb-2 p-2 text-xs bg-yellow-100 text-yellow-900 rounded">
        <strong>DEBUG:</strong>{" "}
        {JSON.stringify(__debugEnv)}
      </div>

      <div className="max-w-3xl mx-auto pt-6 space-y-4">
        <div className="mb-2">
          <Link
            to={isAdminLike ? "/invoices" : "/my/invoices"}
            className="text-sm text-blue-600"
          >
            ← Back to {isAdminLike ? "Invoices" : "My Invoices"}
          </Link>
        </div>

        <div className="flex flex-col sm:flex-row sm:justify-between gap-3 mb-2">
          <div>
            <div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-2">
              <h1 className="text-2xl font-bold">
                Invoice {inv.invoice_no ?? "-"}
              </h1>

              <span
                className={`px-2 py-0.5 rounded text-xs font-semibold ${statusClasses()}`}
              >
                {paymentStatus()}
              </span>
            </div>

            <p className="text-sm text-gray-600">
              Invoice ID: {inv.id} · Period: {inv.period ?? "-"}
            </p>
            <p className="text-sm text-gray-600">Student: {studentLabel}</p>
            <p className="text-sm text-gray-600">Due: {inv.due_date ?? "-"}</p>
          </div>

          <div className="flex flex-col sm:flex-row gap-2 sm:items-center">

            <button
              type="button"
              className="flex justify-center items-center px-3 py-1.5 rounded bg-gray-800 text-white text-sm hover:bg-gray-900 w-full sm:w-auto"
              onClick={async () => {
                

                if (!token) {
                  toast.push("Not authenticated");
                  return;
                }

                try {
                  await downloadWithAuth(
                    `${base}/api/v1/invoices/${inv.id}/download`,
                    `invoice-${inv.invoice_no ?? inv.id}.pdf`,
                    token,
                  );
                  toast.push("Invoice PDF downloaded");
                } catch {
                  toast.push("Failed to download invoice PDF");
                }
              }}
            >
              {isStudentLike ? "View PDF" : "Download PDF"}
            </button>

            {isAdminLike && enableEmail && (
              <button
                type="button"
                className="flex justify-center items-center px-3 py-1.5 rounded bg-indigo-600 text-white text-sm hover:bg-indigo-700 w-full sm:w-auto"
                onClick={handleEmailInvoice}
              >
                Email Invoice
              </button>
            )}


            {balance > 0 && (
              <button
                className="flex justify-center items-center px-3 py-1.5 rounded bg-blue-600 text-white text-sm w-full sm:w-auto"
                onClick={() => setOpenPayment(true)}
              >
                {isStudentLike ? "Pay Now" : "Collect Payment"}
              </button>
            )}
            {isDev && balance > 0 && (
              <button
                className="flex justify-center items-center px-3 py-1.5 rounded bg-red-600 text-white text-sm hover:bg-red-700 w-full sm:w-auto"
                onClick={handleSimulatePayment}
              >
                Simulate Final Payment (DEV)
              </button>
            )}
          </div>
        </div>

        <div className="bg-white p-4 rounded shadow space-y-4">
          <div>
            <h3 className="font-semibold">Line Items</h3>
            <div className="overflow-x-auto">
              <table className="w-full mt-2 min-w-[420px]">
                <tbody>
                  {items.map((it: any, idx: number) => (
                    <tr key={idx} className="border-t">
                      <td className="p-2">{itemTitle(it)}</td>
                      <td className="p-2 text-right">
                        {formatMoney(it.amount ?? 0)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="text-left sm:text-right space-y-1">
            <div>Total due: {formatMoney(totalDue)}</div>
            <div>Paid: {formatMoney(paidAmount)}</div>
            <div className="font-bold">
              Balance: {formatMoney(balance)}
            </div>
          </div>

          {/* -------------------------------------------------
              Receipt History (metadata only)
          ------------------------------------------------- */}

          <div className="border-t pt-3">
            <h3 className="font-semibold mb-2">Receipt History</h3>

            {receiptHistory.length === 0 ? (
              <p className="text-sm text-gray-500">
                No receipts issued for this invoice yet.
              </p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-left">
                      <th className="p-2">Receipt No</th>
                      <th className="p-2">Created At</th>
                      <th className="p-2 text-right">Amount</th>
                      <th className="p-2 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {receiptHistory.map((r: any) => (
                      <tr key={r.id} className="border-b last:border-b-0">
                        <td className="p-2">{r.receipt_no ?? "-"}</td>
                        <td className="p-2">
                          {r.created_at
                            ? new Date(r.created_at).toLocaleString()
                            : "-"}
                        </td>
                        <td className="p-2 text-right">
                          {formatMoney(Number(r.amount ?? 0) || 0)}
                        </td>
                        
                        <td className="p-2 text-right space-x-3">
                          <button
                            type="button"
                            className="text-blue-600 text-sm hover:underline"
                            onClick={async () => {
                              if (!token) {
                                toast.push("Not authenticated");
                                return;
                              }

                              try {
                                await downloadWithAuth(
                                  `${base}/api/v1/receipts/${r.id}/download`,
                                  `receipt-${r.receipt_no ?? r.id}.pdf`,
                                  token,
                                );
                                toast.push("Receipt PDF downloaded");
                              } catch {
                                toast.push("Failed to download receipt PDF");
                              }
                            }}
                          >
                            {isStudentLike ? "View" : "Download"}
                          </button>

                          {isAdminLike && enableEmail && (
                            <button
                              type="button"
                              className="text-indigo-600 text-sm hover:underline"
                              onClick={() => handleEmailReceipt(r.id)}
                            >
                              Email
                            </button>
                          )}
                        </td>

                      </tr>

                    ))}
                  </tbody>
                </table>
              </div>  
            )}
          </div>

        </div>

        <PaymentDialog
          open={openPayment}
          onOpenChange={setOpenPayment}
          onSubmit={handlePaymentSubmit}
          loading={paymentMutation.isPending}
        />
      </div>
    </div>
  );
}
