// C:\coding_projects\dev\schoolflow\frontend\src\pages\ReceiptsList.tsx
/**
 * Receipts list page (admin / accountant view)
 */

import React, { useMemo } from "react";
import { useReceipts, useInvoices, useStudents } from "../api/queries";
import { formatMoney } from "../lib/utils";

export default function ReceiptsList() {
  const {
    data: receiptsData,
    isLoading: loadingReceipts,
    isError: errorReceipts,
  } = useReceipts();

  const { data: invoicesData } = useInvoices();
  const { data: studentsData } = useStudents();

  if (loadingReceipts) {
    return <div>Loading receipts...</div>;
  }

  if (errorReceipts) {
    return <div className="text-red-600">Failed to load receipts.</div>;
  }

  const receipts = Array.isArray(receiptsData)
    ? receiptsData
    : (receiptsData?.results ?? receiptsData ?? []);

  if (!receipts || receipts.length === 0) {
    return (
      <div className="bg-white p-6 rounded shadow text-center">
        No receipts found.
      </div>
    );
  }

  const invoices = Array.isArray(invoicesData)
    ? invoicesData
    : (invoicesData ?? []);
  const students = Array.isArray(studentsData)
    ? studentsData
    : (studentsData ?? []);

  const invoiceById = useMemo(() => {
    const map = new Map<number, any>();
    invoices.forEach((inv: any) => {
      if (inv && typeof inv.id === "number") {
        map.set(inv.id, inv);
      }
    });
    return map;
  }, [invoices]);

  const studentById = useMemo(() => {
    const map = new Map<number, any>();
    students.forEach((s: any) => {
      if (s && typeof s.id === "number") {
        map.set(s.id, s);
      }
    });
    return map;
  }, [students]);

  const findStudentNameForReceipt = (r: any): string => {
    if (!r || r.invoice_id == null) return "-";
    const inv = invoiceById.get(r.invoice_id);
    if (!inv || inv.student_id == null) return `Invoice #${r.invoice_id}`;
    const student = studentById.get(inv.student_id);
    return student?.name ?? `Student #${inv.student_id}`;
  };

  const formatDateTime = (value?: string | null) => {
    if (!value) return "-";
    try {
      return new Date(value).toLocaleString();
    } catch {
      return String(value);
    }
  };

  const base = import.meta.env.VITE_API_BASE || "http://localhost:8000";

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Receipts</h1>
      <div className="bg-white rounded shadow overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr>
              <th className="p-2 text-left">ID</th>
              <th className="p-2 text-left">Receipt No</th>
              <th className="p-2 text-left">Invoice ID</th>
              <th className="p-2 text-left">Student</th>
              <th className="p-2 text-right">Amount</th>
              <th className="p-2 text-left">Created At</th>
              <th className="p-2 text-left">Actions</th>
            </tr>
          </thead>
          <tbody>
            {receipts.map((r: any) => (
              <tr key={r.id} className="border-t">
                <td className="p-2">{r.id}</td>
                <td className="p-2">{r.receipt_no ?? "-"}</td>
                <td className="p-2">{r.invoice_id ?? "-"}</td>
                <td className="p-2">{findStudentNameForReceipt(r)}</td>
                <td className="p-2 text-right">
                  {formatMoney(
                    Number(r.amount != null ? r.amount : 0) || 0
                  )}
                </td>
                <td className="p-2">{formatDateTime(r.created_at)}</td>
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
}
