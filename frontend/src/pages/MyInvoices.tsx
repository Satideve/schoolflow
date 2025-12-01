// C:\coding_projects\dev\schoolflow\frontend\src\pages\MyInvoices.tsx
import React, { useMemo } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../store/auth";
import { useMyInvoices, useStudents } from "../api/queries";
import { formatMoney } from "../lib/utils";

const MyInvoices: React.FC = () => {
  const { user } = useAuth();
  const role = user?.role ?? "user";

  const { data, isLoading, isError } = useMyInvoices();
  const { data: studentsData } = useStudents();

  const invoices = Array.isArray(data) ? data : (data?.results ?? data ?? []);
  const students = Array.isArray(studentsData)
    ? studentsData
    : (studentsData ?? []);

  const studentById = useMemo(() => {
    const map = new Map<number, any>();
    students.forEach((s: any) => {
      if (s && typeof s.id === "number") {
        map.set(s.id, s);
      }
    });
    return map;
  }, [students]);

  const findStudentName = (studentId: number) => {
    const match = studentById.get(studentId);
    return match?.name ?? `Student #${studentId}`;
  };

  const invoicesExist = invoices && invoices.length > 0;

  // For context, prefer the mapping from the logged-in user to a student
  const studentIdFromUser =
    user && typeof (user as any).student_id === "number"
      ? (user as any).student_id
      : undefined;

  const studentIdFromInvoices =
    invoicesExist && typeof invoices[0]?.student_id === "number"
      ? invoices[0].student_id
      : undefined;

  const studentIdForContext = studentIdFromUser ?? studentIdFromInvoices;

  const primaryStudentName =
    typeof studentIdForContext === "number"
      ? findStudentName(studentIdForContext)
      : undefined;

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

  if (!invoicesExist) {
    return (
      <div className="bg-white p-6 rounded shadow space-y-3">
        <h1 className="text-2xl font-bold">
          {primaryStudentName
            ? `${primaryStudentName}'s Invoices`
            : "My Invoices"}
        </h1>
        <p className="text-sm text-slate-600 dark:text-slate-300">
          No invoices found for your account yet.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">
        {primaryStudentName
          ? `${primaryStudentName}'s Invoices`
          : "My Invoices"}
      </h1>
      <p className="text-sm text-slate-600 dark:text-slate-300">
        Showing invoices for{" "}
        <span className="font-semibold">
          {primaryStudentName ??
            (studentIdForContext != null
              ? `Student #${studentIdForContext}`
              : "your account")}
        </span>{" "}
        ({role} account).
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
