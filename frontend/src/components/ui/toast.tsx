// C:\coding_projects\dev\schoolflow\frontend\src\components\ui\toast.tsx
import React from "react";

export const ToastItem: React.FC<{ message: string; id?: string }> = ({ message }) => {
  return (
    <div className="max-w-sm w-full bg-white dark:bg-gray-800 shadow rounded-md p-3 border border-slate-100 dark:border-slate-700">
      <div className="text-sm text-slate-800 dark:text-slate-100">{message}</div>
    </div>
  );
};

export default ToastItem;
