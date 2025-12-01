// C:\coding_projects\dev\schoolflow\frontend\src\pages\MyReceipts.tsx
import React, { useMemo } from "react";
import { useAuth } from "../store/auth";
import { useReceipts, useStudents } from "../api/queries";
import { formatMoney } from "../lib/utils";

const MyReceipts: React.FC = () => {
  const { user } = useAuth();
  const role = user?.role ?? "user";

  const { data, isLoading, isError } = useReceipts();
  const { data: studentsData } = useStudents();

  const receipts = Array.isArray(data) ? data : (data?.results ?? data ?? []);

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

  const studentIdFromUser =
    user && typeof (user as any).student_id === "number"
      ? (user as any).student_id
      : undefined;

  const findStudentName = (studentId: number) => {
    const match = studentById.get(studentId);
    return match?.name ?? `Student #${studentId}`;
  };

  const primaryStudentName =
    typeof studentIdFromUser === "number"
      ? findStudentName(studentIdFromUser)
      : undefined;

  if (isLoading) {
    return <div>Loading my receipts...</div>;
  }

  if (isError) {
    return (
      <div className="text-red-600">
        Failed to load receipts for your account.
      </div>
    );
  }

  if (!receipts || receipts.length === 0) {
    return (
      <div className="bg-white p-6 rounded shadow space-y-3">
        <h1 className="text-2xl font-bold">
          {primaryStudentName
            ? `${primaryStudentName}'s Receipts`
            : "My Receipts"}
        </h1>
        <p className="text-sm text-slate-600 dark:text-slate-300">
          No receipts found for your account yet.
        </p>
      </div>
    );
  }

  const base = import.meta.env.VITE_API_BASE || "http://localhost:8000";

  const formatDateTime = (value?: string | null) => {
    if (!value) return "-";
    try {
      return new Date(value).toLocaleString();
    } catch {
      return String(value);
    }
  };

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">
        {primaryStudentName
          ? `${primaryStudentName}'s Receipts`
          : "My Receipts"}
      </h1>
      <p className="text-sm text-slate-600 dark:text-slate-300">
        Showing receipts for{" "}
        <span className="font-semibold">
          {primaryStudentName ??
            (studentIdFromUser != null
              ? `Student #${studentIdFromUser}`
              : "your account")}
        </span>{" "}
        ({role} account).
      </p>

      <div className="bg-white rounded shadow overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr>
              <th className="p-2 text-left">Receipt No</th>
              <th className="p-2 text-left">Invoice ID</th>
              <th className="p-2 text-right">Amount</th>
              <th className="p-2 text-left">Created At</th>
              <th className="p-2 text-left">Actions</th>
            </tr>
          </thead>
          <tbody>
            {receipts.map((r: any) => (
              <tr key={r.id} className="border-t">
                <td className="p-2">{r.receipt_no ?? "-"}</td>
                <td className="p-2">{r.invoice_id ?? "-"}</td>
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
};

export default MyReceipts;
