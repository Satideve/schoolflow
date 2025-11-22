// C:\coding_projects\dev\schoolflow\frontend\src\pages\MyReceipts.tsx
import React from "react";
import { useAuth } from "../store/auth";

const MyReceipts: React.FC = () => {
  const { user } = useAuth();
  const role = user?.role ?? "user";

  return (
    <div className="space-y-3">
      <h1 className="text-2xl font-bold">My Receipts</h1>
      <p className="text-sm text-slate-600 dark:text-slate-300">
        This is the {role} view for receipts.
      </p>
      <p className="text-sm text-slate-600 dark:text-slate-300">
        In the next steps, we will load only the receipts linked to the
        current student/parent payments and show:
      </p>
      <ul className="list-disc list-inside text-sm text-slate-600 dark:text-slate-300">
        <li>Receipt number and date</li>
        <li>Linked invoice and paid amount</li>
        <li>Downloadable PDF receipt</li>
      </ul>
    </div>
  );
};

export default MyReceipts;
