// C:\coding_projects\dev\schoolflow\frontend\src\pages\MyInvoices.tsx
import React from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../store/auth";
import { useInvoices } from "../api/queries";
import { formatMoney } from "../lib/utils";

const MyInvoices: React.FC = () => {
  const { user } = useAuth();
  const role = user?.role ?? "user";

  const { data, isLoading, isError } = useInvoices();

  if (isLoading) {
    return <div>Loading my invoices...</div>;
  }

  if (isError) {
    return (
      <div className="text-red-600">
        Failed to load invoices for your account.
      </div>
    );
  }

  const invoices = Array.isArray(data) ? data : (data?.results ?? data ?? []);

  if (!invoices || invoices.length === 0) {
    return (
      <div className="bg-white p-6 rounded shadow space-y-3">
        <h1 className="text-2xl font-bold">My Invoices</h1>
        <p className="text-sm text-slate-600 dark:text-slate-300">
          No invoices found for your account yet.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">My Invoices</h1>
      <p className="text-sm text-slate-600 dark:text-slate-300">
        Showing invoices visible to your {role} account.
      </p>

      <div className="bg-white rounded shadow overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr>
              <th className="p-2 text-left">Invoice No</th>
              <th className="p-2 text-left">Period</th>
              <th className="p-2 text-left">Due Date</th>
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

              return (
                <tr key={inv.id} className="border-t">
                  <td className="p-2">{inv.invoice_no}</td>
                  <td className="p-2">{inv.period}</td>
                  <td className="p-2">
                    {inv.due_date ? String(inv.due_date) : "-"}
                  </td>
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
                      View
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
};

export default MyInvoices;
