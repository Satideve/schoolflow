// C:\coding_projects\dev\schoolflow\frontend\src\pages\InvoicesList.tsx
/**
 * Invoices list page
 */

import React, { useState, useMemo } from "react";
import { Link } from "react-router-dom";
import { useInvoices, useStudents } from "../api/queries";
import { formatMoney } from "../lib/utils";

type StatusFilter = "all" | "pending" | "paid";

export default function InvoicesList() {
  const { data, isLoading, isError } = useInvoices();
  const { data: students } = useStudents();
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");

  if (isLoading) {
    return <div>Loading invoices...</div>;
  }

  if (isError) {
    return <div className="text-red-600">Failed to load invoices.</div>;
  }

  const invoicesRaw = Array.isArray(data) ? data : (data?.results ?? data ?? []);

  const studentNameById = new Map<number, string>();
  students?.forEach((s: any) => {
    if (s && typeof s.id === "number") {
      const label = s.name ?? `Student #${s.id}`;
      studentNameById.set(s.id, label);
    }
  });

  const invoices = useMemo(() => {
    if (!invoicesRaw) return [];

    return (invoicesRaw as any[]).filter((inv) => {
      const totalDue =
        inv.total_due != null ? Number(inv.total_due) : Number(inv.amount_due ?? 0);
      const paid = Number(inv.paid_amount ?? 0);
      const balance =
        inv.balance != null && !Number.isNaN(Number(inv.balance))
          ? Number(inv.balance)
          : totalDue - paid;

      if (statusFilter === "all") return true;
      if (statusFilter === "pending") return balance > 0.01;
      if (statusFilter === "paid") return balance <= 0.01;
      return true;
    });
  }, [invoicesRaw, statusFilter]);

  if (!invoices || invoices.length === 0) {
    return (
      <div className="bg-white p-6 rounded shadow text-center">
        No invoices found.
      </div>
    );
  }

  return (
    <div>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mb-4">
        <h1 className="text-2xl font-bold">Invoices</h1>

        <div className="flex flex-wrap gap-2 items-center">
          <select
            className="border rounded px-2 py-1 text-sm"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
          >
            <option value="all">All</option>
            <option value="pending">Pending</option>
            <option value="paid">Paid</option>
          </select>

          <Link
            to="/invoices/create"
            className="inline-flex items-center px-3 py-1 rounded border border-slate-300 text-sm text-slate-800 hover:bg-slate-100"
          >
            Create Invoice
          </Link>
        </div>
      </div>

      <div className="bg-white rounded shadow overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr>
              <th className="p-2 text-left">Invoice No</th>
              <th className="p-2 text-left">Student</th>
              <th className="p-2 text-left">Period</th>
              <th className="p-2 text-right">Total Due</th>
              <th className="p-2 text-right">Paid</th>
              <th className="p-2 text-right">Balance</th>
              <th className="p-2 text-left"></th>
            </tr>
          </thead>
          <tbody>
            {invoices.map((inv: any) => {
              const totalDue =
                inv.total_due != null
                  ? Number(inv.total_due)
                  : Number(inv.amount_due ?? 0);

              const paid = Number(inv.paid_amount ?? 0);

              let balance: number;
              if (inv.balance != null) {
                const raw = Number(inv.balance);
                balance = isNaN(raw) ? totalDue - paid : raw;
              } else {
                balance = totalDue - paid;
              }

              const studentName =
                studentNameById.get(inv.student_id) ??
                `Student #${inv.student_id}`;

              return (
                <tr key={inv.id} className="border-t">
                  <td className="p-2">{inv.invoice_no}</td>
                  <td className="p-2">{studentName}</td>
                  <td className="p-2">{inv.period}</td>
                  <td className="p-2 text-right">
                    {formatMoney(isNaN(totalDue) ? 0 : totalDue)}
                  </td>
                  <td className="p-2 text-right">
                    {formatMoney(isNaN(paid) ? 0 : paid)}
                  </td>
                  <td className="p-2 text-right">
                    {formatMoney(isNaN(balance) ? 0 : balance)}
                  </td>
                  <td className="p-2 text-right">
                    <Link
                      to={`/invoices/${inv.id}`}
                      className="text-blue-600"
                    >
                      Open
                    </Link>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
