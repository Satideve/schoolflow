// C:\coding_projects\dev\schoolflow\frontend\src\components\ui\table.tsx
import React from "react";

export const DataTable: React.FC<{ columns?: React.ReactNode; children?: React.ReactNode }> = ({ columns, children }) => {
  return (
    <div className="overflow-x-auto w-full">
      <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-700">
        <thead className="bg-slate-50 dark:bg-gray-800">
          <tr>{columns}</tr>
        </thead>
        <tbody className="bg-white dark:bg-gray-900 divide-y divide-slate-100 dark:divide-slate-800">{children}</tbody>
      </table>
    </div>
  );
};

export default DataTable;
