// C:\coding_projects\dev\schoolflow\frontend\src\pages\Dashboard.tsx
import React from "react";
import Card from "../components/ui/card";

const Dashboard: React.FC = () => {
  return (
    <div className="grid grid-cols-1 gap-4">
      <Card>
        <h2 className="text-lg font-semibold">Welcome</h2>
        <p className="text-sm text-slate-600 dark:text-slate-300">Quick links: Invoices, Receipts, Create Invoice.</p>
      </Card>
    </div>
  );
};

export default Dashboard;
