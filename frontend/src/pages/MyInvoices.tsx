// C:\coding_projects\dev\schoolflow\frontend\src\pages\MyInvoices.tsx
import React from "react";
import { useAuth } from "../store/auth";

const MyInvoices: React.FC = () => {
  const { user } = useAuth();
  const role = user?.role ?? "user";

  return (
    <div className="space-y-3">
      <h1 className="text-2xl font-bold">My Invoices</h1>
      <p className="text-sm text-slate-600 dark:text-slate-300">
        This is the {role} view for invoices.
      </p>
      <p className="text-sm text-slate-600 dark:text-slate-300">
        In the next steps, we will load only the invoices that belong to the
        current student/parent and show:
      </p>
      <ul className="list-disc list-inside text-sm text-slate-600 dark:text-slate-300">
        <li>Invoice number, period, due date</li>
        <li>Amount due, paid amount, outstanding balance</li>
        <li>Links to view details and download PDFs</li>
      </ul>
    </div>
  );
};

export default MyInvoices;
